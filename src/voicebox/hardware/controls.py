"""Control boundary for keyboard and future GPIO input/output."""

from __future__ import annotations

import asyncio
import sys
from enum import StrEnum
from typing import Protocol


class ControlEvent(StrEnum):
    PRESS = "press"
    RELEASE = "release"


class Controls(Protocol):
    async def next_event(self) -> ControlEvent:
        """Wait for the next input event from a keyboard or physical button."""
        ...

    async def set_status(self, status: str) -> None:
        """Expose status through console output or LEDs."""
        ...


class ConsoleControls:
    """Translate alternating Enter presses into button press/release events."""

    def __init__(self) -> None:
        self._next_event = ControlEvent.PRESS

    async def next_event(self) -> ControlEvent:
        if self._next_event is ControlEvent.PRESS:
            prompt = "Press Enter to start recording… "
            following = ControlEvent.RELEASE
        else:
            prompt = "Press Enter to stop and send… "
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
        event = self._next_event
        self._next_event = following
        return event

    async def set_status(self, status: str) -> None:
        if status == "recording":
            self._next_event = ControlEvent.RELEASE
        elif status in {"idle", "sent", "busy", "error"}:
            self._next_event = ControlEvent.PRESS
        labels = {
            "idle": "Ready for the next voice note.",
            "recording": "🔴 Recording…",
            "sending": "📤 Sending to Telegram…",
            "sent": "✅ Voice note sent.",
            "busy": "VoiceBox is busy; try again in a moment.",
            "error": "⚠️ Recording or sending failed. Try again.",
        }
        print(labels.get(status, status), flush=True)
