"""
database.py — SQLite persistence layer for user accounts and league settings.
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    conn = get_connection()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS league_settings (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id            INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                league_id          TEXT,
                season_year        INTEGER,
                espn_s2            TEXT,
                swid               TEXT,
                anthropic_api_key  TEXT,
                team_name_filter   TEXT,
                updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.close()


# ── Users ──────────────────────────────────────────────────────────────────

def create_user(username: str, password_hash: str):
    """Insert a new user. Returns (True, None) or (False, error_message)."""
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash),
            )
        return True, None
    except sqlite3.IntegrityError:
        return False, "Username already taken."
    finally:
        conn.close()


def get_user_by_username(username: str):
    """Return a user row dict or None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ── League settings ────────────────────────────────────────────────────────

def upsert_league_settings(
    user_id: int,
    league_id: str,
    season_year: int,
    espn_s2_enc: str,
    swid_enc: str,
    api_key_enc: str,
    team_name_filter: str,
) -> None:
    """Insert or update the league settings row for the given user."""
    conn = get_connection()
    try:
        with conn:
            existing = conn.execute(
                "SELECT id FROM league_settings WHERE user_id = ?", (user_id,)
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE league_settings
                    SET league_id = ?, season_year = ?, espn_s2 = ?, swid = ?,
                        anthropic_api_key = ?, team_name_filter = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                    """,
                    (league_id, season_year, espn_s2_enc, swid_enc,
                     api_key_enc, team_name_filter, user_id),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO league_settings
                        (user_id, league_id, season_year, espn_s2, swid,
                         anthropic_api_key, team_name_filter)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, league_id, season_year, espn_s2_enc, swid_enc,
                     api_key_enc, team_name_filter),
                )
    finally:
        conn.close()


def get_league_settings(user_id: int):
    """Return the league settings row dict for the given user, or None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM league_settings WHERE user_id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
