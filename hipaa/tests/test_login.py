"""The login gate must fail closed: no verified identity, no access."""
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

HIPAA_ROOT = Path(__file__).resolve().parent.parent
if str(HIPAA_ROOT) not in sys.path:
    sys.path.insert(0, str(HIPAA_ROOT))

from auth import login  # noqa: E402


class _Stop(BaseException):
    """Stands in for Streamlit's stop signal."""


class _User:
    """st.user: attribute access raises AttributeError for claims that are absent."""

    def __init__(self, **claims):
        self._claims = claims

    def __getattr__(self, name):
        try:
            return self.__dict__["_claims"][name]
        except KeyError:
            raise AttributeError(name) from None


class _FakeStreamlit:
    def __init__(self, user=None, secrets=None, address=None, with_login=True, legacy=False):
        if user is not None:
            setattr(self, "experimental_user" if legacy else "user", user)
        self.secrets = secrets if secrets is not None else {}
        self._address = address
        self.session_state = {}
        self.rendered = []
        self.login_calls = 0
        self.clicked = set()
        if with_login:
            self.login = self._login

    def _login(self):
        self.login_calls += 1

    def get_option(self, name):
        assert name == "server.address"
        return self._address

    def markdown(self, text, **_):
        self.rendered.append(("markdown", text))

    def caption(self, text):
        self.rendered.append(("caption", text))

    def error(self, text):
        self.rendered.append(("error", text))

    def warning(self, text):
        self.rendered.append(("warning", text))

    def info(self, text):
        self.rendered.append(("info", text))

    def button(self, label, key=None, **_):
        self.rendered.append(("button", label))
        return key in self.clicked

    def selectbox(self, *args, **kwargs):  # the old gate used this
        raise AssertionError("the login gate must not offer a choice of identities")

    def stop(self):
        raise _Stop()


def _use(fake, env=None):
    """Patch the module's streamlit handle and the dev-login variable."""
    environ = {k: v for k, v in os.environ.items() if k != login._DEV_LOGIN_ENV}
    environ.update(env or {})
    return mock.patch.object(login, "st", fake), mock.patch.dict(os.environ, environ, clear=True)


class VerifiedIdentityTests(unittest.TestCase):
    def _user(self, fake, env=None):
        p1, p2 = _use(fake, env)
        with p1, p2:
            return login.get_current_user_or_none()

    def test_no_identity_provider_means_no_user(self):
        self.assertIsNone(self._user(_FakeStreamlit()))
        self.assertIsNone(self._user(_FakeStreamlit(user=_User())))

    def test_session_state_cannot_set_the_user(self):
        fake = _FakeStreamlit(user=_User())
        fake.session_state["local_login_email"] = "admin@example.org"
        self.assertIsNone(self._user(fake))

    def test_signed_in_user_is_returned(self):
        fake = _FakeStreamlit(user=_User(is_logged_in=True, email="Pat@Example.org", email_verified=True))
        self.assertEqual(self._user(fake), "Pat@Example.org")

    def test_configured_but_not_signed_in_is_refused(self):
        fake = _FakeStreamlit(user=_User(is_logged_in=False))
        self.assertIsNone(self._user(fake))
        fake = _FakeStreamlit(user=_User(is_logged_in=False, email="pat@example.org"))
        self.assertIsNone(self._user(fake))

    def test_unverified_address_is_refused(self):
        fake = _FakeStreamlit(user=_User(is_logged_in=True, email="pat@example.org", email_verified=False))
        self.assertIsNone(self._user(fake))

    def test_missing_or_malformed_email_is_refused(self):
        for email in (None, "", "not-an-email", 42):
            fake = _FakeStreamlit(user=_User(is_logged_in=True, email=email))
            self.assertIsNone(self._user(fake), email)

    def test_an_address_without_a_completed_sign_in_is_refused(self):
        # Older Streamlit: a header-derived or placeholder address, no sign-in flag.
        for email in ("pat@example.org", "test@example.com"):
            self.assertIsNone(self._user(_FakeStreamlit(user=_User(email=email), legacy=True)), email)
            self.assertIsNone(self._user(_FakeStreamlit(user=_User(email=email))), email)
        # A truthy string is not the boolean Streamlit sets after a sign-in.
        fake = _FakeStreamlit(user=_User(is_logged_in="true", email="pat@example.org"))
        self.assertIsNone(self._user(fake))

    def test_sign_in_under_the_older_attribute_name_is_accepted(self):
        fake = _FakeStreamlit(user=_User(is_logged_in=True, email="pat@example.org"), legacy=True)
        self.assertEqual(self._user(fake), "pat@example.org")

    def test_allow_list_restricts_signed_in_users(self):
        user = _User(is_logged_in=True, email="Pat@Example.org")
        self.assertEqual(
            self._user(_FakeStreamlit(user=user, secrets={"allowed_emails": ["pat@example.org"]})),
            "Pat@Example.org",
        )
        self.assertIsNone(self._user(_FakeStreamlit(user=user, secrets={"allowed_emails": ["lee@example.org"]})))
        self.assertIsNone(self._user(_FakeStreamlit(user=user, secrets={"allowed_emails": []})))
        self.assertIsNone(self._user(_FakeStreamlit(user=user, secrets={"allowed_emails": 7})))

    def test_old_allow_list_secret_grants_nothing(self):
        fake = _FakeStreamlit(user=_User(), secrets={"local_allowed_emails": ["pat@example.org"]})
        self.assertIsNone(self._user(fake))


