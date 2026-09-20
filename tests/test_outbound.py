from __future__ import annotations

import asyncio
from pathlib import Path

from voicebox.core.outbound import OutboundVoiceController
from voicebox.core.state_machine import DeviceState
from voicebox.hardware.controls import ControlEvent
from voicebox.messaging.base import MessagingUnavailableError


class RecordingRecorder:
    def __init__(self, path: Path, *, fail_start: bool = False) -> None:
        self.path = path
        self.fail_start = fail_start
        self.started = 0
        self.stopped = 0
        self.cancelled = 0

    async def start(self) -> None:
        self.started += 1
        if self.fail_start:
            raise RuntimeError("microphone unavailable")

    async def stop(self) -> Path:
        self.stopped += 1
        return self.path

    async def cancel(self) -> None:
        self.cancelled += 1


class RecordingSender:
    def __init__(self, *, failures: int = 0) -> None:
        self.failures = failures
        self.sent: list[tuple[str, Path]] = []

    async def send_voice_note(self, chat_id: str, path: Path) -> None:
        self.sent.append((chat_id, path))
        if self.failures:
            self.failures -= 1
            raise RuntimeError("Telegram unavailable")


class RecordingControls:
    def __init__(self) -> None:
        self.statuses: list[str] = []
        self.sent = asyncio.Event()

    async def next_event(self) -> ControlEvent:
        raise AssertionError("not used by these tests")

    async def set_status(self, status: str) -> None:
        self.statuses.append(status)
        if status in {"sent", "offline", "error"}:
            self.sent.set()


class TimeoutControls(RecordingControls):
    def __init__(self) -> None:
        super().__init__()
        self.events = 0

    async def next_event(self) -> ControlEvent:
        self.events += 1
        if self.events == 1:
            return ControlEvent.PRESS
        await asyncio.Event().wait()
        raise AssertionError("unreachable")


class OfflineSender(RecordingSender):
    async def send_voice_note(self, chat_id: str, path: Path) -> None:
        self.sent.append((chat_id, path))
        raise MessagingUnavailableError("offline")


async def test_press_release_records_sends_and_deletes_local_copy(tmp_path: Path) -> None:
    recording = tmp_path / "note.ogg"
    recording.write_bytes(b"opus")
    recorder = RecordingRecorder(recording)
    sender = RecordingSender()
    controls = RecordingControls()
    controller = OutboundVoiceController(
        recorder,
        sender,
        controls,
        target_chat_id="123",
        retry_delay_seconds=0,
    )

    await controller.handle_event(ControlEvent.PRESS)
    await controller.handle_event(ControlEvent.RELEASE)

    assert recorder.started == 1
    assert recorder.stopped == 1
    assert sender.sent == [("123", recording)]
    assert controls.statuses == ["recording", "sending", "sent"]
    assert not recording.exists()
    assert controller.state.state is DeviceState.IDLE


async def test_send_is_retried_and_failed_recording_is_retained(tmp_path: Path) -> None:
    recording = tmp_path / "note.ogg"
    recording.write_bytes(b"opus")
    sender = RecordingSender(failures=2)
    controls = RecordingControls()
    controller = OutboundVoiceController(
        RecordingRecorder(recording),
        sender,
        controls,
        target_chat_id="123",
        send_attempts=2,
        retry_delay_seconds=0,
    )

    await controller.handle_event(ControlEvent.PRESS)
    await controller.handle_event(ControlEvent.RELEASE)

    assert len(sender.sent) == 2
    assert controls.statuses[-1] == "error"
    assert recording.exists()
    assert controller.state.state is DeviceState.IDLE


async def test_recording_start_failure_recovers_to_idle(tmp_path: Path) -> None:
    recorder = RecordingRecorder(tmp_path / "note.ogg", fail_start=True)
    controls = RecordingControls()
    controller = OutboundVoiceController(
        recorder,
        RecordingSender(),
        controls,
        target_chat_id="123",
    )

    await controller.handle_event(ControlEvent.PRESS)

    assert recorder.cancelled == 1
    assert controls.statuses == ["recording", "error"]
    assert controller.state.state is DeviceState.IDLE


async def test_cancel_discards_recording_without_sending(tmp_path: Path) -> None:
    recorder = RecordingRecorder(tmp_path / "note.ogg")
    sender = RecordingSender()
    controls = RecordingControls()
    controller = OutboundVoiceController(
        recorder,
        sender,
        controls,
        target_chat_id="123",
    )

    await controller.handle_event(ControlEvent.PRESS)
    await controller.handle_event(ControlEvent.CANCEL)

    assert recorder.cancelled == 1
    assert sender.sent == []
    assert controls.statuses == ["recording", "cancelled"]
    assert controller.state.state is DeviceState.IDLE


async def test_network_failure_reports_offline_and_retains_recording(tmp_path: Path) -> None:
    recording = tmp_path / "note.ogg"
    recording.write_bytes(b"opus")
    controls = RecordingControls()
    controller = OutboundVoiceController(
        RecordingRecorder(recording),
        OfflineSender(),
        controls,
        target_chat_id="123",
        send_attempts=1,
        retry_delay_seconds=0,
    )

    await controller.handle_event(ControlEvent.PRESS)
    await controller.handle_event(ControlEvent.RELEASE)

    assert controls.statuses[-1] == "offline"
    assert recording.exists()
    assert controller.state.state is DeviceState.IDLE


async def test_recording_stops_and_sends_at_time_limit(tmp_path: Path) -> None:
    recording = tmp_path / "note.ogg"
    recording.write_bytes(b"opus")
    controls = TimeoutControls()
    controller = OutboundVoiceController(
        RecordingRecorder(recording),
        RecordingSender(),
        controls,
        target_chat_id="123",
        max_recording_seconds=0.01,
    )

    task = asyncio.create_task(controller.run())
    await asyncio.wait_for(controls.sent.wait(), timeout=1)
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)

    assert controls.statuses == ["idle", "recording", "limit", "sending", "sent"]
    assert not recording.exists()
    assert controller.state.state is DeviceState.IDLE
