from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def replace_once(path: Path, old: str, new: str) -> bool:
    text = path.read_text()
    if new in text:
        return False
    if old not in text:
        raise SystemExit(f"expected block not found in {path}")
    path.write_text(text.replace(old, new, 1))
    return True


telegram_path = ROOT / "gateway" / "platforms" / "telegram.py"
telegram_old = """        # Build source
        source = self.build_source(
            chat_id=str(chat.id),
            chat_name=chat.title or (chat.full_name if hasattr(chat, "full_name") else None),
            chat_type=chat_type,
            user_id=str(user.id) if user else None,
            user_name=user.full_name if user else None,
            thread_id=thread_id_str,
            chat_topic=chat_topic,
        )
"""
telegram_new = """        # Telegram can omit from_user on some DM updates; fall back to the DM chat identity.
        dm_fallback_user_id = str(chat.id) if chat_type == "dm" else None
        dm_fallback_user_name = chat.full_name if hasattr(chat, "full_name") and chat_type == "dm" else None

        # Build source
        source = self.build_source(
            chat_id=str(chat.id),
            chat_name=chat.title or (chat.full_name if hasattr(chat, "full_name") else None),
            chat_type=chat_type,
            user_id=str(user.id) if user else dm_fallback_user_id,
            user_name=user.full_name if user else dm_fallback_user_name,
            thread_id=thread_id_str,
            chat_topic=chat_topic,
        )
"""

test_path = ROOT / "tests" / "gateway" / "test_telegram_thread_fallback.py"
test_old = """    assert event.source.thread_id == "1"


@pytest.mark.asyncio
async def test_send_omits_general_topic_thread_id():
"""
test_new = """    assert event.source.thread_id == "1"


def test_dm_without_from_user_falls_back_to_chat_identity():
    \"\"\"DM messages without from_user should still keep a usable user identity.\"\"\"
    adapter = _make_adapter()
    message = SimpleNamespace(
        text="hello from DM",
        caption=None,
        chat=SimpleNamespace(
            id=789,
            type="private",
            title=None,
            full_name="Fallback User",
        ),
        from_user=None,
        message_thread_id=None,
        reply_to_message=None,
        message_id=11,
        date=None,
    )

    event = adapter._build_message_event(message, msg_type=SimpleNamespace(value="text"))

    assert event.source.chat_type == "dm"
    assert event.source.user_id == "789"
    assert event.source.user_name == "Fallback User"


@pytest.mark.asyncio
async def test_send_omits_general_topic_thread_id():
"""

changed = False
changed |= replace_once(telegram_path, telegram_old, telegram_new)
changed |= replace_once(test_path, test_old, test_new)

if changed:
    print("Applied Telegram DM fallback patch")
else:
    print("Telegram DM fallback patch already present")