class DevLoginTests(unittest.TestCase):
    ENV = {login._DEV_LOGIN_ENV: "dev@example.org"}

    def _user(self, fake, env=None):
        p1, p2 = _use(fake, env)
        with p1, p2:
            return login.get_current_user_or_none()

    def test_needs_the_variable_and_a_loopback_only_server(self):
        self.assertEqual(self._user(_FakeStreamlit(address="localhost"), self.ENV), "dev@example.org")
        self.assertEqual(self._user(_FakeStreamlit(address="127.0.0.1"), self.ENV), "dev@example.org")

    def test_ignored_when_the_server_is_reachable_from_elsewhere(self):
        for address in (None, "", "0.0.0.0", "10.0.0.5", "::"):
            self.assertIsNone(self._user(_FakeStreamlit(address=address), self.ENV), address)

    def test_loopback_alone_is_not_enough(self):
        self.assertIsNone(self._user(_FakeStreamlit(address="localhost")))
        self.assertIsNone(self._user(_FakeStreamlit(address="localhost"), {login._DEV_LOGIN_ENV: "nope"}))


class RequireLoginTests(unittest.TestCase):
    def test_anonymous_visitor_is_stopped_and_offered_only_a_sign_in(self):
        fake = _FakeStreamlit(user=_User())
        p1, p2 = _use(fake)
        with p1, p2, self.assertRaises(_Stop):
            login.require_login()
        self.assertIn(("button", "Sign in"), fake.rendered)
        self.assertEqual(fake.login_calls, 0)

    def test_sign_in_button_starts_the_provider_flow(self):
        fake = _FakeStreamlit(user=_User())
        fake.clicked.add("gate_login_btn")
        p1, p2 = _use(fake)
        with p1, p2, self.assertRaises(_Stop):
            login.require_login()
        self.assertEqual(fake.login_calls, 1)

    def test_signed_in_but_not_allowed_is_stopped(self):
        fake = _FakeStreamlit(
            user=_User(is_logged_in=True, email="pat@example.org"),
            secrets={"allowed_emails": ["lee@example.org"]},
        )
        p1, p2 = _use(fake)
        with p1, p2, self.assertRaises(_Stop):
            login.require_login()
        self.assertTrue(any(kind == "error" for kind, _ in fake.rendered))

    def test_never_returns_without_a_user(self):
        class _NoStop(_FakeStreamlit):
            def stop(self):
                return None

        p1, p2 = _use(_NoStop(user=_User()))
        with p1, p2, self.assertRaises(PermissionError):
            login.require_login()

        p1, p2 = _use(None)
        with p1, p2, self.assertRaises(PermissionError):
            login.require_login()

    def test_signed_in_user_passes(self):
        fake = _FakeStreamlit(user=_User(is_logged_in=True, email="pat@example.org"))
        p1, p2 = _use(fake)
        with p1, p2:
            self.assertEqual(login.require_login(), "pat@example.org")
        self.assertEqual(fake.rendered, [])


class RealStreamlitGateTest(unittest.TestCase):
    """Run the real entry point under Streamlit's test harness with nobody signed in."""

    def test_app_stops_at_the_gate(self):
        try:
            from streamlit.testing.v1 import AppTest
        except Exception:  # pragma: no cover - older Streamlit
            self.skipTest("streamlit.testing is not available")

        environ = {k: v for k, v in os.environ.items() if k != login._DEV_LOGIN_ENV}
        with mock.patch.dict(os.environ, environ, clear=True):
            at = AppTest.from_file(str(HIPAA_ROOT / "app.py"), default_timeout=60)
            at.run()

        self.assertFalse(at.exception, [e.value for e in at.exception])
        self.assertEqual(len(at.selectbox), 0)
        self.assertEqual([b.label for b in at.button], ["Sign in"])
        self.assertEqual(len(at.sidebar), 0)
        self.assertNotIn("current_user", at.session_state)

    def test_dev_login_reaches_the_app_only_on_a_loopback_server(self):
        try:
            from streamlit import config
            from streamlit.testing.v1 import AppTest
        except Exception:  # pragma: no cover - older Streamlit
            self.skipTest("streamlit.testing is not available")

        environ = dict(os.environ)
        environ[login._DEV_LOGIN_ENV] = "dev@example.org"
        previous = config.get_option("server.address")
        try:
            with mock.patch.dict(os.environ, environ, clear=True):
                config.set_option("server.address", "0.0.0.0")
                refused = AppTest.from_file(str(HIPAA_ROOT / "app.py"), default_timeout=60)
                refused.run()

                config.set_option("server.address", "localhost")
                admitted = AppTest.from_file(str(HIPAA_ROOT / "app.py"), default_timeout=60)
                admitted.run()
        finally:
            config.set_option("server.address", previous)

        self.assertFalse(refused.exception, [e.value for e in refused.exception])
        self.assertNotIn("current_user", refused.session_state)
        self.assertEqual([b.label for b in refused.button], ["Sign in"])

        self.assertFalse(admitted.exception, [e.value for e in admitted.exception])
        self.assertEqual(admitted.session_state["current_user"], "dev@example.org")
        self.assertEqual(admitted.session_state["current_role"], "viewer")
        self.assertNotIn("Logout", [b.label for b in admitted.sidebar.button])


if __name__ == "__main__":
    unittest.main()
