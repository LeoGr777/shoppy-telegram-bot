"""SQLite storage for shopping list items and per-chat state."""

import logging
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    item_id INTEGER PRIMARY KEY,
    chat_id INTEGER NOT NULL,
    item_name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chats (
    chat_id INTEGER PRIMARY KEY,
    menu_message_id INTEGER
);
"""


class Database:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        # closing() closes the connection, the inner "with" commits or rolls back.
        with closing(sqlite3.connect(self.path, timeout=30)) as conn, conn:
            yield conn

    def setup(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(_SCHEMA)
        logger.info("Database setup complete. Path: %s", self.path)

    def add_items(self, chat_id: int, names: list[str]) -> None:
        with self._connect() as conn:
            conn.executemany(
                "INSERT INTO items (chat_id, item_name) VALUES (?, ?)",
                [(chat_id, name) for name in names],
            )
        logger.info("Added %s item(s) to chat %s", len(names), chat_id)

    def get_items(self, chat_id: int) -> list[tuple[int, str]]:
        with self._connect() as conn:
            return conn.execute(
                "SELECT item_id, item_name FROM items WHERE chat_id = ? ORDER BY item_id",
                (chat_id,),
            ).fetchall()

    def delete_items(self, chat_id: int, item_ids: list[int]) -> None:
        with self._connect() as conn:
            conn.executemany(
                "DELETE FROM items WHERE chat_id = ? AND item_id = ?",
                [(chat_id, item_id) for item_id in item_ids],
            )

    def clear(self, chat_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM items WHERE chat_id = ?", (chat_id,))

    def get_menu_message_id(self, chat_id: int) -> int | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT menu_message_id FROM chats WHERE chat_id = ?", (chat_id,)
            ).fetchone()
        return row[0] if row else None

    def set_menu_message_id(self, chat_id: int, message_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO chats (chat_id, menu_message_id) VALUES (?, ?) "
                "ON CONFLICT(chat_id) DO UPDATE SET menu_message_id = excluded.menu_message_id",
                (chat_id, message_id),
            )
