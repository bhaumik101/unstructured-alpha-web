"""Tests for persistent, weighted Portfolio Intelligence holdings."""

import pytest
from sqlalchemy import delete, select

from utils import db
from utils.portfolio_workspace import (
    get_default_holdings,
    normalize_holdings,
    parse_holdings_text,
    replace_default_holdings,
)


_USERS = (9101, 9102)


@pytest.fixture(autouse=True)
def _clean_portfolios():
    db.init_db()
    with db.engine.begin() as conn:
        ids = select(db.portfolios.c.id).where(db.portfolios.c.user_id.in_(_USERS))
        conn.execute(delete(db.portfolio_holdings).where(db.portfolio_holdings.c.portfolio_id.in_(ids)))
        conn.execute(delete(db.portfolios).where(db.portfolios.c.user_id.in_(_USERS)))
    yield
    with db.engine.begin() as conn:
        ids = select(db.portfolios.c.id).where(db.portfolios.c.user_id.in_(_USERS))
        conn.execute(delete(db.portfolio_holdings).where(db.portfolio_holdings.c.portfolio_id.in_(ids)))
        conn.execute(delete(db.portfolios).where(db.portfolios.c.user_id.in_(_USERS)))


def test_parse_import_normalizes_weights_and_reports_rejected_rows():
    rows, rejected = parse_holdings_text(
        "NVDA, 30%\nAAPL 20\nMSFT\nNOTREAL, 10",
        valid_symbols={"NVDA", "AAPL", "MSFT"},
    )
    assert [row["ticker"] for row in rows] == ["NVDA", "AAPL", "MSFT"]
    assert sum(row["weight_pct"] for row in rows) == pytest.approx(100.0)
    assert rejected == ["NOTREAL, 10"]


def test_duplicate_ticker_keeps_last_value_and_equal_weights_when_unspecified():
    rows = normalize_holdings([
        {"ticker": "aapl"},
        {"ticker": "NVDA"},
        {"ticker": "AAPL", "weight": 40},
    ])
    assert rows == [
        {"ticker": "AAPL", "weight_pct": 50.0, "shares": None, "cost_basis": None},
        {"ticker": "NVDA", "weight_pct": 50.0, "shares": None, "cost_basis": None},
    ]


def test_saved_portfolio_is_private_and_replacement_is_atomic():
    saved = replace_default_holdings(9101, [
        {"ticker": "NVDA", "weight": 70},
        {"ticker": "AAPL", "weight": 30},
    ])
    assert [row["ticker"] for row in saved] == ["NVDA", "AAPL"]
    assert get_default_holdings(9102) == []

    replaced = replace_default_holdings(9101, [{"ticker": "MSFT", "weight": 100}])
    assert [row["ticker"] for row in replaced] == ["MSFT"]
    assert replaced[0]["weight_pct"] == pytest.approx(100.0)


def test_invalid_negative_weight_is_rejected_without_overwriting_saved_data():
    replace_default_holdings(9101, [{"ticker": "AAPL", "weight": 100}])
    with pytest.raises(ValueError):
        replace_default_holdings(9101, [{"ticker": "NVDA", "weight": -1}])
    assert [row["ticker"] for row in get_default_holdings(9101)] == ["AAPL"]
