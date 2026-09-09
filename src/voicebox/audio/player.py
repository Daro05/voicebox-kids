"""Local audio playback adapters."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path


class AudioPlayerUnavailableError(RuntimeError):
    """Raised when no supported local player command is installed."""


class LocalAudioPlayer:
    """Play audio files through a small, replaceable operating-system adapter."""

    # ffplay is preferred because Telegram voice notes use Ogg/Opus, which is not
    # supported consistently by native players on every operating system.
    _CANDIDATES = ("ffplay", "paplay", "mpg123", "afplay")

    def __init__(self, command: str | None = None) -> None:
        self.command = command or self._detect_command()

    @classmethod
    def detect_command(cls) -> str | None:
        for command in cls._CANDIDATES:
            if shutil.which(command):
                return command
        return None

    @classmethod
    def _detect_command(cls) -> str:
        command = cls.detect_command()
        if command:
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
