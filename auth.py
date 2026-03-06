"""
auth.py — User authentication and secrets encryption.

Passwords are hashed with bcrypt.
Sensitive league settings (ESPN cookies, Anthropic API key) are encrypted
with Fernet symmetric encryption using a key that is generated once and stored
in .app_secret.key (excluded from git).
"""

import os

import bcrypt
from cryptography.fernet import Fernet

from database import (
    create_user,
    get_user_by_username,
    get_league_settings,
    upsert_league_settings,
)

_KEY_FILE = os.path.join(os.path.dirname(__file__), ".app_secret.key")
_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is not None:
        return _fernet
    if os.path.exists(_KEY_FILE):
        with open(_KEY_FILE, "rb") as f:
            key = f.read().strip()
    else:
        key = Fernet.generate_key()
        with open(_KEY_FILE, "wb") as f:
            f.write(key)
    _fernet = Fernet(key)
    return _fernet


# ── Encryption helpers ─────────────────────────────────────────────────────

def encrypt(value: str) -> str:
    """Encrypt a string value for storage."""
    if not value:
        return ""
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    """Decrypt a Fernet-encrypted string. Returns '' on failure."""
    if not value:
        return ""
    try:
        return _get_fernet().decrypt(value.encode()).decode()
    except Exception:
        return ""


# ── Password helpers ───────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ── Public API ─────────────────────────────────────────────────────────────

def register_user(username: str, password: str):
    """
    Validate inputs and create a new user.
    Returns (success: bool, message: str).
    """
    username = username.strip()
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    ok, err = create_user(username, hash_password(password))
    if ok:
        return True, "Account created! You can now log in."
    return False, err


def login_user(username: str, password: str):
    """
    Authenticate a user.
    Returns (success: bool, user_id: int | None, message: str).
    """
    username = username.strip()
    user = get_user_by_username(username)
    if not user or not verify_password(password, user["password_hash"]):
        return False, None, "Invalid username or password."
    return True, user["id"], f"Welcome back, {username}!"


def save_settings(
    user_id: int,
    league_id: str,
    season_year: int,
    espn_s2: str,
    swid: str,
    api_key: str,
    team_name_filter: str,
) -> None:
    """Encrypt sensitive fields and persist league settings."""
    upsert_league_settings(
        user_id,
        league_id,
        season_year,
        encrypt(espn_s2),
        encrypt(swid),
        encrypt(api_key),
        team_name_filter,
    )


def load_settings(user_id: int) -> dict | None:
    """
    Load and decrypt saved league settings for a user.
    Returns a settings dict or None if no settings have been saved.
    """
    row = get_league_settings(user_id)
    if not row:
        return None
    return {
        "league_id":        row.get("league_id") or "",
        "season_year":      row.get("season_year") or 2025,
        "espn_s2":          decrypt(row.get("espn_s2") or ""),
        "swid":             decrypt(row.get("swid") or ""),
        "api_key":          decrypt(row.get("anthropic_api_key") or ""),
        "team_name_filter": row.get("team_name_filter") or "",
    }
