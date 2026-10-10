import pytest

from shoppy.db import Database
from shoppy.parsing import ids_except


@pytest.fixture
def db(tmp_path):
    database = Database(tmp_path / "nested" / "test.db")
    database.setup()
    return database


def names(db, chat_id):
    return [name for _, name in db.get_items(chat_id)]


def test_add_and_get_items_in_insertion_order(db):
    db.add_items(1, ["milk", "bread"])
    db.add_items(1, ["eggs"])
    assert names(db, 1) == ["milk", "bread", "eggs"]


def test_chats_are_isolated(db):
    db.add_items(1, ["milk"])
    db.add_items(2, ["beer"])
    assert names(db, 1) == ["milk"]
    db.clear(1)
    assert names(db, 1) == []
    assert names(db, 2) == ["beer"]


def test_delete_items_only_in_own_chat(db):
    db.add_items(1, ["milk"])
    db.add_items(2, ["beer"])
    foreign_id = db.get_items(2)[0][0]
    db.delete_items(1, [foreign_id])
    assert names(db, 2) == ["beer"]


def test_clear_except_keeps_selected(db):
    db.add_items(1, ["milk", "bread", "eggs"])
    db.delete_items(1, ids_except(db.get_items(1), {1, 3}))
    assert names(db, 1) == ["milk", "eggs"]


def test_menu_message_id_survives_new_instance(db):
    assert db.get_menu_message_id(1) is None
    db.set_menu_message_id(1, 42)
    db.set_menu_message_id(1, 43)
    assert Database(db.path).get_menu_message_id(1) == 43


def test_setup_is_idempotent(db):
    db.add_items(1, ["milk"])
    db.setup()
    assert names(db, 1) == ["milk"]
