"""
Unit tests for utils/auth.py and the per-user scoping in utils/alerts_db.py,
run against an in-memory SQLite database (via utils/db.py's dialect-agnostic
SQLAlchemy layer) for full isolation between tests.

Monkeypatching utils.db.engine (not utils.alerts_db.engine or
utils.auth.engine) is deliberate and load-bearing: both of those modules
do `from utils import db` and reference `db.engine` dynamically rather than
importing `engine` directly, specifically so a single monkeypatch here
propagates everywhere -- the classic "from module import name" footgun
(a copied reference that a later monkeypatch on the original module
wouldn't affect) was designed around, not stumbled into.
"""

from sqlalchemy import create_engine

import pytest

from utils import db, auth, alerts_db, email as email_module

# Every signup() call sends a real verification email via Resend unless
# this is mocked -- captured into this list (email, code) so verification-
# flow tests can retrieve the actual randomly-generated code rather than
# guessing it. Cleared per-test by the autouse fixture below.
sent_codes: list[tuple[str, str]] = []


@pytest.fixture(autouse=True)
def _in_memory_db(monkeypatch):
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    monkeypatch.setattr(db, "engine", test_engine)
    monkeypatch.setattr(db, "IS_SQLITE", True)
    db.metadata.create_all(test_engine)

    sent_codes.clear()
    monkeypatch.setattr(email_module, "send_verification_email", lambda to, code: sent_codes.append((to, code)))
    yield


def _latest_code(email: str) -> str:
    return next(code for sent_to, code in reversed(sent_codes) if sent_to == email)


# ── auth ──────────────────────────────────────────────────────────────────────

def test_signup_creates_account_with_hashed_password():
    user = auth.signup("alice@example.com", "supersecret1")
    assert user["email"] == "alice@example.com"
    assert isinstance(user["id"], int)

    with db.engine.begin() as conn:
        from sqlalchemy import select
        row = conn.execute(select(db.users).where(db.users.c.id == user["id"])).mappings().first()
    assert row["password_hash"] != "supersecret1"  # never stored in plaintext
    assert row["password_hash"].startswith("$2b$")  # bcrypt's hash format marker


def test_signup_normalizes_email_case_and_whitespace():
    user = auth.signup("  Alice@Example.com  ", "supersecret1")
    assert user["email"] == "alice@example.com"


def test_signup_rejects_invalid_email():
    with pytest.raises(auth.AuthError):
        auth.signup("not-an-email", "supersecret1")


def test_signup_rejects_short_password():
    with pytest.raises(auth.AuthError):
        auth.signup("bob@example.com", "short")


def test_signup_rejects_duplicate_email():
    auth.signup("carol@example.com", "supersecret1")
    with pytest.raises(auth.AuthError):
        auth.signup("carol@example.com", "anotherpassword")


def test_login_succeeds_with_correct_credentials_after_verification():
    auth.signup("dave@example.com", "supersecret1")
    auth.verify_email("dave@example.com", _latest_code("dave@example.com"))
    user = auth.login("dave@example.com", "supersecret1")
    assert user["email"] == "dave@example.com"


def test_login_is_case_insensitive_on_email():
    auth.signup("eve@example.com", "supersecret1")
    auth.verify_email("eve@example.com", _latest_code("eve@example.com"))
    user = auth.login("EVE@Example.com", "supersecret1")
    assert user["email"] == "eve@example.com"


def test_display_name_is_normalized_and_returned_by_login():
    created = auth.signup("identity@example.com", "supersecret1")
    auth.verify_email("identity@example.com", _latest_code("identity@example.com"))

    saved = auth.update_display_name(created["id"], "  Bhaumik   Giri  ")
    user = auth.login("identity@example.com", "supersecret1")

    assert saved == "Bhaumik Giri"
    assert user["display_name"] == "Bhaumik Giri"


def test_remembered_identity_includes_display_name():
    created = auth.signup("remember-name@example.com", "supersecret1")
    auth.verify_email("remember-name@example.com", _latest_code("remember-name@example.com"))
    auth.update_display_name(created["id"], "Research Lead")
    token = auth.issue_remember_token(created["id"])

    remembered = auth.verify_remember_token(token)

    assert remembered["display_name"] == "Research Lead"


