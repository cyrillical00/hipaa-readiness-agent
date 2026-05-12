"""Authentication and RBAC facade for the HIPAA Readiness Agent."""
import json
import os
from pathlib import Path

try:
    import streamlit as st
except Exception:
    st = None

_ROLES_PATH = Path(__file__).resolve().parent / "roles.json"
_ROLES_CACHE = {"mtime": 0.0, "data": None}
_VALID_ROLES = ("admin", "editor", "contributor", "viewer")
_FALLBACK_ALLOWED = ["cyrillical@gmail.com", "demo@hipaa.example"]


def _load_roles():
    """Load roles.json with mtime based caching. Never raises."""
    try:
        mtime = _ROLES_PATH.stat().st_mtime
    except Exception:
        return {"default_role": "viewer", "users": {}}

    if _ROLES_CACHE["data"] is not None and _ROLES_CACHE["mtime"] == mtime:
        return _ROLES_CACHE["data"]

    try:
        with open(_ROLES_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            data = {"default_role": "viewer", "users": {}}
        data.setdefault("default_role", "viewer")
        data.setdefault("users", {})
    except Exception:
        data = {"default_role": "viewer", "users": {}}

    _ROLES_CACHE["mtime"] = mtime
    _ROLES_CACHE["data"] = data
    return data


def get_auth_mode() -> str:
    """Returns 'cloud' if st.experimental_user is populated, else 'local'."""
    if st is None:
        return "local"
    try:
        user = getattr(st, "experimental_user", None)
        if user is None:
            return "local"
        email = getattr(user, "email", None)
        if email and isinstance(email, str) and "@" in email:
            return "cloud"
    except Exception:
        return "local"
    return "local"


def get_current_user_or_none():
    """Logged in user's email, or None if not logged in or outside Streamlit."""
    if st is None:
        return None
    try:
        user = getattr(st, "experimental_user", None)
        if user is not None:
            email = getattr(user, "email", None)
            if email and isinstance(email, str) and "@" in email:
                return email
    except Exception:
        pass
    try:
        local_email = st.session_state.get("local_login_email")
        if local_email and isinstance(local_email, str) and "@" in local_email:
            return local_email
    except Exception:
        return None
    return None


def get_role(email: str) -> str:
    """Returns role string for an email; default_role if unknown."""
    data = _load_roles()
    default_role = data.get("default_role", "viewer")
    if not email or not isinstance(email, str):
        return default_role
    role = data.get("users", {}).get(email, default_role)
    if role not in _VALID_ROLES:
        return default_role
    return role


def is_admin(email: str) -> bool:
    """True if the email maps to the admin role."""
    return get_role(email) == "admin"


def _get_allowed_emails():
    """Read allow list from secrets, falling back to a built in list."""
    if st is None:
        return list(_FALLBACK_ALLOWED), True
    try:
        raw = st.secrets.get("local_allowed_emails", None)
        if raw and isinstance(raw, (list, tuple)) and all(isinstance(x, str) for x in raw):
            return list(raw), False
    except Exception:
        pass
    return list(_FALLBACK_ALLOWED), True


def render_login_gate() -> None:
    """Render the login UI. Cloud mode prompts for Google. Local mode shows allow list."""
    if st is None:
        return

    mode = get_auth_mode()

    st.markdown("# HIPAA Readiness Agent")
    st.caption("Sign in to continue.")

    if mode == "cloud":
        st.info("Click below to sign in with your Google account.")
        try:
            st.login()
        except Exception:
            st.button("Sign in with Google", type="primary", disabled=True)
            st.caption("Streamlit will redirect you to the Google login page.")
        return

    allowed, used_fallback = _get_allowed_emails()
    if used_fallback:
        st.warning(
            "No local_allowed_emails secret configured. Using a built in fallback list. "
            "Add local_allowed_emails to .streamlit/secrets.toml for production."
        )

    options = [""] + allowed
    choice = st.selectbox(
        "Select an allow listed email",
        options,
        index=0,
        key="local_login_selector",
    )
    if choice:
        st.session_state["local_login_email"] = choice
        st.rerun()


def require_login() -> str:
    """Return current user email or render the login gate and stop the page."""
    email = get_current_user_or_none()
    if email:
        return email
    if st is not None:
        render_login_gate()
        try:
            st.stop()
        except Exception:
            pass
    return ""
