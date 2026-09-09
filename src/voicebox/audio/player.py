"""Local audio playback adapters."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path


class AudioPlayerUnavailableError(RuntimeError):
    """Raised when no supported local player command is installed."""


class LocalAudioPlayer:
    """Play audio files through a small, replaceable operating-system adapter."""

    _CANDIDATES = ("afplay", "ffplay", "paplay", "mpg123")

    def __init__(self, command: str | None = None) -> None:
        self.command = command or self._detect_command()

    @classmethod
    def _detect_command(cls) -> str:
        for command in cls._CANDIDATES:
            if shutil.which(command):
                return command
        raise AudioPlayerUnavailableError(
            "No supported audio player found. Install ffplay or set VOICEBOX_AUDIO_PLAYER."
        )

    def build_command(self, path: Path) -> tuple[str, ...]:
        if self.command == "ffplay":
            return (self.command, "-nodisp", "-autoexit", "-loglevel", "error", str(path))
        return (self.command, str(path))

    async def play(self, path: Path) -> None:
        if not path.is_file():
            raise FileNotFoundError(path)

        process = await asyncio.create_subprocess_exec(
            *self.build_command(path),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()
        if process.returncode:
            detail = stderr.decode(errors="replace").strip()
            raise RuntimeError(f"Audio playback failed ({process.returncode}): {detail}")
