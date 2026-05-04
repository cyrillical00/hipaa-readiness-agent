"""JSONL storage primitive with local mode and GitHub mode (stub)."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

try:
    import streamlit as st
    _HAS_ST = True
except Exception:
    st = None
    _HAS_ST = False

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_STATE_ROOT = _PROJECT_ROOT / ".streamlit" / "state"


def _secret_or_env(key: str) -> str:
    val = ""
    if _HAS_ST:
        try:
            val = st.secrets.get(key, "")
        except Exception:
            val = ""
    if not val:
        val = os.environ.get(key, "")
    return val or ""


def get_storage_mode() -> str:
    """Return 'github' if both repo and PAT env vars are set, else 'local'."""
    repo = _secret_or_env("HIPAA_STATE_REPO")
    pat = _secret_or_env("HIPAA_STATE_PAT")
    if repo and pat:
        return "github"
    return "local"


def _email_to_dir(email: str) -> str:
    """Sanitize an email into a safe directory name."""
    cleaned = (email or "").strip().lower()
    return cleaned.replace("@", "_at_").replace(".", "_dot_")


def get_user_state_dir(user_email: str) -> Path:
    """Return the local Path for this user's state dir; create if missing."""
    safe = _email_to_dir(user_email)
    user_dir = _STATE_ROOT / safe
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def _file_path(user_email: str, name: str) -> Path:
    return get_user_state_dir(user_email) / f"{name}.jsonl"


def list_records(user_email: str, name: str) -> list[dict]:
    """Read all JSONL records for a user. Returns [] if file does not exist."""
    if get_storage_mode() == "github":
        # TODO Phase 6.5 follow-up: implement GitHub Contents API read.
        print("[storage] github mode requested but not implemented; using local fallback")
    path = _file_path(user_email, name)
    if not path.exists():
        return []
    out: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def append_record(user_email: str, name: str, record: dict) -> None:
    """Append one record to the JSONL file. Adds _ts (ISO 8601 UTC) if absent."""
    if get_storage_mode() == "github":
        # TODO Phase 6.5 follow-up: implement GitHub Contents API append.
        print("[storage] github mode requested but not implemented; using local fallback")
    payload = dict(record or {})
    if "_ts" not in payload:
        payload["_ts"] = datetime.now(timezone.utc).isoformat()
    path = _file_path(user_email, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")


def list_users() -> list[str]:
    """Return sanitized directory names for users with at least one state file."""
    if not _STATE_ROOT.exists():
        return []
    out: list[str] = []
    for child in _STATE_ROOT.iterdir():
        if child.is_dir() and any(child.glob("*.jsonl")):
            out.append(child.name)
    return sorted(out)
