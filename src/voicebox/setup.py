"""Guided, local-only setup for a Telegram laptop prototype."""

from __future__ import annotations

import asyncio
import getpass
import os
from dataclasses import dataclass
from pathlib import Path

from telegram import Bot
from telegram.error import TelegramError

from voicebox.audio.player import LocalAudioPlayer


@dataclass(frozen=True, slots=True)
class DiscoveredChat:
    chat_id: int
    label: str


def render_env(token: str, chat_id: int, audio_player: str | None = None) -> str:
    """Build the project-specific environment file without logging its secret."""
    lines = [
        f"TELEGRAM_BOT_TOKEN={token}",
        f"TELEGRAM_ALLOWED_CHAT_IDS={chat_id}",
        f"TELEGRAM_OUTBOUND_CHAT_ID={chat_id}",
        "VOICEBOX_INBOX_DIR=data/inbox",
        "VOICEBOX_OUTBOX_DIR=data/outbox",
        f"VOICEBOX_AUDIO_PLAYER={audio_player or ''}",
        "VOICEBOX_AUDIO_INPUT=:0",
        "VOICEBOX_PLAYBACK_ATTEMPTS=2",
        "VOICEBOX_SEND_ATTEMPTS=2",
        "VOICEBOX_MEDIA_RETENTION_HOURS=24",
    ]
    return "\n".join(lines) + "\n"


def write_env(
    path: Path,
    *,
    token: str,
    chat_id: int,
    audio_player: str | None = None,
) -> None:
    """Create a private env file and refuse to overwrite existing credentials."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as env_file:
            env_file.write(render_env(token, chat_id, audio_player))
    except Exception:
        path.unlink(missing_ok=True)
        raise


def _chat_label(message: object) -> str:
    chat = getattr(message, "chat", None)
    if chat is None:
        return "approved chat"
    title = getattr(chat, "title", None)
    if title:
        return str(title)
    full_name = getattr(chat, "full_name", None)
    if full_name:
        return str(full_name)
    return "private chat"


async def discover_voice_chat(token: str, timeout_seconds: int = 120) -> tuple[str, DiscoveredChat]:
    """Verify the bot and discover a chat from an incoming Telegram voice note."""
    try:
        async with Bot(token=token) as bot:
            identity = await bot.get_me()
            deadline = asyncio.get_running_loop().time() + timeout_seconds
            offset: int | None = None

            while asyncio.get_running_loop().time() < deadline:
                remaining = int(deadline - asyncio.get_running_loop().time())
                updates = await bot.get_updates(
                    offset=offset,
                    timeout=max(1, min(20, remaining)),
                    allowed_updates=["message"],
                )
                for update in updates:
                    offset = update.update_id + 1
                    message = update.effective_message
                    chat = update.effective_chat
                    if message is not None and message.voice is not None and chat is not None:
                        return identity.username or identity.first_name, DiscoveredChat(
                            chat_id=chat.id,
                            label=_chat_label(message),
                        )
    except TelegramError as exc:
        raise RuntimeError(
            "Telegram could not verify the bot. Check the token and network connection."
        ) from exc

    raise TimeoutError("No Telegram voice note arrived before the setup timeout.")


async def run_guided_setup(env_path: Path = Path(".env")) -> None:
    """Guide the owner through bot verification and allowlist discovery."""
    if env_path.exists():
        raise FileExistsError(
            f"{env_path} already exists. Move it aside before running setup again."
        )

    print("VoiceBox Kids setup")
    print("Create a bot with Telegram BotFather, then paste its token below.")
    token = getpass.getpass("Bot token (hidden): ").strip()
    if not token:
        raise ValueError("A Telegram bot token is required.")

    print("Verifying the bot…")
    print("When prompted, send one voice note directly to the bot from an approved chat.")
    bot_name, chat = await discover_voice_chat(token)
    player = LocalAudioPlayer.detect_command()
    # Keep automatic detection enabled so installing ffplay later takes priority
    # over a less compatible player discovered during setup.
    write_env(env_path, token=token, chat_id=chat.chat_id)

    print(f"Connected to @{bot_name} and approved {chat.label} ({chat.chat_id}).")
    print(f"Saved private configuration to {env_path} with owner-only permissions.")
    if player:
        print(f"Detected audio player: {player}.")
    else:
        print("No supported audio player found. Install ffplay before running VoiceBox.")
    print("Next: run `voicebox doctor`, then `voicebox run`.")
