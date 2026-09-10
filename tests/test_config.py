from pathlib import Path

import pytest

from voicebox.core.config import Settings


def test_settings_parse_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "123, 456")
    monkeypatch.setenv("TELEGRAM_OUTBOUND_CHAT_ID", "456")
    monkeypatch.setenv("VOICEBOX_INBOX_DIR", "tmp/inbox")

    settings = Settings.from_env()

    assert settings.allowed_chat_ids == frozenset({123, 456})
    assert settings.outbound_chat_id == 456
    assert settings.inbox_dir == Path("tmp/inbox")
    assert settings.outbox_dir == Path("data/outbox")
    assert settings.audio_input == ":0"
    assert settings.playback_attempts == 2
    assert settings.send_attempts == 2
    assert settings.media_retention_hours == 24


def test_settings_parse_reliability_options(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "123")
    monkeypatch.setenv("VOICEBOX_PLAYBACK_ATTEMPTS", "3")
    monkeypatch.setenv("VOICEBOX_SEND_ATTEMPTS", "4")
    monkeypatch.setenv("VOICEBOX_MEDIA_RETENTION_HOURS", "48")

    settings = Settings.from_env()

    assert settings.playback_attempts == 3
    assert settings.send_attempts == 4
    assert settings.media_retention_hours == 48


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("VOICEBOX_PLAYBACK_ATTEMPTS", "0"),
        ("VOICEBOX_SEND_ATTEMPTS", "-1"),
        ("VOICEBOX_MEDIA_RETENTION_HOURS", "not-a-number"),
    ],
)
def test_settings_reject_invalid_reliability_options(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    value: str,
) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "123")
    monkeypatch.setenv(name, value)

    with pytest.raises(ValueError, match=f"{name} must be a positive integer"):
        Settings.from_env()


def test_settings_require_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "")

    with pytest.raises(ValueError, match="at least one"):
        Settings.from_env()


def test_settings_require_destination_for_multiple_chats(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "123,456")
    monkeypatch.delenv("TELEGRAM_OUTBOUND_CHAT_ID", raising=False)

    with pytest.raises(ValueError, match="TELEGRAM_OUTBOUND_CHAT_ID"):
        Settings.from_env()
