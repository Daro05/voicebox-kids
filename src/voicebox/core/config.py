"""Environment-backed application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    telegram_bot_token: str
    allowed_chat_ids: frozenset[int]
    inbox_dir: Path = Path("data/inbox")
    audio_player: str | None = None
    playback_attempts: int = 2
    media_retention_hours: int = 24

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv()
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        if not token or token == "replace-me":
            raise ValueError("Set TELEGRAM_BOT_TOKEN in .env before starting VoiceBox.")

        raw_chat_ids = os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "")
        try:
            chat_ids = frozenset(
                int(value.strip()) for value in raw_chat_ids.split(",") if value.strip()
            )
        except ValueError as exc:
            raise ValueError("TELEGRAM_ALLOWED_CHAT_IDS must contain numeric IDs.") from exc
        if not chat_ids:
            raise ValueError("Configure at least one TELEGRAM_ALLOWED_CHAT_IDS value.")

        playback_attempts = _positive_int("VOICEBOX_PLAYBACK_ATTEMPTS", default=2)
        retention_hours = _positive_int("VOICEBOX_MEDIA_RETENTION_HOURS", default=24)

        return cls(
            telegram_bot_token=token,
            allowed_chat_ids=chat_ids,
            inbox_dir=Path(os.getenv("VOICEBOX_INBOX_DIR", "data/inbox")),
            audio_player=os.getenv("VOICEBOX_AUDIO_PLAYER") or None,
            playback_attempts=playback_attempts,
            media_retention_hours=retention_hours,
        )


def _positive_int(name: str, *, default: int) -> int:
    raw_value = os.getenv(name, str(default)).strip()
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a positive integer.") from exc
    if value < 1:
        raise ValueError(f"{name} must be a positive integer.")
    return value