def test_display_name_requires_a_professional_length():
    created = auth.signup("name-rules@example.com", "supersecret1")
    with pytest.raises(auth.AuthError):
        auth.update_display_name(created["id"], "A")
    with pytest.raises(auth.AuthError):
        auth.update_display_name(created["id"], "x" * 49)


def test_login_fails_with_wrong_password():
    auth.signup("frank@example.com", "supersecret1")
    with pytest.raises(auth.AuthError):
        auth.login("frank@example.com", "wrongpassword")


def test_login_fails_for_unregistered_email():
    with pytest.raises(auth.AuthError):
        auth.login("nobody@example.com", "whatever123")


def test_login_raises_email_not_verified_before_verification():
    auth.signup("grace@example.com", "supersecret1")
    with pytest.raises(auth.EmailNotVerifiedError):
        auth.login("grace@example.com", "supersecret1")


# ── email verification ───────────────────────────────────────────────────────

def test_signup_sends_a_verification_code():
    auth.signup("henry@example.com", "supersecret1")
    assert _latest_code("henry@example.com") is not None
    assert len(_latest_code("henry@example.com")) == 6


def test_verify_email_with_correct_code_succeeds():
    auth.signup("iris@example.com", "supersecret1")
    code = _latest_code("iris@example.com")
    user = auth.verify_email("iris@example.com", code)
    assert user["email"] == "iris@example.com"

    with db.engine.begin() as conn:
        from sqlalchemy import select
        row = conn.execute(select(db.users).where(db.users.c.email == "iris@example.com")).mappings().first()
    assert row["email_verified"]
    assert row["verification_code_hash"] is None  # cleared after successful verification


def test_verify_email_with_wrong_code_fails():
    auth.signup("jack@example.com", "supersecret1")
    with pytest.raises(auth.AuthError):
        auth.verify_email("jack@example.com", "000000" if _latest_code("jack@example.com") != "000000" else "111111")


def test_verify_email_with_expired_code_fails():
    auth.signup("kate@example.com", "supersecret1")
    code = _latest_code("kate@example.com")

    # Force the stored expiry into the past, simulating time passing.
    with db.engine.begin() as conn:
        from sqlalchemy import select
        from datetime import datetime, timedelta, timezone
        past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        conn.execute(db.users.update().where(db.users.c.email == "kate@example.com").values(
            verification_code_expires_at=past
        ))

    with pytest.raises(auth.AuthError):
        auth.verify_email("kate@example.com", code)


def test_resend_verification_code_issues_a_new_working_code():
    auth.signup("leo@example.com", "supersecret1")
    old_code = _latest_code("leo@example.com")

    auth.resend_verification_code("leo@example.com")
    new_code = _latest_code("leo@example.com")

    # The old code must no longer work once a new one has been issued.
    with pytest.raises(auth.AuthError):
        auth.verify_email("leo@example.com", old_code)
    auth.verify_email("leo@example.com", new_code)  # the fresh one does work


def test_resend_verification_code_fails_for_already_verified_account():
    auth.signup("mia@example.com", "supersecret1")
    auth.verify_email("mia@example.com", _latest_code("mia@example.com"))
    with pytest.raises(auth.AuthError):
        auth.resend_verification_code("mia@example.com")


def test_pre_existing_account_is_grandfathered_in_as_verified():
    """Accounts created before email verification was migrated in must not
    be locked out -- _migrate_users_table() backfills them as verified.

    A brand-new in-memory test DB always creates the table with every
    column already present (create_all() never needs to ALTER an existing
    table), so the actual migration codepath in _migrate_users_table() is
    exercised separately, against a real pre-existing SQLite file, below in
    test_migrate_users_table_grandfathers_existing_accounts(). This test
    instead confirms the OUTCOME that migration is responsible for: a
    verified account's login() doesn't raise EmailNotVerifiedError."""
    password_hash = __import__("bcrypt").hashpw(b"supersecret1", __import__("bcrypt").gensalt()).decode("utf-8")
    with db.engine.begin() as conn:
        from datetime import datetime, timezone
        conn.execute(db.users.insert().values(
            email="old-account@example.com", password_hash=password_hash,
            created_at=datetime.now(timezone.utc).isoformat(), email_verified=True,
        ))

    user = auth.login("old-account@example.com", "supersecret1")
    assert user["email"] == "old-account@example.com"


