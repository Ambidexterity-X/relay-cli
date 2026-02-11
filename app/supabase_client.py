"""
Supabase client initialization for relay CLI.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

from app.session import load_session


def get_client() -> Client:
    """
    Loads SUPABASE_URL and SUPABASE_KEY from .env.
    Creates a Supabase client.
    If a session exists in .env, sets the session on the client using
    supabase.auth.set_session(access_token, refresh_token).
    Returns the client.
    """
    # Load environment variables from .env
    dotenv_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path)
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_KEY must be set in .env file. "
            "Please create a .env file with your Supabase credentials."
        )
    
    # Create the client
    client = create_client(url, key)
    
    # If a session exists, set it on the client
    session = load_session()
    if session.get("access_token") and session.get("refresh_token"):
        try:
            client.auth.set_session(
                session["access_token"],
                session["refresh_token"]
            )
        except Exception:
            # Session might be expired or invalid, continue without it
            pass
    
    return client
