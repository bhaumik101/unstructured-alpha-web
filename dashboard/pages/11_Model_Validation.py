"""
Page 11 — Model Validation Dashboard
Consolidates the validation status of EVERY score this product computes
into one place: every macro/FRED-style signal's real backtest result
(significance rate, average |r|, sample size), plus the per-ticker
differentiator signals and composite scores, each described with exactly
what's been validated, what hasn't, and why -- pulling from
utils/validation_status.py rather than restating anything from memory.

This page exists because it's the actual differentiator this product can
defend: TipRanks' Smart Score, Seeking Alpha's Quant Rating, and similar
composite scores disclose none of their validation status. A platform
that shows "here's exactly how well-supported this number is, including
when it ISN'T" is a different kind of product, not a fancier version of
the same one. That only works if every claim on this page is genuinely
accurate -- nothing here is allowed to be approximated or rounded up.
"""

import pandas as pd
import streamlit as st

from utils.header import render_header, render_sidebar_base
from utils.config import SIGNALS, CATEGORIES
from utils.validation_status import backtest_all_macro_signals, get_static_validation_summary

st.set_page_config(page_title="Model Validation — UA", layout="wide")
render_header("Model Validation Dashboard")
render_sidebar_base()

st.markdown("# Model Validation Dashboard")
st.markdown("""
<div style="background:#FFF8E7;border-radius:6px;padding:14px 18px;border:1px solid #E8D9A8;
            font-size:0.9rem;color:#5D4426;margin-bottom:16px;font-family:Georgia,serif;">
<b>What this page is for:</b> every score on this site traces back to a real, checkable validation
status — backtested with real significance numbers, validated per-ticker on demand, or explicitly
<b>not</b> validated and documented as to why. Most platforms that show a composite "smart score"
disclose none of this. This page is the single place that does, including for the cases where the
honest answer is "this hasn't held up" — that's the point, not an embarrassment to hide.
</div>
""", unsafe_allow_html=True)

# ── Composite scores + differentiator signals ──────────────────────────────────
st.markdown('<div class="section-header">COMPOSITE SCORES & DIFFERENTIATOR SIGNALS</div>', unsafe_allow_html=True)

_STATUS_COLOR = {
    "Backtested — NOT validated": "#7B1010",
    "Validated methodology available — per-ticker, on demand": "#B8860B",
    "Deliberately NOT lag-scanned": "#5D4426",
}

for entry in get_static_validation_summary():
    color = _STATUS_COLOR.get(entry["status"], "#1C2B4A")
    st.markdown(f"""
    <div style="border-left:4px solid {color};background:#FAF7F0;border-radius:4px;
                padding:12px 16px;margin-bottom:10px;">
        <div style="font-weight:700;color:#1C2B4A;font-size:1.0rem;">{entry['category']}</div>
        <div style="color:{color};font-weight:700;font-size:0.85rem;margin:2px 0 6px 0;">{entry['status']}</div>
        <div style="color:#1A1612;font-size:0.88rem;">{entry['detail']}</div>
        <div style="color:#8B7355;font-size:0.75rem;margin-top:6px;font-style:italic;">Source: {entry['source']}</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ── Macro signal library backtest ────────────────────────────────────────────
st.markdown('<div class="section-header">MACRO SIGNAL LIBRARY — REAL BACKTEST RESULTS</div>', unsafe_allow_html=True)
st.caption(
    f"All {len(SIGNALS)} macro/FRED-style signals, tested against up to 5 of each signal's relevant "
    "tickers (not just one) so a signal that only works on a single name doesn't get credit for broad "
    "predictive power. This is the SAME backtest available on the About page — one shared "
    "implementation, so the two pages can't silently disagree with each other."
)

run_backtest = st.button("Run Live Backtest (tests real correlation + significance)", key="run_pcs_backtest_validation_page")

backtest_results = {}
if run_backtest:
    with st.spinner("Backtesting every signal against real price history — this fetches live data, may take a minute…"):
        backtest_results = backtest_all_macro_signals()
    n_validated = sum(1 for r in backtest_results.values() if r["backtested"])
    n_significant = sum(
        1 for r in backtest_results.values()
        if r["backtested"] and r.get("significance_rate", 0) >= 0.5
    )
    st.success(
        f"Backtest complete: {n_validated} of {len(SIGNALS)} signals had enough overlapping data to "
        f"validate. {n_significant} of those showed significant correlation (p<0.05) on at least half "
        f"of the tickers tested. The rest are shown as \"unvalidated\" below, not silently hidden."
    )

rows = []
for sig_id, cfg in SIGNALS.items():
    cat = CATEGORIES.get(cfg["category"], {})
    bt = backtest_results.get(sig_id, {})
    if bt.get("backtested"):
        validation = (
            f"{bt['significance_rate']*100:.0f}% significant, avg |r|={bt['avg_abs_r']:.2f} "
            f"(n={bt['n_tested']} tickers)"
        )
        validated_flag = "Yes"
    else:
        validation = "Not yet run — click \"Run Live Backtest\" above"
        validated_flag = "Not run"

    rows.append({
        "Signal": cfg["name"],
        "Category": cat.get("name", cfg["category"]),
        "Validated?": validated_flag,
        "Backtest Result": validation,
        "Lead Time": f"~{cfg['lag_weeks']}w",
    })

st.dataframe(
    pd.DataFrame(rows), use_container_width=True, hide_index=True,
    column_config={
        "Backtest Result": st.column_config.TextColumn(
            "Backtest Result",
            help="Significance rate and average |r| from the live backtest, when run -- "
                 "not run yet shows plainly as such, never a placeholder number.",
        ),
    },
)

st.markdown("""
<div class="disclaimer">
<b>Not financial advice.</b> Validation status describes how a score's methodology has performed
against historical data — it is not a guarantee of future performance, and a "validated" signal can
still be wrong on any individual occasion. Do your own research before making any investment decision.
</div>
""", unsafe_allow_html=True)
