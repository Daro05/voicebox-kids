from __future__ import annotations

from pathlib import Path

from voicebox.core.controller import VoiceBoxController
from voicebox.core.state_machine import DeviceState
from voicebox.messaging.base import VoiceNote


def note(name: str, chat_id: str = "123") -> VoiceNote:
    return VoiceNote(
        provider="test",
        sender_id="family",
        chat_id=chat_id,
        local_path=Path(name),
    )


class RecordingPlayer:
    def __init__(self, failures: int = 0) -> None:
        self.failures = failures
        self.calls: list[str] = []

    async def play(self, path: Path) -> None:
        self.calls.append(path.name)
        if self.failures:
            self.failures -= 1
            raise RuntimeError("temporary playback failure")


class RecordingMessenger:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.messages: list[tuple[str, str]] = []

    async def send_text(self, chat_id: str, text: str) -> None:
        if self.fail:
            raise RuntimeError("provider unavailable")
        self.messages.append((chat_id, text))


async def test_controller_plays_queued_notes_in_order() -> None:
    player = RecordingPlayer()
    messenger = RecordingMessenger()
    controller = VoiceBoxController(player, messenger, retry_delay_seconds=0)

    await controller.start()
    await controller.submit(note("first.oga"))
    await controller.submit(note("second.oga"))
    await controller.stop()

    assert player.calls == ["first.oga", "second.oga"]
    assert [message[1] for message in messenger.messages] == [
        "✅ VoiceBox played your voice note.",
        "✅ VoiceBox played your voice note.",
    ]
    assert controller.state.state is DeviceState.IDLE


async def test_controller_retries_playback_before_acknowledging() -> None:
    player = RecordingPlayer(failures=1)
    messenger = RecordingMessenger()
    controller = VoiceBoxController(player, messenger, playback_attempts=2, retry_delay_seconds=0)

    await controller.start()
    await controller.submit(note("retry.oga"))
    await controller.stop()

    assert player.calls == ["retry.oga", "retry.oga"]
    assert messenger.messages == [("123", "✅ VoiceBox played your voice note.")]


async def test_controller_reports_final_playback_failure() -> None:
    player = RecordingPlayer(failures=2)
    messenger = RecordingMessenger()
    controller = VoiceBoxController(player, messenger, playback_attempts=2, retry_delay_seconds=0)

    await controller.start()
    await controller.submit(note("broken.oga"))
    await controller.stop()

    assert messenger.messages == [
        ("123", "⚠️ VoiceBox could not play your voice note. Please try again.")
    ]
    assert controller.state.state is DeviceState.IDLE


async def test_status_failure_does_not_stop_the_queue() -> None:
    player = RecordingPlayer()
    controller = VoiceBoxController(player, RecordingMessenger(fail=True), retry_delay_seconds=0)

    await controller.start()
    await controller.submit(note("first.oga"))
    await controller.submit(note("second.oga"))
    await controller.stop()

    assert player.calls == ["first.oga", "second.oga"]
