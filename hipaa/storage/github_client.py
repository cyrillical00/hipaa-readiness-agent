"""Thin GitHub Contents API client used by github_jsonl when github mode is on.

Backs the optional shared-persistence mode: a private GitHub repo holds each
user's JSONL files so state survives Streamlit Cloud restarts. Keep this module
narrow and dependency-light; the only third-party import is ``requests``.

API reference:
https://docs.github.com/en/rest/repos/contents
"""
from __future__ import annotations

import base64
import time
from typing import Optional, Tuple
from urllib.parse import quote

import requests

_API_ROOT = "https://api.github.com"
_TIMEOUT = 10  # seconds; reads and writes both small


class GithubStateError(RuntimeError):
    """Raised on non-recoverable GitHub API failures (auth, rate limit, 5xx)."""


def _headers(pat: str) -> dict:
    """Standard GitHub REST API headers with bearer auth."""
    return {
        "Authorization": f"Bearer {pat}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "hipaa-readiness-agent",
    }


def _encode_path(path: str) -> str:
    """URL-encode each segment of a path but keep ``/`` separators intact."""
    parts = [quote(p, safe="") for p in path.split("/") if p]
    return "/".join(parts)


def _content_url(repo: str, path: str) -> str:
    """Build the contents URL. Empty path resolves to the repo root listing."""
    encoded = _encode_path(path)
    if not encoded:
        return f"{_API_ROOT}/repos/{repo}/contents"
    return f"{_API_ROOT}/repos/{repo}/contents/{encoded}"


def get_file(repo: str, path: str, pat: str) -> Tuple[Optional[str], Optional[str]]:
    """Fetch a file's decoded text and its blob sha.

    Returns ``(content, sha)`` on success, or ``(None, None)`` if the file does
    not exist (HTTP 404). Raises ``GithubStateError`` on any other failure.
    """
    resp = requests.get(_content_url(repo, path), headers=_headers(pat), timeout=_TIMEOUT)
    if resp.status_code == 404:
        return None, None
    if resp.status_code != 200:
        raise GithubStateError(
            f"GET contents failed: {resp.status_code} {resp.text[:200]}"
        )
    payload = resp.json()
    # When path is a directory GitHub returns a list; callers should use list_dir.
    if isinstance(payload, list):
        raise GithubStateError(f"path {path!r} is a directory, not a file")
    encoded = payload.get("content", "") or ""
    # GitHub returns base64 with embedded newlines; b64decode tolerates them.
    try:
        text = base64.b64decode(encoded).decode("utf-8")
    except Exception as e:
        raise GithubStateError(f"failed to decode {path!r}: {e}") from e
    return text, payload.get("sha")


def put_file(
    repo: str,
    path: str,
    content: str,
    sha: Optional[str],
    pat: str,
    message: str,
) -> str:
    """Create or update a file. Returns the new blob sha.

    Pass ``sha=None`` to create a new file; pass the prior sha to update.
    On a 409 conflict (concurrent writer), refetch sha once and retry.
    Raises ``GithubStateError`` on persistent failure.
    """
    body = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
    }
    if sha:
        body["sha"] = sha

    resp = requests.put(
        _content_url(repo, path), headers=_headers(pat), json=body, timeout=_TIMEOUT
    )
    if resp.status_code == 409:
        # Lost race; refetch sha and retry once.
        _, fresh_sha = get_file(repo, path, pat)
        body["sha"] = fresh_sha or ""
        # Brief backoff to let any in-flight conflicting write settle.
        time.sleep(0.5)
        resp = requests.put(
            _content_url(repo, path), headers=_headers(pat), json=body, timeout=_TIMEOUT
        )
    if resp.status_code not in (200, 201):
        raise GithubStateError(
            f"PUT contents failed: {resp.status_code} {resp.text[:200]}"
        )
    return resp.json().get("content", {}).get("sha", "")


def list_dir(repo: str, path: str, pat: str) -> list[str]:
    """List immediate child names of a directory. Empty list on 404."""
    resp = requests.get(_content_url(repo, path), headers=_headers(pat), timeout=_TIMEOUT)
    if resp.status_code == 404:
        return []
    if resp.status_code != 200:
        raise GithubStateError(
            f"GET dir failed: {resp.status_code} {resp.text[:200]}"
        )
    payload = resp.json()
    if not isinstance(payload, list):
        # The path resolved to a file rather than a directory.
        return []
    return [item["name"] for item in payload if "name" in item]
