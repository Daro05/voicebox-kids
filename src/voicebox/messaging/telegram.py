"""Telegram implementation of the messaging boundary."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from voicebox.messaging.base import VoiceNote, VoiceNoteHandler

logger = logging.getLogger(__name__)


def is_chat_allowed(chat_id: int, allowed_chat_ids: frozenset[int]) -> bool:
    """Keep the provider boundary deny-by-default and easy to unit test."""
    return chat_id in allowed_chat_ids


class TelegramMessagingAdapter:
    def __init__(self, token: str, allowed_chat_ids: frozenset[int], inbox_dir: Path) -> None:
        self._allowed_chat_ids = allowed_chat_ids
        self._inbox_dir = inbox_dir
        self._application = Application.builder().token(token).build()
        self._ready = asyncio.Event()
        self._startup_error: Exception | None = None

    async def run(self, on_voice_note: VoiceNoteHandler) -> None:
        self._inbox_dir.mkdir(parents=True, exist_ok=True)
        initialized = False
        application_started = False
        polling_started = False

        async def receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            message = update.effective_message
            chat = update.effective_chat
            sender = update.effective_user
            if message is None or chat is None or message.voice is None:
                return
            if not is_chat_allowed(chat.id, self._allowed_chat_ids):
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

        try:
            self._application.add_handler(MessageHandler(filters.VOICE, receive))
            await self._application.initialize()
            initialized = True
            await self._application.start()
            application_started = True
            if self._application.updater is None:
                raise RuntimeError("Telegram polling updater is unavailable.")
            await self._application.updater.start_polling(allowed_updates=["message"])
            polling_started = True
            self._ready.set()
            await asyncio.Event().wait()
        except Exception as exc:
            self._startup_error = exc
            raise
        finally:
            self._ready.set()
            try:
                if polling_started and self._application.updater is not None:
                    await self._application.updater.stop()
            finally:
                try:
                    if application_started:
                        await self._application.stop()
                finally:
                    if initialized:
                        await self._application.shutdown()

    async def wait_until_ready(self) -> None:
        await self._ready.wait()
        if self._startup_error is not None:
            raise RuntimeError("Telegram could not start.") from self._startup_error

    async def send_voice_note(self, chat_id: str, path: Path) -> None:
        with path.open("rb") as voice:
            await self._application.bot.send_voice(chat_id=int(chat_id), voice=voice)

    async def send_text(self, chat_id: str, text: str) -> None:
        await self._application.bot.send_message(chat_id=int(chat_id), text=text)
