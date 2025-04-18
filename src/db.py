"""
Database module for tracking chats where the bot is added.
"""
import os
import psycopg2

# Ensure psycopg2 returns tuples for fetchall
from psycopg2.extras import RealDictCursor
from typing import Optional

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
                # Create or update chats table to include owner_id
                curs.execute(
                    """
                    CREATE TABLE IF NOT EXISTS chats (
                        id SERIAL PRIMARY KEY,
                        chat_id BIGINT UNIQUE NOT NULL,
                        title TEXT,
                        owner_id BIGINT
                    );
                    """
                )
                # Ensure owner_id column exists for existing tables
                curs.execute(
                    """
                    ALTER TABLE chats
                    ADD COLUMN IF NOT EXISTS owner_id BIGINT;
                    """
                )
    finally:
        conn.close()

def add_chat(chat_id: int, title: str, owner_id: Optional[int] = None) -> None:
    """Add or update a chat record, optionally setting the owner_id."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as curs:
                # Insert or update, preserving existing owner_id if already set
                # Upsert the chat record, preserving existing owner_id when present
                query = (
                    "INSERT INTO chats (chat_id, title, owner_id) "
                    "VALUES (%s, %s, %s) "
                    "ON CONFLICT (chat_id) DO UPDATE SET "
                    "title = EXCLUDED.title, "
                    "owner_id = COALESCE(chats.owner_id, EXCLUDED.owner_id);"
                )
                curs.execute(query, (chat_id, title, owner_id))
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
    
def get_chat_owner(chat_id: int) -> Optional[int]:
    """Return the owner_id for a given chat_id, or None if not set."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as curs:
                curs.execute(
                    "SELECT owner_id FROM chats WHERE chat_id = %s;",
                    (chat_id,),
                )
                row = curs.fetchone()
                if row:
                    return row[0]
                return None
    finally:
        conn.close()