"""Tests for utils.time_stops — expected thesis window and decay."""
from datetime import date, timedelta

from utils import time_stops as ts
from utils.config import SIGNALS

_SHORT = [s for s, c in SIGNALS.items() if float(c.get("lag_weeks") or 4) <= 2][:3]
_LONG = [s for s, c in SIGNALS.items() if float(c.get("lag_weeks") or 4) >= 12][:2]


# ── which signals form the thesis ────────────────────────────────────────────
def test_driving_signals_follow_the_case():
    conf = {"case": "BULL",
            "bull_signals": [{"id": "a"}, {"id": "b"}],
            "bear_signals": [{"id": "z"}]}
    assert ts.driving_signal_ids(conf) == ["a", "b"]
    conf["case"] = "BEAR"
    assert ts.driving_signal_ids(conf) == ["z"]


def test_driving_signals_neutral_falls_back_to_larger_side():
    conf = {"case": "NEUTRAL",
            "bull_signals": [{"id": "a"}],
            "bear_signals": [{"id": "x"}, {"id": "y"}]}
    assert ts.driving_signal_ids(conf) == ["x", "y"]


def test_driving_signals_never_raises():
    for junk in (None, {}, {"case": None}, {"bull_signals": None}):
        assert isinstance(ts.driving_signal_ids(junk), list)


# ── horizon ──────────────────────────────────────────────────────────────────
def test_horizon_uses_median_not_mean():
    """One 52-week outlier must not stretch a short thesis to a year."""
    if not _SHORT:
        return
    ids = _SHORT + [s for s, c in SIGNALS.items() if float(c.get("lag_weeks") or 4) >= 52][:1]
    h = ts.thesis_horizon(ids)
    assert h["median_weeks"] <= 4, "median must resist the long-tail outlier"
    assert h["max_weeks"] >= 52 or h["n"] == len(ids)


def test_horizon_short_signals_give_short_window():
    if not _SHORT:
        return
    h = ts.thesis_horizon(_SHORT)
    assert h["median_weeks"] <= 2
    assert h["expected_by"] > ts._today()


def test_horizon_long_signals_give_long_window():
    if not _LONG:
        return
    h = ts.thesis_horizon(_LONG)
    assert h["median_weeks"] >= 12


def test_horizon_empty_invents_nothing():
    h = ts.thesis_horizon([])
    assert h["n"] == 0 and h["median_weeks"] is None and h["expected_by"] is None
    assert h["label"] == ""


def test_horizon_unknown_signal_uses_default_lag():
    h = ts.thesis_horizon(["totally_unknown_signal"])
    assert h["median_weeks"] == ts.DEFAULT_LAG_WEEKS


def test_horizon_note_frames_it_as_a_guide_not_a_forecast():
    h = ts.thesis_horizon(_SHORT or ["x"])
    note = h["note"].lower()
    assert "not a forecast" in note and "stop" in note


# ── decay ────────────────────────────────────────────────────────────────────
def test_decay_active_within_window():
    today = ts._today()
    d = ts.decay_status(today - timedelta(weeks=2), horizon_weeks=8)
    assert d["status"] == ts.STATUS_ACTIVE
    assert d["pct_elapsed"] == 25.0


def test_decay_maturing_just_past_window():
    today = ts._today()
    d = ts.decay_status(today - timedelta(weeks=9), horizon_weeks=8)
    assert d["status"] == ts.STATUS_MATURING


def test_decay_decayed_well_past_window():
    today = ts._today()
    d = ts.decay_status(today - timedelta(weeks=13), horizon_weeks=8)
    assert d["status"] == ts.STATUS_DECAYED
    assert "decayed" in d["label"].lower()


def test_decay_accepts_iso_string_dates():
    today = ts._today()
    iso = (today - timedelta(weeks=13)).strftime("%Y-%m-%d")
    assert ts.decay_status(iso, horizon_weeks=8)["status"] == ts.STATUS_DECAYED


def test_decay_never_claims_stale_on_bad_data():
    for bad in (None, "not-a-date", 12345, ""):
        d = ts.decay_status(bad, horizon_weeks=8)
        assert d["status"] == ts.STATUS_ACTIVE and d["pct_elapsed"] is None
    # missing/zero horizon must not divide by zero or mark decayed
    assert ts.decay_status(ts._today(), horizon_weeks=0)["status"] == ts.STATUS_ACTIVE
    assert ts.decay_status(ts._today(), horizon_weeks=None)["status"] == ts.STATUS_ACTIVE


def test_decay_future_event_date_not_negative():
    d = ts.decay_status(ts._today() + timedelta(weeks=3), horizon_weeks=8)
    assert d["elapsed_weeks"] == 0.0


# ── rendering ────────────────────────────────────────────────────────────────
def test_horizon_html_empty_when_nothing_to_say():
    assert ts.horizon_html(None) == ""
    assert ts.horizon_html({"median_weeks": None}) == ""


def test_horizon_html_renders_label():
    h = ts.thesis_horizon(_SHORT or ["x"])
    html = ts.horizon_html(h)
    assert "Thesis window" in html and "⏱" in html
