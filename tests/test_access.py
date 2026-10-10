import asyncio
from types import SimpleNamespace

import pytest
from telegram.constants import ChatType
from telegram.ext import ApplicationHandlerStop

from shoppy.bot import restrict_chats
from shoppy.parsing import parse_chat_ids


def run_gate(chat):
    update = SimpleNamespace(effective_chat=chat)
    context = SimpleNamespace(bot_data={"allowed_chat_ids": {1, -100}})
    asyncio.run(restrict_chats(update, context))


def test_allowed_chat_passes():
    run_gate(SimpleNamespace(id=-100, type=ChatType.SUPERGROUP))


@pytest.mark.parametrize(
    "chat",
    [
        SimpleNamespace(id=2, type=ChatType.PRIVATE),
        SimpleNamespace(id=-5, type=ChatType.GROUP),
        None,
    ],
)
def test_other_updates_are_blocked(chat):
    with pytest.raises(ApplicationHandlerStop):
        run_gate(chat)


def test_parse_chat_ids():
    assert parse_chat_ids("123, -100456,") == {123, -100456}
    assert parse_chat_ids("") == set()
    with pytest.raises(ValueError):
        parse_chat_ids("abc")
