# utils/auth.py
# Unstructured Alpha — Account Creation, Login, and Email Verification
#
# Simple email + password auth, built directly into this app's own
# database (no third-party auth provider) -- per explicit user choice.
# Passwords are hashed with bcrypt (a salted, slow hash designed for
# password storage, not a fast general-purpose hash like SHA-256) and the
# plaintext password is never stored or logged anywhere.
#
# Email verification (added 2026-06-21, per explicit user request): every
# new signup gets a 6-digit code emailed via Resend (utils/email.py) and
# must enter it before the account is usable. This is verify-ONCE-at-signup,
# not full 2FA on every login -- a second, narrower follow-up the user
# could ask for later if every-login codes are wanted instead. The code
# itself is hashed with SHA-256, not bcrypt: bcrypt's deliberate slowness
# protects long-lived password secrets against offline brute-forcing; a
# 6-digit OTP's real protection comes from its 15-minute expiry and the
# fact that guessing it requires an online attempt against this app (not
# an offline hash crack), so a fast hash is the right tool here, not a
# slow one applied out of habit.
#
# Known limitation, stated plainly: there is no "remember me" / persistent
# session across browser restarts in this version. Streamlit has no
# built-in cookie API, so a logged-in session lives only in
# st.session_state, which is cleared when the browser tab/session ends --
# every new visit requires logging in again. Also stated plainly: no
# password reset flow and no rate-limiting on login/code-verification
# attempts -- real gaps for a production system, the most obvious next
# hardening steps if this app gets real outside users.

import hashlib
import random
import re
from datetime import datetime, timedelta, timezone

import bcrypt
from sqlalchemy import select

from utils import db, email as email_module
from utils.db import users
from utils.email import EmailSendError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_CODE_VALID_MINUTES = 15


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AuthError(Exception):
    """Raised for user-facing auth failures (bad email, duplicate account, wrong password/code)."""


class EmailNotVerifiedError(AuthError):
    """
    Raised by login() specifically when the password is correct but the
    account hasn't completed email verification yet -- kept as a distinct
    subclass (not just a differently-worded AuthError) so the UI can route
    to the "enter your code" screen instead of showing a generic error.
    """


def _validate_email(email: str) -> str:
    email = email.strip().lower()
    if not _EMAIL_RE.match(email):
        raise AuthError("That doesn't look like a valid email address.")
    return email


def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise AuthError("Password must be at least 8 characters.")


def _generate_code() -> str:
    return f"{random.randint(0, 999999):06d}"


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _issue_verification_code(conn, user_id: int, email: str) -> None:
    """Generate, store, and email a fresh verification code for user_id.
    Shared by signup() and resend_verification_code()."""
    code = _generate_code()
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=_CODE_VALID_MINUTES)).isoformat()
    conn.execute(
        users.update().where(users.c.id == user_id).values(
            verification_code_hash=_hash_code(code),
            verification_code_expires_at=expires_at,
        )
    )
    email_module.send_verification_email(email, code)  # may raise EmailSendError -- caller decides how to handle


def signup(email: str, password: str) -> dict:
    """
    Create a new account and email it a verification code. The account
    exists in the database immediately but login() will raise
    EmailNotVerifiedError until verify_email() succeeds.
    Raises AuthError if the email is invalid or already registered, or
    EmailSendError if Resend isn't configured / rejects the send (the
    account is still created in that case -- resend_verification_code()
    can retry once email sending is fixed, rather than losing the signup).

    The account-creation transaction and the code-issuing-and-emailing step
    below are DELIBERATELY two separate `with db.engine.begin()` blocks,
    not one. Caught live, not assumed: putting the email send inside the
    same transaction as the INSERT meant any EmailSendError (e.g. no
    RESEND_API_KEY configured) rolled the whole transaction back -- silently
    deleting the account that was supposedly "still created in that case",
    directly contradicting this function's own documented behavior. The
    fix is to let the account-creation transaction commit on its own first.
    """
    email = _validate_email(email)
    _validate_password(password)

    with db.engine.begin() as conn:
        existing = conn.execute(select(users.c.id).where(users.c.email == email)).first()
        if existing:
            raise AuthError("An account with that email already exists. Try logging in instead.")

        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        result = conn.execute(
            users.insert().values(
                email=email, password_hash=password_hash, created_at=_now_iso(), email_verified=False,
            )
        )
        user_id = result.inserted_primary_key[0]
    # Account creation committed here -- it persists even if the code/email
    # step below fails.

    with db.engine.begin() as conn:
        _issue_verification_code(conn, user_id, email)

    return {"id": user_id, "email": email}


def resend_verification_code(email: str) -> None:
    """Generate and email a fresh code, replacing any prior unexpired one.
    Raises AuthError if there's no unverified account with that email."""
    email = _validate_email(email)

    with db.engine.begin() as conn:
        row = conn.execute(select(users).where(users.c.email == email)).mappings().first()
        if row is None:
            raise AuthError("No account found with that email.")
        if row["email_verified"]:
            raise AuthError("That account is already verified -- try logging in.")

        _issue_verification_code(conn, row["id"], email)


def verify_email(email: str, code: str) -> dict:
    """Check a verification code and, if valid, mark the account verified.
    Raises AuthError if the account doesn't exist, the code is wrong, or
    the code has expired."""
    email = _validate_email(email)
    code = code.strip()

    with db.engine.begin() as conn:
        row = conn.execute(select(users).where(users.c.email == email)).mappings().first()
        if row is None:
            raise AuthError("No account found with that email.")
        if row["email_verified"]:
            return {"id": row["id"], "email": row["email"]}

        if not row["verification_code_hash"] or not row["verification_code_expires_at"]:
            raise AuthError("No verification code is pending for this account. Request a new one.")

        expires_at = datetime.fromisoformat(row["verification_code_expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            raise AuthError("That code has expired. Request a new one.")

        if _hash_code(code) != row["verification_code_hash"]:
            raise AuthError("Incorrect code.")

        conn.execute(
            users.update().where(users.c.id == row["id"]).values(
                email_verified=True, verification_code_hash=None, verification_code_expires_at=None,
            )
        )

    return {"id": row["id"], "email": row["email"]}


def login(email: str, password: str) -> dict:
    """
    Verify credentials. Raises AuthError if the email isn't registered or
    the password is wrong; raises EmailNotVerifiedError (a subclass of
    AuthError) specifically when the password is correct but the account
    hasn't completed email verification.
    """
    email = _validate_email(email)

    with db.engine.begin() as conn:
        row = conn.execute(select(users).where(users.c.email == email)).mappings().first()

    if row is None:
        raise AuthError("No account found with that email.")

    if not bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8")):
        raise AuthError("Incorrect password.")

    if not row["email_verified"]:
        raise EmailNotVerifiedError("Please verify your email before logging in.")

    return {"id": row["id"], "email": row["email"]}
