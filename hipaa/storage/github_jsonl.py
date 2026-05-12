"""JSONL storage primitive with local mode and GitHub-backed mode.

Local mode (default): files under ``<project_root>/.streamlit/state/{email_safe}/{name}.jsonl``.
GitHub mode (when HIPAA_STATE_REPO and HIPAA_STATE_PAT are set): the same path
layout in a GitHub repo, accessed via the Contents API. See ``storage/README.md``.
"""
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

# Re-export GithubStateError so callers can catch storage errors without
# reaching into the lower-level client module.
from .github_client import (  # noqa: F401
    GithubStateError,
    get_file,
    list_dir,
    put_file,
)

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
    """Sanitize an email into a safe directory name.

    Raises ValueError on empty input so callers cannot accidentally write
    cross-user state to the repo or state root.
    """
    cleaned = (email or "").strip().lower()
    if not cleaned:
        raise ValueError("user_email is required")
    return cleaned.replace("@", "_at_").replace(".", "_dot_")


def get_user_state_dir(user_email: str) -> Path:
    """Return the local Path for this user's state dir; create if missing."""
    safe = _email_to_dir(user_email)
    user_dir = _STATE_ROOT / safe
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def _file_path(user_email: str, name: str) -> Path:
    return get_user_state_dir(user_email) / f"{name}.jsonl"


def _validate_name(name: str) -> None:
    """Reject record-file names that could escape the user dir."""
    if not name or "/" in name or "\\" in name or ".." in name:
        raise ValueError(f"unsafe record name: {name!r}")


def _github_path(user_email: str, name: str) -> str:
    """Build the github-mode path mirroring the local layout."""
    _validate_name(name)
    return f"{_email_to_dir(user_email)}/{name}.jsonl"


def _github_creds() -> tuple[str, str]:
    """Return (repo, pat) for github mode. Both are guaranteed non-empty here
    because get_storage_mode() returns 'github' only when both are set."""
    return _secret_or_env("HIPAA_STATE_REPO"), _secret_or_env("HIPAA_STATE_PAT")


def _parse_jsonl(text: str) -> list[dict]:
    """Parse JSONL text, skipping blank or malformed lines."""
    out: list[dict] = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def list_records(user_email: str, name: str) -> list[dict]:
    """Read all JSONL records for a user. Returns [] if file does not exist.

    Raises ``ValueError`` on unsafe inputs. Raises ``GithubStateError`` in
    github mode if the API call fails (auth, rate limit, 5xx). Local mode
    never raises beyond the input validation.
    """
    _validate_name(name)
    if get_storage_mode() == "github":
        repo, pat = _github_creds()
        text, _sha = get_file(repo, _github_path(user_email, name), pat)
        return _parse_jsonl(text) if text else []

    path = _file_path(user_email, name)
    if not path.exists():
        return []
    return _parse_jsonl(path.read_text(encoding="utf-8"))


def append_record(user_email: str, name: str, record: dict) -> None:
    """Append one record to the JSONL file. Adds _ts (ISO 8601 UTC) if absent.

    Raises ``ValueError`` on unsafe inputs (empty email, traversal in name).
    Raises ``GithubStateError`` in github mode on API failure.
    """
    _validate_name(name)
    payload = dict(record or {})
    if "_ts" not in payload:
        payload["_ts"] = datetime.now(timezone.utc).isoformat()
    new_line = json.dumps(payload, ensure_ascii=False) + "\n"

    if get_storage_mode() == "github":
        repo, pat = _github_creds()
        gh_path = _github_path(user_email, name)
        existing, sha = get_file(repo, gh_path, pat)
        new_content = (existing or "") + new_line
        message = f"append {name} for {_email_to_dir(user_email)}"
        put_file(repo, gh_path, new_content, sha, pat, message)
        return

    path = _file_path(user_email, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(new_line)


def list_users() -> list[str]:
    """Return sanitized directory names for users with at least one state file.

    In github mode, lists immediate children of the repo root and returns dirs
    only. In local mode, walks the on-disk state root.
    """
    if get_storage_mode() == "github":
        repo, pat = _github_creds()
        children = list_dir(repo, "", pat)
        # Sanitized user dirs replace dots with _dot_, so any name with a real
        # dot is a stray top-level file rather than a user directory.
        return sorted(c for c in children if "." not in c)

    if not _STATE_ROOT.exists():
        return []
    out: list[str] = []
    for child in _STATE_ROOT.iterdir():
        if child.is_dir() and any(child.glob("*.jsonl")):
            out.append(child.name)
    return sorted(out)
