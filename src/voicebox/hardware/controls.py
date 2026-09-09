"""Control boundary for keyboard and future GPIO input/output."""

from __future__ import annotations

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