def test_migrate_users_table_grandfathers_existing_accounts(tmp_path, monkeypatch):
    """Exercises the REAL ALTER TABLE migration path: a users table that
    exists WITHOUT the email_verified column (simulating a database created
    before this feature existed) must have existing rows backfilled as
    verified once init_db() runs the migration, and new rows after that
    point must default to unverified."""
    from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text

    file_engine = create_engine(f"sqlite:///{tmp_path / 'migration_test.db'}")
    monkeypatch.setattr(db, "engine", file_engine)
    monkeypatch.setattr(db, "IS_SQLITE", True)

    # Create an OLD-shape users table by hand, without the new columns.
    old_metadata = MetaData()
    old_users = Table(
        "users", old_metadata,
        Column("id", Integer, primary_key=True),
        Column("email", String(255), nullable=False, unique=True),
        Column("password_hash", Text, nullable=False),
        Column("created_at", String(64), nullable=False),
    )
    old_metadata.create_all(file_engine)
    with file_engine.begin() as conn:
        conn.execute(old_users.insert().values(
            email="preexisting@example.com", password_hash="hash", created_at="2025-01-01T00:00:00+00:00",
        ))

    db.init_db()  # creates the other tables fresh + migrates `users`

    with file_engine.begin() as conn:
        from sqlalchemy import select
        row = conn.execute(select(db.users).where(db.users.c.email == "preexisting@example.com")).mappings().first()
    assert row["email_verified"]  # grandfathered in, not locked out
    assert row["onboarding_completed_at"]  # existing members are not interrupted

    # A signup() AFTER migration must still default to unverified.
    auth.signup("brandnew@example.com", "supersecret1")
    with file_engine.begin() as conn:
        from sqlalchemy import select
        row2 = conn.execute(select(db.users).where(db.users.c.email == "brandnew@example.com")).mappings().first()
    assert not row2["email_verified"]
    assert row2["onboarding_completed_at"] is None


# ── multi-tenant isolation ────────────────────────────────────────────────────

def test_watchlist_is_isolated_per_user():
    user1 = auth.signup("user1@example.com", "password123")
    user2 = auth.signup("user2@example.com", "password123")

    alerts_db.add_to_watchlist(user1["id"], "MSFT")
    alerts_db.add_to_watchlist(user2["id"], "GOOGL")

    wl1 = alerts_db.get_watchlist(user1["id"])
    wl2 = alerts_db.get_watchlist(user2["id"])

    assert [r["ticker"] for r in wl1] == ["MSFT"]
    assert [r["ticker"] for r in wl2] == ["GOOGL"]


def test_same_ticker_can_be_watched_by_multiple_users_independently():
    user1 = auth.signup("user1@example.com", "password123")
    user2 = auth.signup("user2@example.com", "password123")

    alerts_db.add_to_watchlist(user1["id"], "CCJ", score_bull_threshold=70.0)
    alerts_db.add_to_watchlist(user2["id"], "CCJ", score_bull_threshold=60.0)

    wl1 = alerts_db.get_watchlist(user1["id"])
    wl2 = alerts_db.get_watchlist(user2["id"])
    assert wl1[0]["score_bull_threshold"] == 70.0
    assert wl2[0]["score_bull_threshold"] == 60.0


def test_alert_feed_is_isolated_per_user():
    user1 = auth.signup("user1@example.com", "password123")
    user2 = auth.signup("user2@example.com", "password123")

    alerts_db.create_alert(user1["id"], "MSFT", "score_threshold", "user1's alert")
    alerts_db.create_alert(user2["id"], "GOOGL", "score_threshold", "user2's alert")

    assert [a["message"] for a in alerts_db.get_alerts(user1["id"])] == ["user1's alert"]
    assert [a["message"] for a in alerts_db.get_alerts(user2["id"])] == ["user2's alert"]


def test_mark_read_cannot_cross_user_boundary():
    """A user must not be able to mark another user's alert as read, even
    knowing its raw alert id."""
    user1 = auth.signup("user1@example.com", "password123")
    user2 = auth.signup("user2@example.com", "password123")
    alert_id = alerts_db.create_alert(user1["id"], "MSFT", "score_threshold", "user1's alert")

    alerts_db.mark_read(user2["id"], alert_id)  # user2 tries to mark user1's alert read

    user1_alerts = alerts_db.get_alerts(user1["id"])
    assert user1_alerts[0]["is_read"] == 0  # still unread -- the cross-user mark had no effect


