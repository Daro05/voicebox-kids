from voicebox.audio.cues import FfplayStatusCues


def test_ffplay_cue_uses_generated_sine_tone() -> None:
    cues = FfplayStatusCues("/project/.ffmpeg/bin/ffplay")

    command = cues.build_command(880, 0.1)

    assert command[0] == "/project/.ffmpeg/bin/ffplay"
    assert command[command.index("-f") + 1] == "lavfi"
    assert command[-1] == "sine=frequency=880:duration=0.1"
