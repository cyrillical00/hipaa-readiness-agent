"""Evidence repository: stores per-control files and URL references for HIPAA controls."""
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from storage.github_jsonl import get_user_state_dir


_MAX_FILE_BYTES = 10 * 1024 * 1024
_MAX_FILENAME_LEN = 200
_ALLOWED_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "application/pdf",
    "text/plain",
    "text/csv",
}
_FILENAME_SAFE_RE = re.compile(r"[^a-zA-Z0-9._-]")
_INDEX_NAME = "evidence_index.jsonl"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _evidence_root(user_email: str) -> Path:
    base = get_user_state_dir(user_email) / "evidence"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _index_path(user_email: str) -> Path:
    return get_user_state_dir(user_email) / _INDEX_NAME


def _sanitize_filename(filename: str) -> str:
    if not filename or not isinstance(filename, str):
        raise ValueError("Filename is required")
    base = Path(filename).name
    if not base:
        raise ValueError("Filename is empty after stripping path components")
    cleaned = _FILENAME_SAFE_RE.sub("_", base)
    if len(cleaned) > _MAX_FILENAME_LEN:
        raise ValueError(f"Filename exceeds {_MAX_FILENAME_LEN} characters")
    return cleaned


def _append_index(user_email: str, entry: dict) -> None:
    path = _index_path(user_email)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as err:
        raise ValueError(f"Could not write evidence: {err}")


def _read_index(user_email: str) -> list[dict]:
    path = _index_path(user_email)
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


def _rewrite_index(user_email: str, entries: list[dict]) -> None:
    path = _index_path(user_email)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("w", encoding="utf-8") as fh:
            for entry in entries:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as err:
        raise ValueError(f"Could not write evidence: {err}")


def upload_file(
    user_email: str,
    control_id: str,
    filename: str,
    file_bytes: bytes,
    caption: str = "",
    content_type: str = "",
) -> dict:
    """Save bytes under .streamlit/state/{email}/evidence/{control_id}/{filename} and append index entry."""
    if not control_id or not isinstance(control_id, str):
        raise ValueError("control_id is required")
    if not isinstance(file_bytes, (bytes, bytearray)):
        raise ValueError("file_bytes must be bytes")
    size = len(file_bytes)
    if size == 0:
        raise ValueError("File is empty")
    if size > _MAX_FILE_BYTES:
        raise ValueError(f"File exceeds 10 MB limit ({size} bytes)")
    ctype = (content_type or "").strip().lower()
    if ctype not in _ALLOWED_CONTENT_TYPES:
        allowed = ", ".join(sorted(_ALLOWED_CONTENT_TYPES))
        raise ValueError(f"Content type not allowed: '{content_type}'. Allowed: {allowed}")

    safe_name = _sanitize_filename(filename)
    ctrl_dir = _evidence_root(user_email) / control_id
    try:
        ctrl_dir.mkdir(parents=True, exist_ok=True)
    except OSError as err:
        raise ValueError(f"Could not write evidence: {err}")

    target = ctrl_dir / safe_name
    if target.exists():
        stem = target.stem
        suffix = target.suffix
        target = ctrl_dir / f"{stem}_{uuid.uuid4().hex[:8]}{suffix}"
        safe_name = target.name

    try:
        with target.open("wb") as fh:
            fh.write(bytes(file_bytes))
    except OSError as err:
        raise ValueError(f"Could not write evidence: {err}")

    entry = {
        "evidence_id": uuid.uuid4().hex,
        "control_id": control_id,
        "filename": safe_name,
        "caption": caption or "",
        "kind": "file",
        "size_bytes": size,
        "content_type": ctype,
        "_ts": _now_iso(),
    }
    _append_index(user_email, entry)
    return entry


def add_url(user_email: str, control_id: str, url: str, caption: str = "") -> dict:
    """Append index entry for a URL reference (no file write)."""
    if not control_id or not isinstance(control_id, str):
        raise ValueError("control_id is required")
    if not url or not isinstance(url, str):
        raise ValueError("URL is required")
    url_clean = url.strip()
    if not (url_clean.startswith("http://") or url_clean.startswith("https://")):
        raise ValueError("URL must start with http:// or https://")

    entry = {
        "evidence_id": uuid.uuid4().hex,
        "control_id": control_id,
        "filename": url_clean,
        "url": url_clean,
        "caption": caption or "",
        "kind": "url",
        "size_bytes": 0,
        "content_type": "",
        "_ts": _now_iso(),
    }
    _append_index(user_email, entry)
    return entry


def list_evidence(user_email: str, control_id: str | None = None) -> list[dict]:
    """All index entries for the user, optionally filtered to one control_id."""
    entries = _read_index(user_email)
    if control_id is None:
        return entries
    return [e for e in entries if e.get("control_id") == control_id]


def get_evidence_bytes(user_email: str, evidence_id: str) -> tuple[bytes, str, str] | None:
    """Returns (bytes, filename, content_type) for download. None if URL kind or not found."""
    entries = _read_index(user_email)
    match = next((e for e in entries if e.get("evidence_id") == evidence_id), None)
    if not match:
        return None
    if match.get("kind") != "file":
        return None
    fname = match.get("filename", "")
    ctype = match.get("content_type", "")
    ctrl_id = match.get("control_id", "")
    target = _evidence_root(user_email) / ctrl_id / fname
    if not target.exists():
        return None
    try:
        with target.open("rb") as fh:
            data = fh.read()
    except OSError:
        return None
    return data, fname, ctype


def delete_evidence(user_email: str, evidence_id: str) -> bool:
    """Remove file (if file kind) and remove index entry. Returns True on success."""
    entries = _read_index(user_email)
    match = next((e for e in entries if e.get("evidence_id") == evidence_id), None)
    if not match:
        return False
    if match.get("kind") == "file":
        ctrl_id = match.get("control_id", "")
        fname = match.get("filename", "")
        target = _evidence_root(user_email) / ctrl_id / fname
        if target.exists():
            try:
                target.unlink()
            except OSError:
                return False
    remaining = [e for e in entries if e.get("evidence_id") != evidence_id]
    _rewrite_index(user_email, remaining)
    return True


def evidence_count_by_control(user_email: str) -> dict[str, int]:
    """Returns {control_id: count}. Used by the scorer to flip the evidence boolean."""
    counts: dict[str, int] = {}
    for e in _read_index(user_email):
        cid = e.get("control_id", "")
        if not cid:
            continue
        counts[cid] = counts.get(cid, 0) + 1
    return counts
