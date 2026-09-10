"""Provider-neutral record-and-send interaction workflow."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Protocol

from voicebox.audio.recorder import AudioRecorder
from voicebox.core.state_machine import DeviceState, StateMachine
from voicebox.hardware.controls import ControlEvent, Controls

logger = logging.getLogger(__name__)


class VoiceSender(Protocol):
    async def send_voice_note(self, chat_id: str, path: Path) -> None:
        """Send a local voice note to a trusted chat."""
        ...


class OutboundVoiceController:
    """Coordinate recording, retry delivery, and return safely to idle."""

    def __init__(
        self,
        recorder: AudioRecorder,
        messenger: VoiceSender,
        controls: Controls,
        *,
        target_chat_id: str,
        state: StateMachine | None = None,
        interaction_lock: asyncio.Lock | None = None,
        send_attempts: int = 2,
        retry_delay_seconds: float = 0.25,
    ) -> None:
        if send_attempts < 1:
            raise ValueError("send_attempts must be at least 1.")
        self._recorder = recorder
        self._messenger = messenger
        self._controls = controls
        self._target_chat_id = target_chat_id
        self.state = state or StateMachine()
        self._interaction_lock = interaction_lock or asyncio.Lock()
        self._send_attempts = send_attempts
        self._retry_delay_seconds = retry_delay_seconds
        self._recording = False
        self._owns_interaction = False

    async def run(self) -> None:
        await self._controls.set_status("idle")
        try:
            while True:
                await self.handle_event(await self._controls.next_event())
        finally:
            if self._recording:
                await self._recorder.cancel()
                self._recording = False
            if self._owns_interaction:
                self._recover_to_idle()
                self._release_interaction()

    async def handle_event(self, event: ControlEvent) -> None:
        if event is ControlEvent.PRESS:
            await self._start_recording()
        elif event is ControlEvent.RELEASE:
            await self._stop_and_send()

    async def _start_recording(self) -> None:
        if self._recording:
            return
        await self._interaction_lock.acquire()
        self._owns_interaction = True
        if self.state.state is not DeviceState.IDLE:
            self._release_interaction()
            await self._controls.set_status("busy")
            return
        try:
            self.state.transition_to(DeviceState.RECORDING)
            await self._recorder.start()
            self._recording = True
            await self._controls.set_status("recording")
        except Exception:
            logger.exception("Could not start microphone recording")
            await self._recorder.cancel()
            self._recover_to_idle()
            self._release_interaction()
            await self._controls.set_status("error")

    async def _stop_and_send(self) -> None:
        if not self._recording:
            return

        try:
            recording = await self._recorder.stop()
            self._recording = False
            self.state.transition_to(DeviceState.SENDING)
            await self._controls.set_status("sending")

            for attempt in range(1, self._send_attempts + 1):
                try:
                    await self._messenger.send_voice_note(self._target_chat_id, recording)
                    recording.unlink(missing_ok=True)
                    self.state.transition_to(DeviceState.IDLE)
                    await self._controls.set_status("sent")
                    return
                except Exception:
                    logger.exception(
                        "Voice-note send attempt %s/%s failed",
                        attempt,
                        self._send_attempts,
                    )
                    if attempt < self._send_attempts:
                        await asyncio.sleep(self._retry_delay_seconds)

            self.state.transition_to(DeviceState.ERROR)
            self.state.transition_to(DeviceState.IDLE)
            await self._controls.set_status("error")
        except Exception:
            logger.exception("Could not finish microphone recording")
            self._recording = False
            self._recover_to_idle()
            await self._controls.set_status("error")
        finally:
            self._release_interaction()

    def _recover_to_idle(self) -> None:
        if self.state.state is DeviceState.IDLE:
            return
        if self.state.state is not DeviceState.ERROR:
            try:
                self.state.transition_to(DeviceState.ERROR)
            except Exception:
                self.state.state = DeviceState.ERROR
        self.state.transition_to(DeviceState.IDLE)

    def _release_interaction(self) -> None:
        if self._owns_interaction:
            self._interaction_lock.release()
            self._owns_interaction = False
