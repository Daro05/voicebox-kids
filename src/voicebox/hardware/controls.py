"""Control boundary for keyboard and future GPIO input/output."""

from __future__ import annotations

import asyncio
import logging
import sys
from enum import StrEnum
from typing import Protocol

from voicebox.audio.cues import SilentStatusCues, StatusCues

logger = logging.getLogger(__name__)


class ControlEvent(StrEnum):
    PRESS = "press"
    RELEASE = "release"
    CANCEL = "cancel"


class Controls(Protocol):
    async def next_event(self) -> ControlEvent:
        """Wait for the next input event from a keyboard or physical button."""
        ...

    async def set_status(self, status: str) -> None:
        """Expose status through console output or LEDs."""
        ...


class ConsoleControls:
    """Translate alternating Enter presses into button press/release events."""

    def __init__(self, cues: StatusCues | None = None) -> None:
        self._next_event = ControlEvent.PRESS
        self._cues = cues or SilentStatusCues()

    async def next_event(self) -> ControlEvent:
        if self._next_event is ControlEvent.PRESS:
            prompt = "Press Enter to start recording… "
            following = ControlEvent.RELEASE
        else:
            prompt = "Press Enter to stop and send, or type c to cancel… "
            following = ControlEvent.PRESS
        print(prompt, end="", flush=True)
        loop = asyncio.get_running_loop()
        line_ready: asyncio.Future[str] = loop.create_future()

        def read_line() -> None:
            line = sys.stdin.readline()
            if not line_ready.done():
                line_ready.set_result(line)

        loop.add_reader(sys.stdin.fileno(), read_line)
        try:
            line = await line_ready
        finally:
            loop.remove_reader(sys.stdin.fileno())
        if line == "":
            raise EOFError("Console input closed.")
        if line.strip().lower() in {"c", "cancel"}:
            event = ControlEvent.CANCEL
            following = ControlEvent.PRESS
        else:
            event = self._next_event
        self._next_event = following
        return event

    async def set_status(self, status: str) -> None:
        if status == "recording":
            self._next_event = ControlEvent.RELEASE
        elif status in {"idle", "sent", "cancelled", "busy", "offline", "error"}:
            self._next_event = ControlEvent.PRESS
        labels = {
            "idle": "Ready for the next voice note.",
            "recording": "🔴 Recording…",
            "sending": "📤 Sending to Telegram…",
            "sent": "✅ Voice note sent.",
            "cancelled": "Recording cancelled.",
            "limit": "Maximum recording time reached.",
            "busy": "VoiceBox is busy; try again in a moment.",
            "offline": "⚠️ No connection. Recording kept locally for recovery.",
            "error": "⚠️ Recording or sending failed. Try again.",
        }
        print(labels.get(status, status), flush=True)
        try:
            await self._cues.play(status)
        except Exception:
            logger.exception("Could not play the %s status cue", status)
