"""Queued voice-note processing independent from messaging and hardware providers."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Protocol

from voicebox.core.state_machine import DeviceState, StateMachine
from voicebox.messaging.base import VoiceNote

logger = logging.getLogger(__name__)


class AudioPlayer(Protocol):
    async def play(self, path: Path) -> None:
        """Play one local audio file and return when playback finishes."""
        ...


class StatusMessenger(Protocol):
    async def send_text(self, chat_id: str, text: str) -> None:
        """Send a short status message to the originating chat."""
        ...


class VoiceBoxController:
    """Serialize playback, retry transient failures, and acknowledge outcomes."""

    def __init__(
        self,
        player: AudioPlayer,
        messenger: StatusMessenger,
        *,
        state: StateMachine | None = None,
        interaction_lock: asyncio.Lock | None = None,
        playback_attempts: int = 2,
        retry_delay_seconds: float = 0.25,
    ) -> None:
        if playback_attempts < 1:
            raise ValueError("playback_attempts must be at least 1.")
        self.state = state or StateMachine()
        self._interaction_lock = interaction_lock or asyncio.Lock()
        self._player = player
        self._messenger = messenger
        self._playback_attempts = playback_attempts
        self._retry_delay_seconds = retry_delay_seconds
        self._queue: asyncio.Queue[VoiceNote | None] = asyncio.Queue()
        self._worker: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self._worker is None:
            self._worker = asyncio.create_task(self._work(), name="voicebox-playback")

    async def submit(self, note: VoiceNote) -> None:
        if self._worker is None:
            raise RuntimeError("Start the controller before submitting voice notes.")
        await self._queue.put(note)
        logger.info("Queued voice note from approved chat %s", note.chat_id)

    async def stop(self) -> None:
        if self._worker is None:
            return
        await self._queue.join()
        await self._queue.put(None)
        await self._worker
        self._worker = None

    async def _work(self) -> None:
        while True:
            note = await self._queue.get()
            try:
                if note is None:
                    return
                await self._process(note)
            except Exception:
                logger.exception("Unexpected error while processing a voice note")
                self._recover_to_idle()
            finally:
                self._queue.task_done()

    async def _process(self, note: VoiceNote) -> None:
        async with self._interaction_lock:
            self.state.transition_to(DeviceState.RECEIVING)
            self.state.transition_to(DeviceState.PLAYING)

            for attempt in range(1, self._playback_attempts + 1):
                try:
                    await self._player.play(note.local_path)
                    self.state.transition_to(DeviceState.IDLE)
                    await self._safe_send_status(
                        note.chat_id,
                        "✅ VoiceBox played your voice note.",
                    )
                    return
                except Exception:
                    logger.exception(
                        "Playback attempt %s/%s failed for %s",
                        attempt,
                        self._playback_attempts,
                        note.local_path.name,
                    )
                    if attempt < self._playback_attempts:
                        await asyncio.sleep(self._retry_delay_seconds)

            self.state.transition_to(DeviceState.ERROR)
            await self._safe_send_status(
                note.chat_id,
                "⚠️ VoiceBox could not play your voice note. Please try again.",
            )
            self.state.transition_to(DeviceState.IDLE)

    async def _safe_send_status(self, chat_id: str, text: str) -> None:
        try:
            await self._messenger.send_text(chat_id, text)
        except Exception:
            logger.exception("Could not send playback status to chat %s", chat_id)

    def _recover_to_idle(self) -> None:
        if self.state.state is not DeviceState.ERROR:
            try:
                self.state.transition_to(DeviceState.ERROR)
            except Exception:
                self.state.state = DeviceState.ERROR
        self.state.transition_to(DeviceState.IDLE)
