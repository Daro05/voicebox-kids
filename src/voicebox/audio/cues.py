"""Short, replaceable audio cues for screen-free device states."""

from __future__ import annotations

import asyncio
import logging
from typing import Protocol

logger = logging.getLogger(__name__)


class StatusCues(Protocol):
    async def play(self, status: str) -> None:
        """Play the cue associated with a device status."""
        ...


class SilentStatusCues:
    async def play(self, status: str) -> None:
        """Keep status handling functional when generated tones are unavailable."""


class FfplayStatusCues:
    """Generate brief tones with ffplay without storing additional media files."""

    _PATTERNS: dict[str, tuple[tuple[int, float], ...]] = {
        "idle": ((660, 0.07),),
        "recording": ((880, 0.10),),
        "sending": ((520, 0.08),),
        "sent": ((880, 0.08), (1174, 0.12)),
        "cancelled": ((330, 0.08), (220, 0.12)),
        "limit": ((740, 0.08), (520, 0.12)),
        "offline": ((260, 0.12), (260, 0.12)),
        "error": ((220, 0.25),),
    }

    def __init__(self, command: str) -> None:
        self.command = command

    def build_command(self, frequency: int, duration: float) -> tuple[str, ...]:
        return (
            self.command,
            "-nodisp",
            "-autoexit",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency={frequency}:duration={duration}",
        )

    async def play(self, status: str) -> None:
        for frequency, duration in self._PATTERNS.get(status, ()):
            process = await asyncio.create_subprocess_exec(
                *self.build_command(frequency, duration),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            try:
                await asyncio.wait_for(process.wait(), timeout=2)
            except TimeoutError:
                process.kill()
                await process.wait()
                logger.warning("Timed out while playing the %s status cue", status)
