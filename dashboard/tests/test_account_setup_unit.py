"""Persistence and safety checks for the first-run account setup."""

from sqlalchemy import create_engine, select
import pytest

from utils import account_setup, auth, db, email as email_module


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setattr(db, "IS_SQLITE", True)
    db.metadata.create_all(engine)
    monkeypatch.setattr(email_module, "send_verification_email", lambda *_args: None)


def _new_user(email="setup@example.com"):
    return auth.signup(email, "supersecret1")


def test_new_account_needs_setup_and_skip_resolves_it():
    user = _new_user()
    assert account_setup.needs_account_setup(user["id"])

    completed_at = account_setup.skip_account_setup(user["id"])

    assert completed_at
    assert not account_setup.needs_account_setup(user["id"])


def test_complete_setup_persists_identity_research_and_watchlist():
    user = _new_user()

    result = account_setup.complete_account_setup(
        user["id"],
        display_name="  Alpha   Researcher  ",
        risk_profile={"tolerance": "aggressive", "horizon": "short", "emphasis": "full"},
        interest_tickers=["NVDA", "SPY", "NVDA"],
        digest_preference="morning_email",
    )

    with db.engine.begin() as conn:
        profile = conn.execute(select(db.users).where(db.users.c.id == user["id"])).mappings().one()
        tickers = conn.execute(
            select(db.watchlist.c.ticker).where(db.watchlist.c.user_id == user["id"])
        ).scalars().all()
    assert result["display_name"] == "Alpha Researcher"
    assert profile["display_name"] == "Alpha Researcher"
    assert '"tolerance":"aggressive"' in profile["risk_profile"]
    assert profile["digest_preference"] == "morning_email"
    assert not profile["digest_opted_in"]  # delivery stays Pro-gated
    assert profile["onboarding_completed_at"]
    assert sorted(tickers) == ["NVDA", "SPY"]


def test_pro_morning_preference_activates_delivery():
    user = _new_user("pro-setup@example.com")
    with db.engine.begin() as conn:
        conn.execute(db.users.update().where(db.users.c.id == user["id"]).values(subscription_tier="pro"))

    account_setup.complete_account_setup(
        user["id"],
        display_name="Pro Member",
        risk_profile={},
        interest_tickers=["QQQ"],
        digest_preference="morning_email",
    )

    with db.engine.begin() as conn:
        opted_in = conn.execute(
            select(db.users.c.digest_opted_in).where(db.users.c.id == user["id"])
        ).scalar_one()
    assert opted_in


def test_watchlist_failure_keeps_setup_resumable(monkeypatch):
    user = _new_user("retry-setup@example.com")

    def fail_watchlist_write(*_args, **_kwargs):
        raise RuntimeError("write failed")

    monkeypatch.setattr("utils.alerts_db.add_to_watchlist", fail_watchlist_write)

    with pytest.raises(RuntimeError, match="write failed"):
        account_setup.complete_account_setup(
            user["id"],
            display_name="Retry Member",
            risk_profile={},
            interest_tickers=["SPY"],
            digest_preference="in_app",
        )
    assert account_setup.needs_account_setup(user["id"])


@pytest.mark.parametrize(
    "name,tickers,preference",
    [("A", ["SPY"], "in_app"), ("Valid Name", [], "in_app"), ("Valid Name", ["SPY"], "sms")],
)
def test_invalid_setup_does_not_mark_complete(name, tickers, preference):
    user = _new_user(f"invalid-{len(name)}-{len(tickers)}-{preference}@example.com")
    with pytest.raises(ValueError):
        account_setup.complete_account_setup(
            user["id"],
            display_name=name,
            risk_profile={},
            interest_tickers=tickers,
            digest_preference=preference,
        )
    assert account_setup.needs_account_setup(user["id"])
