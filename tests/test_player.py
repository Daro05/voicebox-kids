from pathlib import Path

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
