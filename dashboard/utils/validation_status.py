# utils/validation_status.py
# Unstructured Alpha — Consolidated Model Validation Status
#
# WHY THIS MODULE EXISTS: every score this product computes (macro signals,
# insider activity, short interest, 13F, the Confluence/Supercycle
# composites) has gone through a DIFFERENT amount and kind of real
# validation -- some backtested with real significance numbers, some
# explicitly NOT validated and documented as such, some validated only
# per-ticker on demand rather than as a single global number. This module
# is the single, honest source of truth for "how validated is X, exactly,"
# pulling from the actual scoring/backtest functions rather than
# restating anything from memory -- every claim below traces back to a
# real function call or a docstring that was re-read at the time this was
# written, not approximated.
#
# backtest_all_macro_signals() was moved here from pages/8_About.py
# (previously a page-local function) so the new Model Validation
# Dashboard (pages/11_Model_Validation.py) and the About page's signal
# library both call the exact same implementation -- duplicating this
# logic across two pages would risk them silently drifting out of sync
# with each other, which is exactly the kind of inconsistency a
# "validation" feature cannot afford to have.

from datetime import datetime, timedelta
from typing import Dict

import streamlit as st

from utils.config import SIGNALS
from utils.fetchers import fetch_signal_series, fetch_price
from utils.analysis import compute_backtested_pcs


@st.cache_data(ttl=86400, show_spinner=False)
def backtest_all_macro_signals(_v: int = 2) -> Dict[str, dict]:
    """
    Backtest every macro/FRED-style signal's PCS against up to 5 of its
    relevant tickers (not just the first one) so a signal that only
    correlates with one ticker doesn't get an inflated, falsely-broad PCS.
    Cached for 24h since this is a real-data validation pass over ~38
    signals x up to 5 tickers each, not a cheap live score.

    Returns {signal_id: compute_backtested_pcs() result}. Each result has
    "backtested": False (with pcs=None) when there wasn't enough
    overlapping data to test at all -- callers must treat that as "not
    validated," never silently substitute a default.
    """
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")

    out = {}
    for sig_id, cfg in SIGNALS.items():
        try:
            sig_series = fetch_signal_series(cfg, start, end)
            test_tickers = (cfg.get("relevant_tickers") or [])[:5]
            price_series_list = [fetch_price(t, start, end) for t in test_tickers]
            out[sig_id] = compute_backtested_pcs(
                sig_series, price_series_list,
                lag_weeks=cfg.get("lag_weeks", 0), tickers=test_tickers,
            )
        except Exception:
            out[sig_id] = {"pcs": None, "backtested": False, "n_tested": 0,
                            "significance_rate": 0.0, "avg_abs_r": 0.0, "details": []}
    return out


def get_static_validation_summary() -> list:
    """
    Validation status for every score category that ISN'T a per-signal
    macro backtest (those come from backtest_all_macro_signals() instead,
    computed live/cached, not hand-written here). These five entries are
    deliberately NOT computed live -- they're either a one-time documented
    finding (Confluence/Supercycle's walk-forward backtest, already
    disclosed in utils/analysis.py's docstrings) or a structural fact about
    what methodology applies and why (insider/short-interest's per-ticker,
    on-demand validated scan; 13F's deliberate exclusion).

    Every number quoted here was copied verbatim from the actual source
    docstring it describes (utils/analysis.py's compute_confluence() and
    compute_supercycle_score(), utils/lead_time_research.py's module
    docstring) at the time this was written -- not approximated or
    recalled from memory. If those backtests are ever re-run with
    different results, this summary needs updating to match, not the
    other way around.
    """
    return [
        {
            "category": "Confluence Score (per-ticker macro composite)",
            "status": "Backtested — NOT validated",
            "detail": (
                "Walk-forward backtest found no statistically significant relationship between the "
                "score and forward returns, pooled across 6 tickers. High conviction means the "
                "signals agree with each other right now — it does not yet mean they're right."
            ),
            "source": "utils/analysis.py — compute_confluence() docstring",
        },
        {
            "category": "Power Supercycle Score",
            "status": "Backtested — NOT validated",
            "detail": (
                "Walk-forward backtest (6 tickers spanning the thesis — CEG, VST, NEE, ETN, VRT, PWR — "
                "~19 monthly checkpoints, pooled) found no statistically significant relationship with "
                "1/2/3-month forward returns in either direction (all |r| < 0.07, p > 0.5 pooled). Two "
                "of the six tickers showed a significant NEGATIVE relationship in isolation before "
                "pooling, driven by the two most narrative-extended names, where a high reading "
                "coincided with a cyclical top rather than leading one."
            ),
            "source": "utils/analysis.py — compute_supercycle_score() docstring",
        },
        {
            "category": "Insider Activity (Form 4 open-market buys/sells)",
            "status": "Validated methodology available — per-ticker, on demand",
            "detail": (
                "Has a real out-of-sample-tested, multiple-comparisons-corrected lead-time scan "
                "(Bonferroni correction across lags tested; best lag fit on the earlier ~70% of "
                "history, then re-tested on the held-out, more recent ~30% it never saw). This is NOT "
                "a single global number — run it for a specific ticker on that ticker's Deep Dive page "
                "(\"Run validated lead-time scan\"), since whether this signal leads price, and by how "
                "long, can genuinely differ by ticker and sector."
            ),
            "source": "utils/lead_time_research.py — lag_scan_with_validation()",
        },
        {
            "category": "Short Interest (FINRA consolidated)",
            "status": "Validated methodology available — per-ticker, on demand",
            "detail": (
                "Same validated lead-time methodology as Insider Activity above, run on demand per "
                "ticker. Sample size is the real constraint here: FINRA's API caps results at 50 rows "
                "and reports bi-monthly, so even 2 years of history is roughly 48 data points before "
                "weekly resampling — the Signal Reliability Score's sample-size component reflects "
                "this directly rather than hiding it."
            ),
            "source": "utils/lead_time_research.py — lag_scan_with_validation()",
        },
        {
            "category": "13F Institutional Positioning",
            "status": "Deliberately NOT lag-scanned",
            "detail": (
                "13F filings are quarterly — a few years of history is only 8-12 data points, not "
                "enough to honestly fit and validate a lead-time lag. Rather than fit a curve to "
                "8 points and call it a finding, this signal is excluded from the validated lead-time "
                "scan entirely. The audit trail (source filing links) is still available on each "
                "ticker's Deep Dive page."
            ),
            "source": "utils/lead_time_research.py — module docstring",
        },
    ]
