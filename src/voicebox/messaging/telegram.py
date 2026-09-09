"""Telegram implementation of the messaging boundary."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from voicebox.messaging.base import VoiceNote, VoiceNoteHandler

logger = logging.getLogger(__name__)


class TelegramMessagingAdapter:
    def __init__(self, token: str, allowed_chat_ids: frozenset[int], inbox_dir: Path) -> None:
        self._allowed_chat_ids = allowed_chat_ids
        self._inbox_dir = inbox_dir
        self._application = Application.builder().token(token).build()

    async def run(self, on_voice_note: VoiceNoteHandler) -> None:
        self._inbox_dir.mkdir(parents=True, exist_ok=True)

        async def receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            message = update.effective_message
            chat = update.effective_chat
            sender = update.effective_user
            if message is None or chat is None or message.voice is None:
                return
            if chat.id not in self._allowed_chat_ids:
                logger.warning("Ignored voice note from unapproved chat %s", chat.id)
                return

            remote_file = await context.bot.get_file(message.voice.file_id)
            filename = f"telegram-{message.message_id}-{message.voice.file_unique_id}.oga"
            destination = self._inbox_dir / filename
            await remote_file.download_to_drive(custom_path=destination)
            await on_voice_note(
                VoiceNote(
                    provider="telegram",
                    sender_id=str(sender.id) if sender else "unknown",
                    chat_id=str(chat.id),
                    local_path=destination,
                )
            )

        self._application.add_handler(MessageHandler(filters.VOICE, receive))
        await self._application.initialize()
        await self._application.start()
        if self._application.updater is None:
            raise RuntimeError("Telegram polling updater is unavailable.")
        await self._application.updater.start_polling(allowed_updates=["message"])
        try:
            await asyncio.Event().wait()
        finally:
            await self._application.updater.stop()
            await self._application.stop()
            await self._application.shutdown()

    async def send_voice_note(self, chat_id: str, path: Path) -> None:
        with path.open("rb") as voice:
            await self._application.bot.send_voice(chat_id=int(chat_id), voice=voice)