def test_remove_from_watchlist_only_affects_that_user():
    user1 = auth.signup("user1@example.com", "password123")
    user2 = auth.signup("user2@example.com", "password123")
    alerts_db.add_to_watchlist(user1["id"], "MSFT")
    alerts_db.add_to_watchlist(user2["id"], "MSFT")

    alerts_db.remove_from_watchlist(user1["id"], "MSFT")

    assert alerts_db.get_watchlist(user1["id"]) == []
    assert len(alerts_db.get_watchlist(user2["id"])) == 1


# ── "remember me" persistent login ──────────────────────────────────────────
#
# These three functions (issue/verify/revoke) are pure DB operations -- no
# Streamlit, no browser, no cookie component involved -- so they're fully
# unit-testable here. What CANNOT be tested this way, and isn't tested
# anywhere in this suite, is the actual browser cookie round-trip: the
# streamlit-cookies-manager-v2 component's cookies.ready() requires a real
# browser executing its JS side to ever become True. Under AppTest (no real
# browser attached), require_login()'s not-logged-in path will always see
# cookies.ready() == False and call st.stop() -- meaning AppTest can confirm
# that path doesn't crash, but tells you NOTHING about whether a real
# "remember me" cookie actually gets set, read back, or survives a browser
# restart. That part requires checking against a live, deployed app in a
# real browser, not this suite. Same category of blind spot as the
# st.fragment one documented in conftest.py's module docstring.

def test_issue_remember_token_returns_a_usable_token_and_verify_succeeds():
    user = auth.signup("remember1@example.com", "password123")
    auth.verify_email("remember1@example.com", _latest_code("remember1@example.com"))

    token = auth.issue_remember_token(user["id"])
    assert isinstance(token, str) and len(token) > 20  # secrets.token_urlsafe(32) -- a real, long token

    verified = auth.verify_remember_token(token)
    assert verified == {
        "id": user["id"],
        "email": "remember1@example.com",
        "display_name": None,
    }


def test_verify_remember_token_rejects_garbage_token():
    assert auth.verify_remember_token("not-a-real-token-at-all") is None


def test_verify_remember_token_rejects_expired_token():
    user = auth.signup("remember2@example.com", "password123")
    auth.verify_email("remember2@example.com", _latest_code("remember2@example.com"))
    token = auth.issue_remember_token(user["id"])

    # Force the stored expiry into the past, simulating 30+ days passing.
    with db.engine.begin() as conn:
        from sqlalchemy import select
        from datetime import datetime, timedelta, timezone
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        conn.execute(db.remember_tokens.update().where(
            db.remember_tokens.c.token_hash == auth._hash_code(token)
        ).values(expires_at=past))

    assert auth.verify_remember_token(token) is None


def test_revoke_remember_token_invalidates_it():
    user = auth.signup("remember3@example.com", "password123")
    auth.verify_email("remember3@example.com", _latest_code("remember3@example.com"))
    token = auth.issue_remember_token(user["id"])
    assert auth.verify_remember_token(token) is not None  # works before revoking

    auth.revoke_remember_token(token)

    assert auth.verify_remember_token(token) is None  # dead after revoking


def test_revoke_remember_token_is_safe_to_call_on_unknown_token():
    """Logging out with no remember-me cookie ever set must not raise --
    revoke_remember_token() is called unconditionally by utils/auth_ui.py's
    logout() whenever a token happens to be in session_state."""
    auth.revoke_remember_token("a-token-that-was-never-issued")  # no exception


def test_each_login_can_issue_an_independent_remember_token():
    """Two separate 'remember me' tokens for the same user (e.g. one
    per device) must both work independently -- logging out one device
    must not be implemented as "delete by user_id", which would silently
    kill the other device's session too (see revoke_remember_token's
    docstring: it deletes by hash, specifically to avoid this)."""
    user = auth.signup("remember4@example.com", "password123")
    auth.verify_email("remember4@example.com", _latest_code("remember4@example.com"))

    token_device_a = auth.issue_remember_token(user["id"])
    token_device_b = auth.issue_remember_token(user["id"])
    assert token_device_a != token_device_b

    auth.revoke_remember_token(token_device_a)

    assert auth.verify_remember_token(token_device_a) is None
    assert auth.verify_remember_token(token_device_b) is not None


