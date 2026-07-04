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
_MAX_FAILED_LOGINS = 5      # consecutive wrong passwords before account lockout
_LOCKOUT_MINUTES = 15       # how long the lockout lasts
_MAX_OTP_ATTEMPTS = 5       # wrong verification codes before code is invalidated
_RESET_CODE_VALID_MINUTES = 15  # password reset code TTL


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


class AccountLockedError(AuthError):
    """
    Raised by login() when too many consecutive wrong passwords have
    temporarily locked the account. Kept distinct from AuthError so the UI
    can display the lockout duration rather than a generic "wrong password"
    message (and avoid implying the password was incorrect, which would
    confirm to an attacker that the email is registered).
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


def signup(email: str, password: str, ref_code: str = "") -> dict:
    """
    Create a new account and email it a verification code. The account
    exists in the database immediately but login() will raise
    EmailNotVerifiedError until verify_email() succeeds.
    Raises AuthError if the email is invalid or already registered, or
    EmailSendError if Resend isn't configured / rejects the send (the
    account is still created in that case -- resend_verification_code()
    can retry once email sending is fixed, rather than losing the signup).

    ref_code: optional referral code from ?ref= query param. If valid,
    records the referral relationship so the referrer can earn their reward
    when this user converts to Pro.

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

    # Record referral relationship if a valid ref_code was supplied.
    # Best-effort — never blocks signup on failure.
    if ref_code:
        try:
            from utils.referral import record_referral_signup
            record_referral_signup(email, ref_code)
        except Exception:
            pass

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
    the code has expired. After _MAX_OTP_ATTEMPTS wrong codes the pending
    code is invalidated and the user must request a fresh one."""
    email = _validate_email(email)
    code = code.strip()

    # Read pass — separate from the write below so failed-attempt increments
    # aren't rolled back when we raise AuthError inside the same transaction.
    with db.engine.begin() as conn:
        row = conn.execute(select(users).where(users.c.email == email)).mappings().first()

    if row is None:
        raise AuthError("No account found with that email.")
    if row["email_verified"]:
        return {"id": row["id"], "email": row["email"]}

    if not row.get("verification_code_hash") or not row.get("verification_code_expires_at"):
        raise AuthError("No verification code is pending for this account. Request a new one.")

    expires_at = datetime.fromisoformat(row["verification_code_expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        raise AuthError("That code has expired. Request a new one.")

    attempt_count = row.get("verification_attempt_count") or 0

    # Already exhausted — invalidate and tell them to start over.
    if attempt_count >= _MAX_OTP_ATTEMPTS:
        with db.engine.begin() as conn:
            conn.execute(users.update().where(users.c.id == row["id"]).values(
                verification_code_hash=None, verification_code_expires_at=None,
                verification_attempt_count=0,
            ))
        raise AuthError("Too many incorrect attempts. Request a new verification code.")

    if _hash_code(code) != row["verification_code_hash"]:
        new_count = attempt_count + 1
        if new_count >= _MAX_OTP_ATTEMPTS:
            # This attempt exhausts the limit — invalidate the code.
            with db.engine.begin() as conn:
                conn.execute(users.update().where(users.c.id == row["id"]).values(
                    verification_code_hash=None, verification_code_expires_at=None,
                    verification_attempt_count=0,
                ))
            raise AuthError("Too many incorrect attempts. Request a new verification code.")
        with db.engine.begin() as conn:
            conn.execute(users.update().where(users.c.id == row["id"]).values(
                verification_attempt_count=new_count,
            ))
        remaining = _MAX_OTP_ATTEMPTS - new_count
        raise AuthError(f"Incorrect code. {remaining} attempt(s) remaining.")

    # Code is correct — mark verified and reset counter.
    with db.engine.begin() as conn:
        conn.execute(users.update().where(users.c.id == row["id"]).values(
            email_verified=True, verification_code_hash=None,
            verification_code_expires_at=None, verification_attempt_count=0,
        ))

    # Fire-and-forget welcome email — must NOT raise so a Resend hiccup never
    # prevents the user from logging in after verifying.
    try:
        email_module.send_welcome_email(row["email"])
    except Exception as _exc:  # EmailSendError or anything else from Resend
        import logging as _logging
        _logging.getLogger(__name__).warning(
            "Welcome email failed for %s: %s", row["email"], _exc
        )

    return {"id": row["id"], "email": row["email"]}


def login(email: str, password: str) -> dict:
    """
    Verify credentials. Raises:
      AccountLockedError  — too many failed attempts, account temporarily locked
      AuthError           — email not registered or wrong password
      EmailNotVerifiedError — password correct but account not yet verified
    On success, resets the failed-attempt counter and returns the user dict.
    """
    email = _validate_email(email)

    # Read in its own transaction so the writes below aren't rolled back if
    # we raise after them (same pattern as verify_email above).
    with db.engine.begin() as conn:
        row = conn.execute(select(users).where(users.c.email == email)).mappings().first()

    if row is None:
        raise AuthError("No account found with that email.")

    # Check lockout BEFORE testing the password — avoids telling an attacker
    # "your password would be wrong" even while locked.
    locked_until_str = row.get("login_locked_until")
    if locked_until_str:
        unlock_time = datetime.fromisoformat(locked_until_str)
        if datetime.now(timezone.utc) < unlock_time:
            remaining = max(1, int((unlock_time - datetime.now(timezone.utc)).total_seconds() / 60) + 1)
            raise AccountLockedError(
                f"Too many failed attempts. This account is locked for another "
                f"{remaining} minute(s). Try again later or reset your password."
            )
        # Lockout has expired — clear it before proceeding.
        with db.engine.begin() as conn:
            conn.execute(users.update().where(users.c.id == row["id"]).values(
                login_attempt_count=0, login_locked_until=None,
            ))

    if not bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8")):
        attempt_count = (row.get("login_attempt_count") or 0) + 1
        if attempt_count >= _MAX_FAILED_LOGINS:
            lock_until = (
                datetime.now(timezone.utc) + timedelta(minutes=_LOCKOUT_MINUTES)
            ).isoformat()
            with db.engine.begin() as conn:
                conn.execute(users.update().where(users.c.id == row["id"]).values(
                    login_attempt_count=0, login_locked_until=lock_until,
                ))
            raise AccountLockedError(
                f"Too many failed attempts. This account is locked for "
                f"{_LOCKOUT_MINUTES} minutes. Try again later or reset your password."
            )
        with db.engine.begin() as conn:
            conn.execute(users.update().where(users.c.id == row["id"]).values(
                login_attempt_count=attempt_count,
            ))
        remaining_attempts = _MAX_FAILED_LOGINS - attempt_count
        raise AuthError(
            f"Incorrect password. {remaining_attempts} attempt(s) remaining before lockout."
        )

    if not row["email_verified"]:
        raise EmailNotVerifiedError("Please verify your email before logging in.")

    # Successful login — reset the fail counter.
    with db.engine.begin() as conn:
        conn.execute(users.update().where(users.c.id == row["id"]).values(
            login_attempt_count=0, login_locked_until=None,
        ))

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


def request_password_reset(email: str) -> None:
    """
    Generate a 6-digit reset code, store its hash, and email it to the
    account holder. If no account exists for that email, do nothing silently
    — callers should always show a generic "if registered, check your email"
    message so this can't be used to enumerate registered addresses.
    Raises EmailSendError if Resend rejects the send (the reset code was
    stored in DB already, so the user can still use it once email is working).
    """
    email = _validate_email(email)

    with db.engine.begin() as conn:
        row = conn.execute(select(users.c.id).where(users.c.email == email)).fetchone()
        if row is None:
            return  # silent — don't reveal whether the email is registered

        code = _generate_code()
        expires_at = (
            datetime.now(timezone.utc) + timedelta(minutes=_RESET_CODE_VALID_MINUTES)
        ).isoformat()
        conn.execute(users.update().where(users.c.id == row[0]).values(
            password_reset_code_hash=_hash_code(code),
            password_reset_expires_at=expires_at,
        ))

    email_module.send_password_reset_email(email, code)  # raises EmailSendError on failure


def reset_password(email: str, code: str, new_password: str) -> None:
    """
    Verify a password reset code and update the account's password hash.
    Raises AuthError if the account doesn't exist, the code is wrong, or
    the code has expired. Also clears any login lockout so a forgotten
    password can't strand a user indefinitely.
    """
    email = _validate_email(email)
    _validate_password(new_password)
    code = code.strip()

    with db.engine.begin() as conn:
        row = conn.execute(select(users).where(users.c.email == email)).mappings().first()

    if row is None:
        raise AuthError("No account found with that email.")

    if not row.get("password_reset_code_hash") or not row.get("password_reset_expires_at"):
        raise AuthError("No password reset is pending. Request a new reset code.")

    expires_at = datetime.fromisoformat(row["password_reset_expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        raise AuthError("That reset code has expired. Request a new one.")

    if _hash_code(code) != row["password_reset_code_hash"]:
        raise AuthError("Incorrect reset code.")

    new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    with db.engine.begin() as conn:
        conn.execute(users.update().where(users.c.id == row["id"]).values(
            password_hash=new_hash,
            password_reset_code_hash=None,
            password_reset_expires_at=None,
            # Clear any lingering lockout — a successful password reset is a
            # valid recovery path for a locked account.
            login_attempt_count=0,
            login_locked_until=None,
        ))


def change_password(user_id: int, current_password: str, new_password: str) -> None:
    """
    Verify current_password and update to new_password for the given user.
    Raises AuthError on wrong current password, or if new password is too short.
    Used by the Profile page for in-session password changes (no email code needed).
    """
    _validate_password(new_password)

    with db.engine.begin() as conn:
        row = conn.execute(
            select(users.c.password_hash).where(users.c.id == user_id)
        ).fetchone()

    if row is None:
        raise AuthError("Account not found.")
    if not bcrypt.checkpw(current_password.encode("utf-8"), row[0].encode("utf-8")):
        raise AuthError("Current password is incorrect.")

    new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    with db.engine.begin() as conn:
        conn.execute(users.update().where(users.c.id == user_id).values(password_hash=new_hash))


def get_full_profile(user_id: int) -> dict | None:
    """Return all profile fields for a user, or None if not found."""
    with db.engine.begin() as conn:
        row = conn.execute(select(users).where(users.c.id == user_id)).mappings().first()
    if row is None:
        return None
    return dict(row)


def update_display_name(user_id: int, display_name: str) -> None:
    """Save or clear the display name for a user."""
    name = display_name.strip()[:64] if display_name else None
    with db.engine.begin() as conn:
        conn.execute(users.update().where(users.c.id == user_id).values(display_name=name))


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
