"""Application composition root."""

from __future__ import annotations

import asyncio
import logging

from voicebox.audio.player import LocalAudioPlayer
from voicebox.core.config import Settings
from voicebox.core.state_machine import DeviceState, StateMachine
from voicebox.messaging.base import VoiceNote
from voicebox.messaging.telegram import TelegramMessagingAdapter

logger = logging.getLogger(__name__)


async def run() -> None:
    settings = Settings.from_env()
    player = LocalAudioPlayer(settings.audio_player)
    state = StateMachine()
    messaging = TelegramMessagingAdapter(
        token=settings.telegram_bot_token,
        allowed_chat_ids=settings.allowed_chat_ids,
        inbox_dir=settings.inbox_dir,
    )

    async def on_voice_note(note: VoiceNote) -> None:
        try:
            state.transition_to(DeviceState.RECEIVING)
            logger.info("Received voice note from approved chat %s", note.chat_id)
            state.transition_to(DeviceState.PLAYING)
            await player.play(note.local_path)
            state.transition_to(DeviceState.IDLE)
        except Exception:
            logger.exception("Could not process voice note")
            if state.state is not DeviceState.ERROR:
                state.transition_to(DeviceState.ERROR)
            state.transition_to(DeviceState.IDLE)

    logger.info("VoiceBox is listening for approved Telegram voice notes")
    await messaging.run(on_voice_note)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        asyncio.run(run())
    except (KeyboardInterrupt, SystemExit):
        logger.info("VoiceBox stopped")
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
