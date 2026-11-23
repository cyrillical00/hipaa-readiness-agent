"""Authentication and RBAC facade for the HIPAA Readiness Agent.

Identity comes only from the identity provider behind Streamlit (st.login /
st.user). Nothing a visitor types or selects in the page can establish who
they are, and a session without a verified identity is stopped at the gate.
"""
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

# Local development only: see _dev_login_email().
_DEV_LOGIN_ENV = "HIPAA_DEV_LOGIN_EMAIL"
_LOOPBACK_ADDRESSES = {"localhost", "127.0.0.1", "::1"}


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


def _is_email(value) -> bool:
    return isinstance(value, str) and "@" in value


def _claim(user, name, default=None):
    """Read one attribute of st.user. Never raises."""
    try:
        return getattr(user, name)
    except Exception:
        return default


def _verified_email():
    """Email of a user who completed the identity provider's sign-in, or None.

    Only a session that Streamlit marks as logged in through st.login counts.
    An address reported without that flag (older Streamlit releases filled one
    in from a request header, or with a fixed placeholder) is not an identity.
    """
    if st is None:
        return None
    user = getattr(st, "user", None)
    if user is None:
        # Name used by the first Streamlit releases that had st.login.
        user = getattr(st, "experimental_user", None)
    if user is None:
        return None

    if _claim(user, "is_logged_in") is not True:
        return None
    email = _claim(user, "email")
    if not _is_email(email):
        return None
    # Providers that report whether the address was verified must say yes.
    if _claim(user, "email_verified", True) is False:
        return None
    return email


def _server_is_loopback_only() -> bool:
    """True only when Streamlit is bound to this machine's loopback interface."""
    try:
        address = st.get_option("server.address")
    except Exception:
        return False
    return isinstance(address, str) and address.strip().lower() in _LOOPBACK_ADDRESSES


def _dev_login_email():
    """Developer identity for a server that only this machine can reach, or None.

    Needs both HIPAA_DEV_LOGIN_EMAIL and a loopback-only server
    (`streamlit run app.py --server.address localhost`). A deployed app listens
    on a routable address, so setting the variable there changes nothing.
    """
    if st is None:
        return None
    email = os.environ.get(_DEV_LOGIN_ENV, "").strip()
    if not _is_email(email):
        return None
    if not _server_is_loopback_only():
        return None
    return email


def _allowed_emails():
    """Lower-cased allow list from the `allowed_emails` secret.

    Returns None when the secret is absent (any signed-in account is admitted,
    with the default role). A secret that is present but unusable admits nobody.
    """
    try:
        raw = st.secrets.get("allowed_emails", None)
    except Exception:
        return None
    if raw is None:
        return None
    if isinstance(raw, str):
        raw = [raw]
    try:
        return {x.strip().lower() for x in raw if isinstance(x, str) and x.strip()}
    except Exception:
        return set()


def get_auth_mode() -> str:
    """Returns 'cloud' when an identity provider vouches for the user, else 'local'."""
    return "cloud" if _verified_email() else "local"


def get_current_user_or_none():
    """Signed-in user's email, or None if nobody is signed in or they are not allowed."""
    if st is None:
        return None
    email = _verified_email()
    if email is not None:
        allowed = _allowed_emails()
        if allowed is not None and email.strip().lower() not in allowed:
            return None
        return email
    return _dev_login_email()


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


def render_login_gate() -> None:
    """Explain why access was refused and offer the identity provider's sign-in."""
    if st is None:
        return

    st.markdown("# HIPAA Readiness Agent")

    if _verified_email() is not None:
        # Signed in, but not on the allow list.
        st.error("Your account is not authorised to use this deployment.")
        logout = getattr(st, "logout", None)
        if logout is not None and st.button("Sign out", key="gate_logout_btn"):
            try:
                logout()
            except Exception:
                pass
        return

    st.caption("Sign in to continue.")

    if os.environ.get(_DEV_LOGIN_ENV, "").strip() and not _server_is_loopback_only():
        st.warning(
            f"{_DEV_LOGIN_ENV} is set but ignored: the developer login only works when "
            "the server is bound to this machine "
            "(`streamlit run app.py --server.address localhost`)."
        )

    login = getattr(st, "login", None)
    if login is None:
        st.error(
            "This Streamlit version has no sign-in support. Install the pinned "
            "requirements and configure an [auth] section in .streamlit/secrets.toml."
        )
        return

    if st.button("Sign in", type="primary", key="gate_login_btn"):
        try:
            login()
        except Exception:
            st.error(
                "Sign-in is not configured for this deployment. Add an [auth] section "
                "to .streamlit/secrets.toml (see the README) and restart the app."
            )


def require_login() -> str:
    """Return the current user's email, or render the login gate and stop the page.

    Never returns without a user: if the page cannot be stopped, it raises.
    """
    email = get_current_user_or_none()
    if email:
        return email
    if st is not None:
        render_login_gate()
        st.stop()
    raise PermissionError("No verified user identity; refusing to continue.")
