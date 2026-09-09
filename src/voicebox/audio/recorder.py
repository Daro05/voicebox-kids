"""Audio recording boundary for the next MVP slice."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class AudioRecorder(Protocol):
    """A microphone adapter implemented by laptop and Raspberry Pi recorders."""

    async def record(self) -> Path:
        """Record one voice note and return its local file path."""
        ...
