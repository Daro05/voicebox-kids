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

        return cls(
            telegram_bot_token=token,
            allowed_chat_ids=chat_ids,
            inbox_dir=Path(os.getenv("VOICEBOX_INBOX_DIR", "data/inbox")),
            audio_player=os.getenv("VOICEBOX_AUDIO_PLAYER") or None,
        )
