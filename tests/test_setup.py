from __future__ import annotations

import stat
from pathlib import Path

import pytest

from voicebox.setup import render_env, write_env


def test_render_env_contains_only_expected_configuration() -> None:
    content = render_env("test-token", -123, "ffplay")

    assert content == (
        "TELEGRAM_BOT_TOKEN=test-token\n"
        "TELEGRAM_ALLOWED_CHAT_IDS=-123\n"
        "VOICEBOX_INBOX_DIR=data/inbox\n"
        "VOICEBOX_AUDIO_PLAYER=ffplay\n"
    )


def test_write_env_creates_owner_only_file(tmp_path: Path) -> None:
    destination = tmp_path / ".env"

    write_env(destination, token="test-token", chat_id=123)

    assert stat.S_IMODE(destination.stat().st_mode) == 0o600
    assert "TELEGRAM_BOT_TOKEN=test-token" in destination.read_text()


def test_write_env_refuses_to_replace_credentials(tmp_path: Path) -> None:
    destination = tmp_path / ".env"
    destination.write_text("existing-secret")

    with pytest.raises(FileExistsError):
        write_env(destination, token="new-token", chat_id=123)

    assert destination.read_text() == "existing-secret"
