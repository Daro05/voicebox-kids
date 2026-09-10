"""Laptop audio recording adapter backed by FFmpeg."""

from __future__ import annotations

import asyncio
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol
from uuid import uuid4


class AudioRecorderUnavailableError(RuntimeError):
    """Raised when FFmpeg is not available for microphone capture."""


class AudioRecorder(Protocol):
    async def start(self) -> None:
        """Start capturing one voice note."""
        ...

    async def stop(self) -> Path:
        """Stop capture and return the encoded local recording."""
        ...

    async def cancel(self) -> None:
        """Stop capture without returning a recording."""
        ...


def resolve_ffmpeg_command(audio_player: str | None = None) -> str | None:
    """Find FFmpeg next to an explicit ffplay binary or on PATH."""
    if audio_player and Path(audio_player).name == "ffplay":
        sibling = Path(audio_player).with_name("ffmpeg")
        if sibling.is_file():
            return str(sibling)
    return shutil.which("ffmpeg")


class FfmpegAudioRecorder:
    """Record mono Ogg/Opus notes through a replaceable FFmpeg command."""

    def __init__(
        self,
        command: str,
        output_dir: Path,
        *,
        input_device: str = ":0",
    ) -> None:
        if not shutil.which(command):
            raise AudioRecorderUnavailableError(
                "FFmpeg is unavailable. Install it or configure VOICEBOX_AUDIO_PLAYER."
            )
        self.command = command
        self.output_dir = output_dir
        self.input_device = input_device
        self._process: asyncio.subprocess.Process | None = None
        self._destination: Path | None = None

    def build_command(self, destination: Path) -> tuple[str, ...]:
        return (
            self.command,
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "avfoundation",
            "-i",
            self.input_device,
            "-vn",
            "-ac",
            "1",
            "-ar",
            "48000",
            "-c:a",
            "libopus",
            "-b:a",
            "32k",
            "-y",
            str(destination),
        )

    async def start(self) -> None:
        if self._process is not None:
            raise RuntimeError("A recording is already in progress.")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        self._destination = self.output_dir / f"voicebox-{timestamp}-{uuid4().hex[:8]}.ogg"
        self._process = await asyncio.create_subprocess_exec(
            *self.build_command(self._destination),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.sleep(0.1)
        if self._process.returncode is not None:
            await self._raise_process_error("Microphone recording could not start")

    async def stop(self) -> Path:
        process = self._require_process()
        destination = self._require_destination()
        if process.stdin is not None:
            process.stdin.write(b"q\n")
            await process.stdin.drain()
        try:
            _, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
        except TimeoutError:
            process.kill()
            await process.communicate()
            self._reset()
            destination.unlink(missing_ok=True)
            raise RuntimeError("Microphone recording did not stop in time.") from None

        returncode = process.returncode
        self._reset()
        if returncode:
            destination.unlink(missing_ok=True)
            detail = stderr.decode(errors="replace").strip()
            raise RuntimeError(f"Microphone recording failed ({returncode}): {detail}")
        if not destination.is_file() or destination.stat().st_size == 0:
            destination.unlink(missing_ok=True)
            raise RuntimeError("Microphone recording produced no audio.")
        return destination

    async def cancel(self) -> None:
        process = self._process
        destination = self._destination
        if process is not None and process.returncode is None:
            process.kill()
            await process.communicate()
        self._reset()
        if destination is not None:
            destination.unlink(missing_ok=True)

    def _require_process(self) -> asyncio.subprocess.Process:
        if self._process is None:
            raise RuntimeError("No recording is in progress.")
        return self._process

    def _require_destination(self) -> Path:
        if self._destination is None:
            raise RuntimeError("No recording destination is available.")
        return self._destination

    async def _raise_process_error(self, message: str) -> None:
        process = self._require_process()
        destination = self._destination
        _, stderr = await process.communicate()
        detail = stderr.decode(errors="replace").strip()
        self._reset()
        if destination is not None:
            destination.unlink(missing_ok=True)
        raise RuntimeError(f"{message}: {detail}")

    def _reset(self) -> None:
        self._process = None
        self._destination = None
