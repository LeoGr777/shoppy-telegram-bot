# database.py
"""
This module contains the setup of the database as well as functions like adding items, deleting items, etc.
"""
# ### IMPORTS ###

# 1.1 Standard Libraries
import sqlite3
import logging
import os

# =============================================================================
#  DATABASE SETUP
# =============================================================================
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_DIR  = os.getenv("DB_DIR", os.path.join(PROJECT_ROOT, "app", "data"))
DB_NAME = os.getenv("DB_NAME", "shopping_list.db")
DB_PATH = os.getenv("DB_PATH", os.path.join(DB_DIR, DB_NAME))

def connect():
    """Centralized connection function with correct path."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH, timeout=30)

def setup_database() -> None:
    """Creates the database file and the 'items' table if they don't exist."""
    try:
        with connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    item_id INTEGER PRIMARY KEY,
                    chat_id INTEGER NOT NULL,
                    item_name TEXT NOT NULL
                )
            """)
        logging.info("Database setup complete. Path: %s", DB_PATH)
    except sqlite3.Error as e:
        logging.error("Database error during setup: %s", e)

# =============================================================================
#  CRUD FUNCTIONS (Create, Read, Update, Delete)
# =============================================================================

def add_item(chat_id: int, item_name: str) -> bool:
    """Adds a new item to the database for a specific chat."""
    try:
       with connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO items (chat_id, item_name) VALUES (?, ?)",
                (chat_id, item_name)
            )
            logging.info("DB: Inserted id=%s chat_id=%s name=%s", cursor.lastrowid, chat_id, item_name)
            return True
    except sqlite3.Error as e:
        logging.error("Failed to add item: %s", e)
        return False

def get_items(chat_id: int) -> list:
    """Retrieves all items for a specific chat from the database."""
    try:
       with connect() as conn:
            cursor = conn.cursor()     
            cursor.execute(
                "SELECT item_id, item_name FROM items WHERE chat_id = ?",
                (chat_id,)
            )  
            items = cursor.fetchall()
            return items
    except sqlite3.Error as e:
        logging.error(f"Failed to get items: {e}")
        return []

def delete_item(item_id: int) -> bool:
    """Deletes an item from the database using its unique item_id."""
    try:
       with connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM items WHERE item_id = ?", (item_id,))
            # Check if a row was actually deleted
            success = cursor.rowcount > 0
            return success
    except sqlite3.Error as e:
        logging.error(f"Failed to delete item: {e}")
        return False
    
def clear_list(chat_id: int) -> bool:
    """Drops the item list using its unique chat_id"""
    try:
       with connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM items WHERE chat_id = ?", (chat_id,))
            # Check if a row was actually deleted
            success = cursor.rowcount > 0
            return success
    except sqlite3.Error as e:
        logging.error(f"Failed to delete list: {e}")
        return False
