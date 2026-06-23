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
# "Remember me" persistent login (added 2026-06-21, per explicit user
# request, via utils/auth_ui.py + the streamlit-cookies-manager-v2
# component -- Streamlit itself still has no built-in cookie API, so this
# is bolted on with a third-party browser-cookie component, not a core
# Streamlit feature). issue_remember_token()/verify_remember_token()/
# revoke_remember_token() below implement it: a high-entropy random token
# goes in the user's browser cookie; only its SHA-256 hash is ever stored
# server-side (utils/db.py's remember_tokens table), so a database leak
# alone can't be used to forge a session -- the same reasoning already
# applied to verification_code_hash. Stated plainly, this is NOT
# token-rotation-on-each-use (a real refresh-token system would reissue a
# new token every time the old one is redeemed, limiting how long a
# stolen cookie value stays useful) -- a fixed-expiry, non-rotating token
# is a deliberate simplification for this project's scale, not an
# oversight. Also stated plainly: still no password reset flow and no
# rate-limiting on login/code-verification attempts -- real gaps for a
# production system, the most obvious next hardening steps if this app
# gets real outside users.

import hashlib
import random
import re
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from sqlalchemy import select, update

from utils import db, email as email_module
from utils.db import users, remember_tokens
from utils.email import EmailSendError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_CODE_VALID_MINUTES = 15
_REMEMBER_ME_DAYS = 30


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


def issue_remember_token(user_id: int) -> str:
    """
    Generate a fresh "remember me" token for user_id, store its hash, and
    return the RAW token -- the caller (utils/auth_ui.py) puts this raw
    value in a browser cookie. secrets.token_urlsafe(32) gives 256 bits of
    randomness, the same order of magnitude as a bcrypt hash itself --
    intentionally overkill for guessing resistance, since the actual
    constraint here is "don't make this the weak link," not minimizing
    bytes. Reuses _hash_code()'s SHA-256-hexdigest logic: hashing a random
    token and hashing a 6-digit code are the same operation, just applied
    to different kinds of secret.
    """
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=_REMEMBER_ME_DAYS)).isoformat()
    with db.engine.begin() as conn:
        conn.execute(
            remember_tokens.insert().values(
                user_id=user_id, token_hash=_hash_code(token), created_at=_now_iso(), expires_at=expires_at,
            )
        )
    return token


def verify_remember_token(token: str) -> dict | None:
    """
    Look up a raw token (as read back from the browser cookie) by its
    hash. Returns the user dict ({"id", "email"}) if it matches a
    non-expired row, else None -- callers treat None as "fall through to
    the normal login form," not as an error, since an expired or
    already-revoked cookie is an entirely expected, non-exceptional case.
    """
    with db.engine.begin() as conn:
        row = conn.execute(
            select(remember_tokens.c.user_id, remember_tokens.c.expires_at, users.c.email)
            .join(users, users.c.id == remember_tokens.c.user_id)
            .where(remember_tokens.c.token_hash == _hash_code(token))
        ).mappings().first()

    if row is None:
        return None
    if datetime.now(timezone.utc) > datetime.fromisoformat(row["expires_at"]):
        return None

    return {"id": row["user_id"], "email": row["email"]}


def revoke_remember_token(token: str) -> None:
    """Delete a remember-me token by its raw value (called at logout).
    Deleting by hash, not by user_id, so logging out in one browser
    doesn't invalidate a "remember me" session left active in another."""
    with db.engine.begin() as conn:
        conn.execute(remember_tokens.delete().where(remember_tokens.c.token_hash == _hash_code(token)))


def set_digest_optin(user_id: int, opted_in: bool) -> None:
    """Toggle the morning digest opt-in for a user."""
    with db.engine.begin() as conn:
        conn.execute(update(users).where(users.c.id == user_id).values(digest_opted_in=opted_in))


def get_digest_optin(user_id: int) -> bool:
    """Return the current digest opt-in state for a user. Defaults False if unset."""
    with db.engine.begin() as conn:
        row = conn.execute(select(users.c.digest_opted_in).where(users.c.id == user_id)).fetchone()
    if row is None:
        return False
    return bool(row[0])


def cleanup_expired_remember_tokens() -> int:
    """
    Delete remember_tokens rows past their expires_at that were never used
    or explicitly revoked. verify_remember_token() already treats an
    expired row as "not logged in" -- correct from a security standpoint
    -- but it never deletes that row, so a token nobody ever logs back in
    with (browser cleared, cookie never read again, etc.) sits in the
    table forever. Harmless at small scale, genuinely unbounded growth
    over years at real scale. Called probabilistically from
    utils.db.run_periodic_maintenance(), not on every request -- a DELETE
    with an indexed comparison is cheap, but there's no reason to run it
    on every single page load across every user.

    Returns the number of rows deleted (mainly so a caller/test can
    confirm this actually did something, not just that it didn't crash).
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    with db.engine.begin() as conn:
        result = conn.execute(remember_tokens.delete().where(remember_tokens.c.expires_at < now_iso))
        return result.rowcount
