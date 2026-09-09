from voicebox.messaging.telegram import is_chat_allowed


def test_only_explicitly_allowed_chats_are_accepted() -> None:
    allowlist = frozenset({123, -456})

    assert is_chat_allowed(123, allowlist)
    assert is_chat_allowed(-456, allowlist)
    assert not is_chat_allowed(999, allowlist)
