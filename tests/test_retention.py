from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from voicebox.core.retention import MediaRetentionPolicy


def test_prune_removes_only_expired_audio(tmp_path: Path) -> None:
    now = datetime(2026, 9, 9, 12, tzinfo=UTC)
    expired = tmp_path / "expired.oga"
    recent = tmp_path / "recent.oga"
    unrelated = tmp_path / "notes.txt"
    for path in (expired, recent, unrelated):
        path.write_text("content")
    old_timestamp = (now - timedelta(hours=25)).timestamp()
    os.utime(expired, (old_timestamp, old_timestamp))
    os.utime(unrelated, (old_timestamp, old_timestamp))

    removed = MediaRetentionPolicy(tmp_path, timedelta(hours=24)).prune(now)

    assert removed == [expired]
    assert not expired.exists()
    assert recent.exists()
    assert unrelated.exists()


def test_prune_ignores_missing_directory(tmp_path: Path) -> None:
    policy = MediaRetentionPolicy(tmp_path / "missing")

    assert policy.prune() == []


def test_retention_must_be_positive(tmp_path: Path) -> None:
    policy = MediaRetentionPolicy(tmp_path, timedelta(0))

    with pytest.raises(ValueError, match="greater than zero"):
        policy.prune()
