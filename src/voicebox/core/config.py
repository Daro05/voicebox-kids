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
    outbound_chat_id: int
    inbox_dir: Path = Path("data/inbox")
    outbox_dir: Path = Path("data/outbox")
    audio_player: str | None = None
    audio_input: str = ":0"
    playback_attempts: int = 2
    send_attempts: int = 2
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

        raw_outbound_chat_id = os.getenv("TELEGRAM_OUTBOUND_CHAT_ID", "").strip()
        if raw_outbound_chat_id:
            try:
                outbound_chat_id = int(raw_outbound_chat_id)
            except ValueError as exc:
                raise ValueError("TELEGRAM_OUTBOUND_CHAT_ID must be numeric.") from exc
            if outbound_chat_id not in chat_ids:
                raise ValueError("TELEGRAM_OUTBOUND_CHAT_ID must be in the allowed chat list.")
        elif len(chat_ids) == 1:
            outbound_chat_id = next(iter(chat_ids))
        else:
            raise ValueError(
                "Set TELEGRAM_OUTBOUND_CHAT_ID when more than one chat is allowed."
            )

        playback_attempts = _positive_int("VOICEBOX_PLAYBACK_ATTEMPTS", default=2)
        send_attempts = _positive_int("VOICEBOX_SEND_ATTEMPTS", default=2)
        retention_hours = _positive_int("VOICEBOX_MEDIA_RETENTION_HOURS", default=24)

        return cls(
            telegram_bot_token=token,
            allowed_chat_ids=chat_ids,
            outbound_chat_id=outbound_chat_id,
            inbox_dir=Path(os.getenv("VOICEBOX_INBOX_DIR", "data/inbox")),
            outbox_dir=Path(os.getenv("VOICEBOX_OUTBOX_DIR", "data/outbox")),
            audio_player=os.getenv("VOICEBOX_AUDIO_PLAYER") or None,
            audio_input=os.getenv("VOICEBOX_AUDIO_INPUT", ":0"),
            playback_attempts=playback_attempts,
            send_attempts=send_attempts,
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
