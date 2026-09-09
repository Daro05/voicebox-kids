from pathlib import Path

import pytest

from voicebox.audio.player import LocalAudioPlayer


def test_ffplay_uses_noninteractive_flags() -> None:
    player = LocalAudioPlayer("ffplay")

    assert player.build_command(Path("note.oga")) == (
        "ffplay",
        "-nodisp",
        "-autoexit",
        "-loglevel",
        "error",
        "note.oga",
    )


def test_native_player_receives_path() -> None:
    player = LocalAudioPlayer("afplay")

    assert player.build_command(Path("note.oga")) == ("afplay", "note.oga")


def test_ffplay_path_receives_headless_playback_flags() -> None:
    player = LocalAudioPlayer("/project/.ffmpeg/bin/ffplay")

    assert player.build_command(Path("note.oga")) == (
        "/project/.ffmpeg/bin/ffplay",
        "-nodisp",
        "-autoexit",
        "-loglevel",
        "error",
        "note.oga",
    )


def test_detection_prefers_ffplay(monkeypatch: pytest.MonkeyPatch) -> None:
    available = {"ffplay", "afplay"}
    monkeypatch.setattr("voicebox.audio.player.shutil.which", lambda command: command in available)

    assert LocalAudioPlayer.detect_command() == "ffplay"


def test_explicit_player_path_can_be_validated(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "voicebox.audio.player.shutil.which",
        lambda command: command if command == "/project/.ffmpeg/bin/ffplay" else None,
    )

    assert LocalAudioPlayer.is_command_available("/project/.ffmpeg/bin/ffplay")
