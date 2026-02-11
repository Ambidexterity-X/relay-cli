"""
Session management for relay CLI.
Handles reading and writing session tokens to .env file.
"""


from pathlib import Path
from dotenv import dotenv_values, set_key


def _get_dotenv_path() -> Path:
    """Get the path to the .env file."""
    # Look for .env in the project root (where pyproject.toml is)
    current = Path(__file__).resolve().parent.parent
    dotenv_path = current / ".env"
    return dotenv_path


def load_session() -> dict:
    """
    Reads .env and returns a dict with keys:
    access_token, refresh_token, user_id
    Returns empty strings for missing values.
    """
    dotenv_path = _get_dotenv_path()
    
    if not dotenv_path.exists():
        return {
            "access_token": "",
            "refresh_token": "",
            "user_id": ""
        }
    
    values = dotenv_values(dotenv_path)
    
    return {
        "access_token": values.get("SUPABASE_ACCESS_TOKEN", ""),
        "refresh_token": values.get("SUPABASE_REFRESH_TOKEN", ""),
        "user_id": values.get("SUPABASE_USER_ID", "")
    }


def save_session(access_token: str, refresh_token: str, user_id: str) -> None:
    """
    Writes session fields to .env using python-dotenv's set_key().
    Does not touch SUPABASE_URL or SUPABASE_KEY.
    """
    dotenv_path = str(_get_dotenv_path())
    
    set_key(dotenv_path, "SUPABASE_ACCESS_TOKEN", access_token)
    set_key(dotenv_path, "SUPABASE_REFRESH_TOKEN", refresh_token)
    set_key(dotenv_path, "SUPABASE_USER_ID", user_id)


def clear_session() -> None:
    """
    Clears access_token, refresh_token, user_id from .env by setting them to "".
    """
    dotenv_path = str(_get_dotenv_path())
    
    set_key(dotenv_path, "SUPABASE_ACCESS_TOKEN", "")
    set_key(dotenv_path, "SUPABASE_REFRESH_TOKEN", "")
    set_key(dotenv_path, "SUPABASE_USER_ID", "")


def is_logged_in() -> bool:
    """
    Returns True if access_token is present and non-empty in .env.
    """
    session = load_session()
    return bool(session.get("access_token"))
