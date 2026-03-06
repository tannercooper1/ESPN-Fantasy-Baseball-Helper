"""
database.py — SQLite persistence layer for user accounts and league profiles.
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
    """Create tables if they don't exist and run any pending migrations."""
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
            CREATE TABLE IF NOT EXISTS profiles (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id            INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name               TEXT NOT NULL,
                league_id          TEXT,
                season_year        INTEGER,
                espn_s2            TEXT,
                swid               TEXT,
                anthropic_api_key  TEXT,
                team_name_filter   TEXT,
                created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Migrate old league_settings table if it exists
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        if "league_settings" in tables:
            conn.execute("""
                INSERT INTO profiles
                    (user_id, name, league_id, season_year, espn_s2, swid,
                     anthropic_api_key, team_name_filter, created_at, updated_at)
                SELECT user_id, 'My League', league_id, season_year, espn_s2, swid,
                       anthropic_api_key, team_name_filter,
                       updated_at, updated_at
                FROM league_settings
            """)
            conn.execute("DROP TABLE league_settings")
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


# ── Profiles ───────────────────────────────────────────────────────────────

def get_all_profiles(user_id: int) -> list[dict]:
    """Return all profiles for a user, ordered by name."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM profiles WHERE user_id = ? ORDER BY name",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_profile(profile_id: int, user_id: int) -> dict | None:
    """Return a single profile row (must belong to user_id) or None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM profiles WHERE id = ? AND user_id = ?",
            (profile_id, user_id),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_profile(
    user_id: int,
    name: str,
    league_id: str,
    season_year: int,
    espn_s2_enc: str,
    swid_enc: str,
    api_key_enc: str,
    team_name_filter: str,
) -> int:
    """Insert a new profile and return its id."""
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(
                """
                INSERT INTO profiles
                    (user_id, name, league_id, season_year, espn_s2, swid,
                     anthropic_api_key, team_name_filter)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, name, league_id, season_year,
                 espn_s2_enc, swid_enc, api_key_enc, team_name_filter),
            )
        return cur.lastrowid
    finally:
        conn.close()


def update_profile(
    profile_id: int,
    user_id: int,
    name: str,
    league_id: str,
    season_year: int,
    espn_s2_enc: str,
    swid_enc: str,
    api_key_enc: str,
    team_name_filter: str,
) -> None:
    """Update an existing profile (must belong to user_id)."""
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """
                UPDATE profiles
                SET name = ?, league_id = ?, season_year = ?,
                    espn_s2 = ?, swid = ?, anthropic_api_key = ?,
                    team_name_filter = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
                """,
                (name, league_id, season_year, espn_s2_enc, swid_enc,
                 api_key_enc, team_name_filter, profile_id, user_id),
            )
    finally:
        conn.close()


def delete_profile(profile_id: int, user_id: int) -> None:
    """Delete a profile (must belong to user_id)."""
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "DELETE FROM profiles WHERE id = ? AND user_id = ?",
                (profile_id, user_id),
            )
    finally:
        conn.close()
