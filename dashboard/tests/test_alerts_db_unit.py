"""
Unit tests for utils/alerts_db.py — the persistent SQLite layer behind
watchlist + alert storage. Each test gets its own temp DB file (via
monkeypatching DB_DIR/DB_PATH) so tests never share state or touch the
real data/alerts.db a developer might have on disk.
"""

import pytest

from utils import alerts_db


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test_alerts.db"
    monkeypatch.setattr(alerts_db, "DB_DIR", str(tmp_path))
    monkeypatch.setattr(alerts_db, "DB_PATH", str(db_path))
    alerts_db.init_db()
    yield


def test_init_db_is_idempotent():
    alerts_db.init_db()
    alerts_db.init_db()  # must not raise on a second call


def test_add_and_get_watchlist():
    alerts_db.add_to_watchlist("MSFT")
    alerts_db.add_to_watchlist("ccj", score_bull_threshold=70.0)  # lowercase input
    wl = alerts_db.get_watchlist()
    tickers = {row["ticker"] for row in wl}
    assert tickers == {"MSFT", "CCJ"}
    ccj_row = next(r for r in wl if r["ticker"] == "CCJ")
    assert ccj_row["score_bull_threshold"] == 70.0


def test_add_to_watchlist_upserts_thresholds():
    alerts_db.add_to_watchlist("GOOGL", score_bull_threshold=65.0)
    alerts_db.add_to_watchlist("GOOGL", score_bull_threshold=80.0)
    wl = alerts_db.get_watchlist()
    assert len(wl) == 1
    assert wl[0]["score_bull_threshold"] == 80.0


def test_remove_from_watchlist():
    alerts_db.add_to_watchlist("AAPL")
    assert alerts_db.is_watched("AAPL")
    alerts_db.remove_from_watchlist("aapl")  # lowercase input
    assert not alerts_db.is_watched("AAPL")
    assert alerts_db.get_watchlist() == []


def test_remove_from_watchlist_also_clears_alert_state():
    alerts_db.add_to_watchlist("NVDA")
    alerts_db.set_alert_state("NVDA", last_score=72.0)
    alerts_db.remove_from_watchlist("NVDA")
    assert alerts_db.get_alert_state("NVDA") is None


def test_is_watched_false_for_unwatched_ticker():
    assert not alerts_db.is_watched("ZZZZ")


def test_alert_state_roundtrip():
    assert alerts_db.get_alert_state("AVGO") is None
    alerts_db.set_alert_state("avgo", last_score=55.0, last_price=410.0)
    state = alerts_db.get_alert_state("AVGO")
    assert state["last_score"] == 55.0
    assert state["last_price"] == 410.0
    assert state["last_checked_at"]  # populated automatically


def test_set_alert_state_upserts():
    alerts_db.set_alert_state("HAL", last_score=50.0)
    alerts_db.set_alert_state("HAL", last_score=60.0)
    state = alerts_db.get_alert_state("HAL")
    assert state["last_score"] == 60.0


def test_create_and_get_alerts():
    alerts_db.create_alert("CCJ", "score_threshold", "Score crossed bullish", direction="bullish")
    alerts_db.create_alert("MSFT", "price_move", "Hit 52-week high", direction="bullish")
    alerts = alerts_db.get_alerts()
    assert len(alerts) == 2
    # most recent first
    assert alerts[0]["ticker"] == "MSFT"
    assert alerts[0]["is_read"] == 0


def test_count_unread_and_mark_all_read():
    alerts_db.create_alert("CCJ", "score_threshold", "msg1")
    alerts_db.create_alert("CCJ", "score_threshold", "msg2")
    assert alerts_db.count_unread() == 2
    alerts_db.mark_all_read()
    assert alerts_db.count_unread() == 0
    assert all(a["is_read"] == 1 for a in alerts_db.get_alerts())


def test_mark_read_single_alert():
    id1 = alerts_db.create_alert("CCJ", "score_threshold", "msg1")
    alerts_db.create_alert("CCJ", "score_threshold", "msg2")
    alerts_db.mark_read(id1)
    assert alerts_db.count_unread() == 1


def test_get_alerts_unread_only_filter():
    id1 = alerts_db.create_alert("CCJ", "score_threshold", "msg1")
    alerts_db.create_alert("CCJ", "score_threshold", "msg2")
    alerts_db.mark_read(id1)
    unread = alerts_db.get_alerts(unread_only=True)
    assert len(unread) == 1
    assert unread[0]["message"] == "msg2"


def test_get_alerts_respects_limit():
    for i in range(5):
        alerts_db.create_alert("CCJ", "score_threshold", f"msg{i}")
    assert len(alerts_db.get_alerts(limit=3)) == 3


def test_clear_all_alerts():
    alerts_db.create_alert("CCJ", "score_threshold", "msg1")
    alerts_db.clear_all_alerts()
    assert alerts_db.get_alerts() == []
    assert alerts_db.count_unread() == 0
