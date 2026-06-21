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

from utils import db, auth, alerts_db


@pytest.fixture(autouse=True)
def _in_memory_db(monkeypatch):
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    monkeypatch.setattr(db, "engine", test_engine)
    monkeypatch.setattr(db, "IS_SQLITE", True)
    db.metadata.create_all(test_engine)
    yield


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


def test_login_succeeds_with_correct_credentials():
    auth.signup("dave@example.com", "supersecret1")
    user = auth.login("dave@example.com", "supersecret1")
    assert user["email"] == "dave@example.com"


def test_login_is_case_insensitive_on_email():
    auth.signup("eve@example.com", "supersecret1")
    user = auth.login("EVE@Example.com", "supersecret1")
    assert user["email"] == "eve@example.com"


def test_login_fails_with_wrong_password():
    auth.signup("frank@example.com", "supersecret1")
    with pytest.raises(auth.AuthError):
        auth.login("frank@example.com", "wrongpassword")


def test_login_fails_for_unregistered_email():
    with pytest.raises(auth.AuthError):
        auth.login("nobody@example.com", "whatever123")


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
