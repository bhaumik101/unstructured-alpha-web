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
from utils.validation_status import validate_all_macro_signals, get_static_validation_summary

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

# ── Macro signal library — universal lag validation ─────────────────────────
st.markdown('<div class="section-header">MACRO SIGNAL LIBRARY — VALIDATED LEAD-TIME RESULTS</div>', unsafe_allow_html=True)
st.caption(
    f"All {len(SIGNALS)} macro/FRED-style signals, now run through the SAME rigorous methodology "
    "originally built only for insider activity and short interest: an out-of-sample split, "
    "Bonferroni correction across every lag tested, and cross-ticker pooled confirmation -- "
    "rolled up into one transparent Signal Reliability Score per signal (utils/lead_time_research.py). "
    "Every signal held to the same bar, no exceptions."
)

run_validated = st.button(
    "Run Universal Lag Validation (out-of-sample + corrected, every signal)",
    key="run_validated_lag_scan_all_signals",
)

validated_results = {}
if run_validated:
    with st.spinner(
        "Running the validated lag-scan for every signal against up to 5 tickers each — "
        "this is heavier than a simple correlation pass, may take a minute or two…"
    ):
        validated_results = validate_all_macro_signals()
    n_scored = sum(1 for r in validated_results.values() if not r["validation"].get("error"))
    n_reliable = sum(1 for r in validated_results.values() if r["reliability"]["score"] >= 70)
    st.success(
        f"Validation complete: {n_scored} of {len(SIGNALS)} signals had enough data to score. "
        f"{n_reliable} scored 70+ (\"Reasonably well-supported\"). The rest are shown exactly as "
        f"scored below, including the weak ones — that's the point of this page."
    )

rows = []
for sig_id, cfg in SIGNALS.items():
    cat = CATEGORIES.get(cfg["category"], {})
    vr = validated_results.get(sig_id)
    if vr is None:
        reliability_str  = "Not yet run"
        survives_str     = "—"
        holds_oos_str     = "—"
        best_lag_str      = "—"
    elif vr["validation"].get("error"):
        reliability_str  = "Insufficient data"
        survives_str     = "—"
        holds_oos_str     = "—"
        best_lag_str      = "—"
    else:
        rel = vr["reliability"]
        v   = vr["validation"]
        reliability_str = f"{rel['score']}/100 — {rel['label']}"
        survives_str    = "Yes" if v.get("survives_correction") else "No"
        holds_oos_str    = "Yes" if v.get("holds_out_of_sample") else "No"
        best_lag_str     = f"{v.get('best_lag', '—')}w"

    rows.append({
        "Signal": cfg["name"],
        "Category": cat.get("name", cfg["category"]),
        "Reliability Score": reliability_str,
        "Survives Correction": survives_str,
        "Holds Out-of-Sample": holds_oos_str,
        "Best Lag (in-sample)": best_lag_str,
    })

st.dataframe(
    pd.DataFrame(rows), use_container_width=True, hide_index=True,
    column_config={
        "Reliability Score": st.column_config.TextColumn(
            "Reliability Score",
            help="0-100, from utils/lead_time_research.py's compute_signal_reliability_score(): "
                 "corrected significance + out-of-sample hold-up + sample size + cross-ticker pooling.",
        ),
        "Survives Correction": st.column_config.TextColumn(
            "Survives Correction", help="Best in-sample lag's p-value beats alpha/n_lags (Bonferroni).",
        ),
        "Holds Out-of-Sample": st.column_config.TextColumn(
            "Holds Out-of-Sample",
            help="That same lag, re-tested on the held-out ~30% of history it was never fit to.",
        ),
    },
)

with st.expander("How is this different from the simpler backtest on the About page?"):
    st.markdown(
        "The About page's signal library still shows a simpler, same-sample significance test "
        "(`compute_backtested_pcs` — fast, tests against up to 5 tickers, no out-of-sample split or "
        "multiple-comparisons correction). It's a reasonable quick overview but, on its own, will show "
        "more signals looking \"significant\" than actually survive the stricter bar above — that gap "
        "is expected and is exactly why this page exists. Live confluence-score weighting "
        "(`utils/ticker_score.py`) is unaffected by either backtest; it uses its own real-time, "
        "per-ticker correlation regardless of what either validation pass finds."
    )

st.markdown("""
<div class="disclaimer">
<b>Not financial advice.</b> Validation status describes how a score's methodology has performed
against historical data — it is not a guarantee of future performance, and a "validated" signal can
still be wrong on any individual occasion. Do your own research before making any investment decision.
</div>
""", unsafe_allow_html=True)
