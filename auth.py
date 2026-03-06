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

import database

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
    if not value:
        return ""
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
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


# ── User auth ──────────────────────────────────────────────────────────────

def register_user(username: str, password: str):
    """Validate and create a new user. Returns (success, message)."""
    username = username.strip()
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    ok, err = database.create_user(username, hash_password(password))
    return (True, "Account created! You can now log in.") if ok else (False, err)


def login_user(username: str, password: str):
    """Authenticate a user. Returns (success, user_id | None, message)."""
    username = username.strip()
    user = database.get_user_by_username(username)
    if not user or not verify_password(password, user["password_hash"]):
        return False, None, "Invalid username or password."
    return True, user["id"], f"Welcome back, {username}!"


# ── Profile CRUD ───────────────────────────────────────────────────────────

def _decrypt_profile(row: dict) -> dict:
    return {
        "id":               row["id"],
        "name":             row["name"],
        "league_id":        row.get("league_id") or "",
        "season_year":      row.get("season_year") or 2025,
        "espn_s2":          decrypt(row.get("espn_s2") or ""),
        "swid":             decrypt(row.get("swid") or ""),
        "api_key":          decrypt(row.get("anthropic_api_key") or ""),
        "team_name_filter": row.get("team_name_filter") or "",
        "league_context":   row.get("league_context") or "",
        # Email settings
        "email_to":         row.get("email_to") or "",
        "smtp_from":        row.get("smtp_from") or "",
        "smtp_password":    decrypt(row.get("smtp_password") or ""),
        "smtp_host":        row.get("smtp_host") or "smtp.gmail.com",
        "smtp_port":        row.get("smtp_port") or 587,
        "email_schedule":   row.get("email_schedule") or "manual",
        "last_email_sent":  row.get("last_email_sent") or "",
    }


def list_profiles(user_id: int) -> list[dict]:
    """Return all decrypted profiles for a user."""
    return [_decrypt_profile(r) for r in database.get_all_profiles(user_id)]


def create_profile(
    user_id: int,
    name: str,
    league_id: str,
    season_year: int,
    espn_s2: str,
    swid: str,
    api_key: str,
    team_name_filter: str,
    league_context: str = "",
) -> int:
    """Encrypt sensitive fields and create a new profile. Returns the new profile id."""
    return database.create_profile(
        user_id, name, league_id, season_year,
        encrypt(espn_s2), encrypt(swid), encrypt(api_key),
        team_name_filter, league_context,
    )


def update_profile(
    profile_id: int,
    user_id: int,
    name: str,
    league_id: str,
    season_year: int,
    espn_s2: str,
    swid: str,
    api_key: str,
    team_name_filter: str,
    league_context: str = "",
) -> None:
    """Encrypt sensitive fields and update an existing profile."""
    database.update_profile(
        profile_id, user_id, name, league_id, season_year,
        encrypt(espn_s2), encrypt(swid), encrypt(api_key),
        team_name_filter, league_context,
    )


def save_league_context(profile_id: int, user_id: int, league_context: str) -> None:
    """Quick-save just the league context notes without touching other fields."""
    database.save_league_context(profile_id, user_id, league_context)


def save_email_config(
    profile_id: int,
    user_id: int,
    email_to: str,
    smtp_from: str,
    smtp_password: str,
    smtp_host: str,
    smtp_port: int,
    email_schedule: str,
) -> None:
    """Encrypt SMTP password and persist email settings."""
    database.save_email_config(
        profile_id, user_id,
        email_to, smtp_from, encrypt(smtp_password),
        smtp_host, smtp_port, email_schedule,
    )


def update_last_email_sent(profile_id: int, user_id: int) -> None:
    database.update_last_email_sent(profile_id, user_id)


def delete_profile(profile_id: int, user_id: int) -> None:
    database.delete_profile(profile_id, user_id)
