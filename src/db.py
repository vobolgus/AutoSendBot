"""
Database module for tracking chats where the bot is added.
"""
import os
import psycopg2

# Ensure psycopg2 returns tuples for fetchall
from psycopg2.extras import RealDictCursor

# Expected environment variable DATABASE_URL, e.g., from Railway
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable not set")
    # sslmode=require helps on some hosted environments
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def init_db():
    """Initialize the database, creating tables if they do not exist."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as curs:
                curs.execute(
                    """
                    CREATE TABLE IF NOT EXISTS chats (
                        id SERIAL PRIMARY KEY,
                        chat_id BIGINT UNIQUE NOT NULL,
                        title TEXT
                    );
                    """
                )
    finally:
        conn.close()

def add_chat(chat_id: int, title: str) -> None:
    """Add or update a chat record."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as curs:
                curs.execute(
                    """
                    INSERT INTO chats (chat_id, title)
                    VALUES (%s, %s)
                    ON CONFLICT (chat_id) DO UPDATE SET title = EXCLUDED.title;
                    """,
                    (chat_id, title),
                )
    finally:
        conn.close()

def remove_chat(chat_id: int) -> None:
    """Remove a chat record."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as curs:
                curs.execute(
                    "DELETE FROM chats WHERE chat_id = %s;",
                    (chat_id,),
                )
    finally:
        conn.close()

def get_chats() -> list[tuple[int, str]]:
    """Return all recorded chats as a list of (chat_id, title)."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as curs:
                curs.execute("SELECT chat_id, title FROM chats;")
                return curs.fetchall()
    finally:
        conn.close()