"""Application composition root."""

from __future__ import annotations

import argparse
import asyncio
import logging
from collections.abc import Sequence
from datetime import timedelta
from pathlib import Path

from voicebox.audio.player import AudioPlayerUnavailableError, LocalAudioPlayer
from voicebox.core.config import Settings
from voicebox.core.controller import VoiceBoxController
from voicebox.core.retention import MediaRetentionPolicy
from voicebox.messaging.telegram import TelegramMessagingAdapter
from voicebox.setup import run_guided_setup

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Enable application logs without exposing Telegram credentials in request URLs."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)


async def run_voicebox() -> None:
    settings = Settings.from_env()
    player = LocalAudioPlayer(settings.audio_player)
    messaging = TelegramMessagingAdapter(
        token=settings.telegram_bot_token,
        allowed_chat_ids=settings.allowed_chat_ids,
        inbox_dir=settings.inbox_dir,
    )
    controller = VoiceBoxController(
        player,
        messaging,
        playback_attempts=settings.playback_attempts,
    )
    retention = MediaRetentionPolicy(
        settings.inbox_dir,
        max_age=timedelta(hours=settings.media_retention_hours),
    )
    removed = retention.prune()
    if removed:
        logger.info("Removed %s expired voice note(s)", len(removed))

    logger.info("VoiceBox is listening for approved Telegram voice notes")
    await controller.start()
    try:
        await messaging.run(controller.submit)
    finally:
        await controller.stop()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="voicebox",
        description="Run and configure the VoiceBox Kids laptop prototype.",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("run", help="Listen for approved Telegram voice notes.")
    setup_parser = subparsers.add_parser("setup", help="Configure Telegram securely.")
    setup_parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
        help="Configuration file to create (default: .env).",
    )
    subparsers.add_parser("doctor", help="Check configuration and local audio support.")
    return parser


def doctor() -> bool:
    healthy = True
    settings: Settings | None = None
    try:
        settings = Settings.from_env()
        print(f"✓ Configuration loaded; {len(settings.allowed_chat_ids)} chat(s) approved.")
    except ValueError as exc:
        print(f"✗ Configuration: {exc}")
        healthy = False

    if settings and settings.audio_player:
        command = (
            settings.audio_player
            if LocalAudioPlayer.is_command_available(settings.audio_player)
            else None
        )
    else:
        command = LocalAudioPlayer.detect_command()
    if command:
        player_name = Path(command).name
        print(f"✓ Audio player available: {player_name}.")
        if player_name == "afplay":
            print("! ffplay is recommended for Telegram Ogg/Opus compatibility.")
    else:
        print("✗ Audio player: install ffplay or configure VOICEBOX_AUDIO_PLAYER.")
        healthy = False
    return healthy


async def dispatch(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "setup":
        await run_guided_setup(args.env_file)
        return 0
    if args.command == "doctor":
        return 0 if doctor() else 1
    await run_voicebox()
    return 0


def main() -> None:
    configure_logging()
    try:
        raise SystemExit(asyncio.run(dispatch()))
    except (KeyboardInterrupt, SystemExit):
        raise
    except (AudioPlayerUnavailableError, FileExistsError, TimeoutError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
