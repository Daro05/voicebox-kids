from pathlib import Path

import pytest

from voicebox.core.config import Settings


def test_settings_parse_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "123, 456")
    monkeypatch.setenv("VOICEBOX_INBOX_DIR", "tmp/inbox")

    settings = Settings.from_env()

    assert settings.allowed_chat_ids == frozenset({123, 456})
    assert settings.inbox_dir == Path("tmp/inbox")


def test_settings_require_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "")

    with pytest.raises(ValueError, match="at least one"):
        Settings.from_env()
