# utils/auth.py
# Unstructured Alpha — Account Creation + Login
#
# Simple email + password auth, built directly into this app's own
# database (no third-party auth provider) -- per explicit user choice.
# Passwords are hashed with bcrypt (a salted, slow hash designed for
# password storage, not a fast general-purpose hash like SHA-256) and the
# plaintext password is never stored or logged anywhere.
#
# Known limitation, stated plainly: there is no "remember me" / persistent
# session across browser restarts in this version. Streamlit has no
# built-in cookie API, so a logged-in session lives only in
# st.session_state, which is cleared when the browser tab/session ends --
# every new visit requires logging in again. A real "stay logged in"
# experience would need a signed session cookie (e.g. via the community
# `streamlit-cookies-manager` package) layered on top of this, which is a
# reasonable fast-follow but adds a real new dependency and its own
# security surface (cookie signing key management), so it's deliberately
# not bundled into this first pass.
#
# Also stated plainly: this module does not implement password reset,
# email verification, or rate-limiting on login attempts. Those are real
# gaps for a production auth system and the most obvious next hardening
# steps if this app gets real outside users.

import re
from datetime import datetime, timezone

import bcrypt
from sqlalchemy import select

from utils import db
from utils.db import users

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AuthError(Exception):
    """Raised for user-facing auth failures (bad email, duplicate account, wrong password)."""


def _validate_email(email: str) -> str:
    email = email.strip().lower()
    if not _EMAIL_RE.match(email):
        raise AuthError("That doesn't look like a valid email address.")
    return email


def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise AuthError("Password must be at least 8 characters.")


def signup(email: str, password: str) -> dict:
    """Create a new account. Raises AuthError if the email is invalid or already registered."""
    email = _validate_email(email)
    _validate_password(password)

    with db.engine.begin() as conn:
        existing = conn.execute(select(users.c.id).where(users.c.email == email)).first()
        if existing:
            raise AuthError("An account with that email already exists. Try logging in instead.")

        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        result = conn.execute(
            users.insert().values(email=email, password_hash=password_hash, created_at=_now_iso())
        )
        user_id = result.inserted_primary_key[0]

    return {"id": user_id, "email": email}


def login(email: str, password: str) -> dict:
    """Verify credentials. Raises AuthError if the email isn't registered or the password is wrong."""
    email = _validate_email(email)

    with db.engine.begin() as conn:
        row = conn.execute(select(users).where(users.c.email == email)).mappings().first()

    if row is None:
        raise AuthError("No account found with that email.")

    if not bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8")):
        raise AuthError("Incorrect password.")

    return {"id": row["id"], "email": row["email"]}
