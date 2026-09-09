"""Provider-neutral messaging contracts."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True, slots=True)
class VoiceNote:
    provider: str
    sender_id: str
    chat_id: str
    local_path: Path


VoiceNoteHandler = Callable[[VoiceNote], Awaitable[None]]


class MessagingAdapter(Protocol):
    async def run(self, on_voice_note: VoiceNoteHandler) -> None:
        """Receive messages until the process is stopped."""
        ...

    async def send_voice_note(self, chat_id: str, path: Path) -> None:
        """Send one local recording through the provider."""
        ...

    async def send_text(self, chat_id: str, text: str) -> None:
        """Send a short provider-neutral status message."""
        ...
