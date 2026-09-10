from pathlib import Path

import pytest

from voicebox.audio.recorder import FfmpegAudioRecorder, resolve_ffmpeg_command


def test_resolve_ffmpeg_next_to_explicit_ffplay(tmp_path: Path) -> None:
    ffplay = tmp_path / "ffplay"
    ffmpeg = tmp_path / "ffmpeg"
    ffplay.touch()
    ffmpeg.touch()

    assert resolve_ffmpeg_command(str(ffplay)) == str(ffmpeg)


def test_recorder_builds_macos_ogg_opus_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("voicebox.audio.recorder.shutil.which", lambda command: command)
    recorder = FfmpegAudioRecorder(
        "/tools/ffmpeg",
        tmp_path,
        input_device=":2",
    )

    command = recorder.build_command(tmp_path / "note.ogg")

    assert command[0] == "/tools/ffmpeg"
    assert command[command.index("-i") + 1] == ":2"
    assert command[command.index("-c:a") + 1] == "libopus"
    assert command[-1] == str(tmp_path / "note.ogg")
