"""Local media-retention policy for downloaded voice notes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

_AUDIO_SUFFIXES = frozenset({".oga", ".ogg", ".opus", ".wav", ".mp3"})


@dataclass(frozen=True, slots=True)
class MediaRetentionPolicy:
    directory: Path
    max_age: timedelta = timedelta(hours=24)

    def prune(self, now: datetime | None = None) -> list[Path]:
        """Delete expired audio files and return the paths that were removed."""
        if self.max_age <= timedelta(0):
            raise ValueError("Media retention must be greater than zero.")
        if not self.directory.exists():
            return []

        reference = now or datetime.now(UTC)
        cutoff = reference.timestamp() - self.max_age.total_seconds()
        removed: list[Path] = []
        for path in self.directory.iterdir():
            if (
                path.is_symlink()
                or not path.is_file()
                or path.suffix.lower() not in _AUDIO_SUFFIXES
            ):
                continue
            if path.stat().st_mtime < cutoff:
                path.unlink()
                removed.append(path)
        return removed
