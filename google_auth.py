"""Load existing Google OAuth credentials from a private folder.

Never opens a browser, never copies files, never logs secret values.
"""
import glob
import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

DEFAULT_PRIVATE_DIR = r"C:\Users\Guy\.gemini\antigravity\scratch\gmail-calendar-agent"
DEFAULT_CLIENT_DIR = r"C:\Users\Guy\Downloads"

_creds: Credentials | None = None


class AuthError(RuntimeError):
    """Raised when credentials are missing or cannot be refreshed."""


def _private_dir() -> Path:
    return Path(os.environ.get("GOOGLE_PRIVATE_DIR", DEFAULT_PRIVATE_DIR))


def _find_client_secret() -> Path | None:
    """Look for client_secret*.json in the private dir, then the fallback dir."""
    fallback = os.environ.get("GOOGLE_CLIENT_SECRET_DIR", DEFAULT_CLIENT_DIR)
    for folder in (_private_dir(), Path(fallback)):
        matches = sorted(glob.glob(str(folder / "client_secret*.json")))
        if matches:
            return Path(matches[-1])
    return None


def _load_token_info() -> dict:
    token_path = _private_dir() / "token.json"
    if not token_path.is_file():
        raise AuthError(
            f"token.json not found in {token_path.parent}. "
            "Set GOOGLE_PRIVATE_DIR or re-authorize outside this server."
        )
    info = json.loads(token_path.read_text(encoding="utf-8"))
    if not (info.get("client_id") and info.get("client_secret")):
        secret_path = _find_client_secret()
        if secret_path is None:
            raise AuthError("token.json lacks client info and no client_secret*.json was found.")
        raw = json.loads(secret_path.read_text(encoding="utf-8"))
        client = raw.get("installed") or raw.get("web") or {}
        info.setdefault("client_id", client.get("client_id"))
        info.setdefault("client_secret", client.get("client_secret"))
    return info


def get_credentials() -> Credentials:
    """Return valid credentials, refreshing silently (in memory) if needed."""
    global _creds
    if _creds is None:
        _creds = Credentials.from_authorized_user_info(_load_token_info())
    if not _creds.valid:
        if not _creds.refresh_token:
            raise AuthError("Token expired and has no refresh token. Re-authorize outside this server.")
        try:
            _creds.refresh(Request())
        except Exception as exc:  # do not leak token details
            raise AuthError(f"Could not refresh Google token ({type(exc).__name__}). "
                            "Re-authorize outside this server.") from None
    return _creds


def gmail_service():
    return build("gmail", "v1", credentials=get_credentials(), cache_discovery=False)


def calendar_service():
    return build("calendar", "v3", credentials=get_credentials(), cache_discovery=False)
