"""
Unit tests for utils/universe.py — the growing ticker universe (watchlist adds
+ daily big-name seeding). HERMETIC: stubs utils.config; the DB-backed calls
degrade gracefully to the static universe when no DB is present, which is
exactly what these tests exercise alongside the pure merge/normalise logic.
"""

import sys
import types

import pytest

_stub = types.ModuleType("utils.config")
_stub.TICKERS = {
    "AAPL": {"name": "Apple Inc.", "sector": "Technology"},
    "MSFT": {"name": "Microsoft", "sector": "Technology"},
    "XOM":  {"name": "Exxon", "sector": "Energy"},
}
_stub.SIGNALS = {}
_stub.CATEGORIES = {}
sys.modules.setdefault("utils.config", _stub)

from utils import universe as u  # noqa: E402


def test_normalize():
    assert u.normalize_ticker("  nvda ") == "NVDA"
    assert u.normalize_ticker("") == ""


def test_merge_universe():
    # dynamic 'aapl' dedups with static AAPL; result normalised + sorted
    assert u.merge_universe(u.TICKERS, ["nvda", " aapl "]) == ["AAPL", "MSFT", "NVDA", "XOM"]
    assert u.merge_universe({"A": 1, "B": 2}, []) == ["A", "B"]         # dict keys
    assert u.merge_universe(["A", "b"], ["c"]) == ["A", "B", "C"]       # iterable static


def test_resolve_meta():
    r = u.resolve_meta("AAPL")
    assert r["name"] == "Apple Inc." and r["sector"] == "Technology"
    r2 = u.resolve_meta("ZZZZ")   # unknown → yfinance unavailable → bare fallback
    assert r2["name"] == "ZZZZ" and r2["sector"] == ""


def test_add_to_universe_input_validation():
    assert u.add_to_universe("") is False                 # empty
    assert u.add_to_universe("ABCDEFGHIJKLMNOPQ") is False  # > 16 chars
    assert u.add_to_universe("AA@PL") is False             # illegal chars


def test_graceful_db_unavailable_fallbacks():
    assert u.get_dynamic_universe() == []
    assert u.get_full_universe() == ["AAPL", "MSFT", "XOM"]   # static only
    assert u.universe_size() == {"static": 3, "added": 0, "total": 3}
