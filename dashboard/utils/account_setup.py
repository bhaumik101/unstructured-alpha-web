"""Persistent, one-time account setup for newly verified members."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update

from utils import db
from utils.db import users
from utils.risk_profile import normalize as normalize_risk_profile


INTEREST_TICKERS: tuple[str, ...] = (
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA",
    "JPM", "XOM", "CCJ", "GLD", "TLT", "SPY", "QQQ", "IWM",
)
DIGEST_PREFERENCES = ("in_app", "morning_email")
MAX_STARTER_TICKERS = 5


def needs_account_setup(user_id: int | None) -> bool:
    """Return True only for a real user whose setup has not been resolved."""
    if not user_id:
        return False
    try:
        with db.engine.begin() as conn:
            row = conn.execute(
                select(users.c.onboarding_completed_at).where(users.c.id == user_id)
            ).fetchone()
        # A missing user must never create a redirect loop.
        return row is not None and row[0] is None
    except Exception:
        # Account setup is an enhancement, never an availability gate.
        return False


def complete_account_setup(
    user_id: int,
    *,
    display_name: str,
    risk_profile: Any,
    interest_tickers: list[str] | tuple[str, ...],
    digest_preference: str,
) -> dict:
    """Validate and save setup preferences, then seed the user's watchlist."""
    name = " ".join((display_name or "").split())
    if not 2 <= len(name) <= 48:
        raise ValueError("Display name must be between 2 and 48 characters.")

    preference = str(digest_preference or "").strip().lower()
    if preference not in DIGEST_PREFERENCES:
        raise ValueError("Choose a valid briefing preference.")

    selected: list[str] = []
    for raw in interest_tickers or ():
        ticker = str(raw).upper().strip()
        if ticker in INTEREST_TICKERS and ticker not in selected:
            selected.append(ticker)
    if not selected:
        raise ValueError("Choose at least one ticker to personalize your starting view.")
    if len(selected) > MAX_STARTER_TICKERS:
        raise ValueError(f"Choose up to {MAX_STARTER_TICKERS} starting tickers.")

    profile = normalize_risk_profile(risk_profile)
    completed_at = datetime.now(timezone.utc).isoformat()
    with db.engine.begin() as conn:
        tier = conn.execute(
            select(users.c.subscription_tier).where(users.c.id == user_id)
        ).scalar_one_or_none()
        if tier is None:
            raise ValueError("Account not found.")
        conn.execute(
            update(users).where(users.c.id == user_id).values(
                display_name=name,
                risk_profile=json.dumps(profile, separators=(",", ":")),
                digest_preference=preference,
                digest_opted_in=(preference == "morning_email" and tier == "pro"),
            )
        )

    # Use the shared watchlist write path so universe expansion,
    # instrumentation, and alert defaults remain consistent everywhere.
    from utils.alerts_db import add_to_watchlist
    for ticker in selected:
        add_to_watchlist(user_id, ticker)

    # Completion is written last. If a watchlist write fails, the setup stays
    # resumable instead of claiming success with a partially initialized account.
    with db.engine.begin() as conn:
        conn.execute(
            update(users).where(users.c.id == user_id).values(
                onboarding_completed_at=completed_at,
            )
        )

    return {
        "display_name": name,
        "risk_profile": profile,
        "interest_tickers": selected,
        "digest_preference": preference,
        "completed_at": completed_at,
    }


def skip_account_setup(user_id: int) -> str:
    """Resolve setup without changing any existing account preferences."""
    completed_at = datetime.now(timezone.utc).isoformat()
    with db.engine.begin() as conn:
        result = conn.execute(
            update(users).where(users.c.id == user_id).values(
                onboarding_completed_at=completed_at,
            )
        )
        if not result.rowcount:
            raise ValueError("Account not found.")
    return completed_at
