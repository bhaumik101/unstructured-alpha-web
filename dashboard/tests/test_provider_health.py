"""Data Trust Center telemetry and genuine-data fallback contracts."""

from datetime import datetime, timezone

import pandas as pd

from utils import provider_health


def setup_function():
    provider_health._reset_for_tests()


def _series(date: str = "2026-07-21") -> pd.Series:
    return pd.Series([101.5], index=pd.to_datetime([date]), dtype=float)


def test_provider_aliases_and_health_are_sanitized():
    provider_health.record_provider_event(
        "yfinance", success=False, latency_ms=42.4, error_type="Timeout", status_code=503,
    )
    rows = {row["provider"]: row for row in provider_health.provider_health_snapshot()}
    assert rows["yahoo"]["state"] == "degraded"
    assert rows["yahoo"]["latency_ms"] == 42.4
    assert rows["yahoo"]["last_error"] == "Timeout"
    assert "url" not in rows["yahoo"]


def test_last_known_good_is_real_labeled_and_copied():
    original = _series()
    provider_health.remember_last_known_good("fred:test", original, provider="fred")
    original.iloc[0] = -999

    cached = provider_health.get_last_known_good("fred:test")
    assert float(cached.iloc[0]) == 101.5
    assert cached.attrs["data_state"] == "cached_live"
    assert cached.attrs["stale"] is True
    assert cached.attrs["provider"] == "fred"
    assert "fetch_error" not in cached.attrs


def test_empty_values_are_never_remembered():
    provider_health.remember_last_known_good(
        "fred:empty", pd.Series(dtype=float), provider="fred",
    )
    assert provider_health.get_last_known_good("fred:empty") is None


def test_freshness_respects_release_frequency():
    now = datetime(2026, 7, 22, tzinfo=timezone.utc)
    daily = {"data": _series("2026-07-21"), "config": {"source": "fred", "frequency": "daily"}}
    monthly = {"data": _series("2026-06-20"), "config": {"source": "fred", "frequency": "monthly"}}
    delayed = {"data": _series("2026-05-01"), "config": {"source": "fred", "frequency": "daily"}}

    assert provider_health.freshness_for_signal(daily, now=now)["state"] == "fresh"
    assert provider_health.freshness_for_signal(monthly, now=now)["state"] == "fresh"
    assert provider_health.freshness_for_signal(delayed, now=now)["state"] == "delayed"


def test_cached_live_state_takes_precedence_over_observation_age():
    data = _series("2026-07-21")
    data.attrs["data_state"] = "cached_live"
    signal = {"data": data, "config": {"source": "fred", "frequency": "daily"}}
    assert provider_health.freshness_for_signal(signal)["state"] == "cached_live"


def test_signal_dispatch_reuses_only_a_prior_genuine_observation(monkeypatch):
    from utils import fetchers

    live = _series()
    unavailable = pd.Series(dtype=float)
    unavailable.attrs.update({"fetch_error": True, "error_type": "Timeout"})
    responses = iter([live, unavailable])
    monkeypatch.setattr(fetchers, "fetch_price", lambda *args, **kwargs: next(responses))
    cfg = {"source": "yfinance", "series_id": "TEST"}

    first = fetchers.fetch_signal_series(cfg, "2026-01-01", "2026-07-22")
    second = fetchers.fetch_signal_series(cfg, "2026-01-01", "2026-07-22")

    assert first.attrs["data_state"] == "live"
    assert second.attrs["data_state"] == "cached_live"
    assert second.equals(first)
    assert not fetchers.is_unavailable(second)


def test_signal_dispatch_without_prior_live_data_stays_unavailable(monkeypatch):
    from utils import fetchers

    unavailable = pd.Series(dtype=float)
    unavailable.attrs.update({"fetch_error": True, "error_type": "Timeout"})
    monkeypatch.setattr(fetchers, "fetch_price", lambda *args, **kwargs: unavailable)
    result = fetchers.fetch_signal_series(
        {"source": "yfinance", "series_id": "NEVER_LIVE"},
        "2026-01-01", "2026-07-22",
    )
    assert fetchers.is_unavailable(result)
    assert result.empty


def test_public_refresh_copy_matches_shared_score_cache_source():
    from utils.product_metrics import SCORE_REFRESH_DESCRIPTION, SCORE_REFRESH_HOURS

    assert SCORE_REFRESH_HOURS == 6
    assert str(SCORE_REFRESH_HOURS) in SCORE_REFRESH_DESCRIPTION


def test_data_trust_center_all_sections_render(monkeypatch):
    from streamlit.testing.v1 import AppTest
    from tests.conftest import DASHBOARD_ROOT
    import utils.header as header

    # A standalone page AppTest has no st.navigation registry, so sidebar
    # page_link calls cannot resolve. The links themselves are covered by the
    # app routing tests; suppress them here to exercise every page section.
    monkeypatch.setattr(header.st, "page_link", lambda *args, **kwargs: None)
    at = AppTest.from_file(str(DASHBOARD_ROOT / "pages/48_Data_Trust.py"), default_timeout=120)
    at.run()
    rail = next((radio for radio in at.radio if radio.key == "data_trust_section_rail"), None)
    assert rail is not None

    # Signal Freshness is last because this Streamlit AppTest version treats a
    # segmented-control string default as characters on the *next* rerun.
    for section in ("Provider Health", "Methodology", "Signal Freshness"):
        rail.set_value(section).run()
        assert not at.exception, f"Data Trust Center failed in {section}: {list(at.exception)}"
        rail = next(radio for radio in at.radio if radio.key == "data_trust_section_rail")