# ── periodic maintenance / retention cleanup (added 2026-06-22, per UI/usage
# audit: expired remember-tokens and old read alerts were never purged) ──────

def test_cleanup_expired_remember_tokens_deletes_only_expired_rows():
    from datetime import datetime, timedelta, timezone

    user = auth.signup("cleanup1@example.com", "password123")
    auth.verify_email("cleanup1@example.com", _latest_code("cleanup1@example.com"))

    live_token = auth.issue_remember_token(user["id"])
    expired_token = auth.issue_remember_token(user["id"])
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    with db.engine.begin() as conn:
        conn.execute(db.remember_tokens.update().where(
            db.remember_tokens.c.token_hash == auth._hash_code(expired_token)
        ).values(expires_at=past))

    deleted = auth.cleanup_expired_remember_tokens()

    assert deleted == 1
    assert auth.verify_remember_token(live_token) is not None  # untouched
    # The expired row is actually gone from the table now, not just treated
    # as expired by a date check -- verify_remember_token already returned
    # None for it before cleanup ran, so check the row itself disappeared.
    with db.engine.begin() as conn:
        from sqlalchemy import select
        remaining = conn.execute(
            select(db.remember_tokens.c.id).where(
                db.remember_tokens.c.token_hash == auth._hash_code(expired_token)
            )
        ).first()
    assert remaining is None


def test_cleanup_expired_remember_tokens_is_safe_with_no_expired_rows():
    user = auth.signup("cleanup2@example.com", "password123")
    auth.verify_email("cleanup2@example.com", _latest_code("cleanup2@example.com"))
    auth.issue_remember_token(user["id"])

    assert auth.cleanup_expired_remember_tokens() == 0


def test_cleanup_old_read_alerts_deletes_only_old_and_read():
    user = auth.signup("cleanup3@example.com", "password123")
    auth.verify_email("cleanup3@example.com", _latest_code("cleanup3@example.com"))
    uid = user["id"]

    old_read_id   = alerts_db.create_alert(uid, "CCJ", "score_change", "old, read -- should be deleted")
    old_unread_id = alerts_db.create_alert(uid, "CCJ", "score_change", "old, unread -- must survive")
    new_read_id   = alerts_db.create_alert(uid, "CCJ", "score_change", "recent, read -- must survive")

    alerts_db.mark_read(uid, old_read_id)
    alerts_db.mark_read(uid, new_read_id)

    from datetime import datetime, timedelta, timezone
    old_ts = (datetime.now(timezone.utc) - timedelta(days=120)).isoformat()
    with db.engine.begin() as conn:
        conn.execute(db.alerts.update().where(db.alerts.c.id.in_([old_read_id, old_unread_id]))
                     .values(created_at=old_ts))

    deleted = alerts_db.cleanup_old_read_alerts(retention_days=90)

    assert deleted == 1
    remaining_ids = {row["id"] for row in alerts_db.get_alerts(uid, limit=50)}
    assert old_read_id not in remaining_ids        # old AND read -- gone
    assert old_unread_id in remaining_ids           # old but UNREAD -- never auto-deleted
    assert new_read_id in remaining_ids             # read but recent -- not old enough yet


def test_run_periodic_maintenance_force_runs_both_cleanups():
    user = auth.signup("cleanup4@example.com", "password123")
    auth.verify_email("cleanup4@example.com", _latest_code("cleanup4@example.com"))
    token = auth.issue_remember_token(user["id"])

    from datetime import datetime, timedelta, timezone
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    with db.engine.begin() as conn:
        conn.execute(db.remember_tokens.update().where(
            db.remember_tokens.c.token_hash == auth._hash_code(token)
        ).values(expires_at=past))

    result = db.run_periodic_maintenance(force=True)

    assert result["ran"] is True
    assert result["remember_tokens_deleted"] == 1


def test_run_periodic_maintenance_without_force_usually_skips(monkeypatch):
    """
    Without force=True, this should almost never run -- pin random.random()
    to always return a value above the probability gate, deterministically
    proving the gate actually gates rather than relying on it being
    statistically unlikely to trigger in a single test run.
    """
    monkeypatch.setattr("random.random", lambda: 0.999)
    result = db.run_periodic_maintenance()
    assert result == {"ran": False, "remember_tokens_deleted": 0, "alerts_deleted": 0}
