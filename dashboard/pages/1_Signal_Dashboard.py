"""
Page 1 — Signal Dashboard
Clean, accessible signal library with Simple / Pro mode toggle.
Tab-based category filter. Searchable signal list.
"""

from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.config import CATEGORIES, SIGNALS, TICKERS
from utils.fetchers import fetch_signal_series, is_synthetic
from utils.analysis import score_signal
from utils.header import render_header, render_sidebar_base, ticker_chips, render_synthetic_data_banner
from utils.score_history import get_signal_flips

st.set_page_config(page_title="Signal Dashboard — UA", layout="wide")
render_header("Signal Dashboard")
render_sidebar_base()

END   = datetime.now().strftime("%Y-%m-%d")
START = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")

STATUS_COLOR = {"bullish": "#1B5E20", "bearish": "#7B1010", "neutral": "#8B7355", "insufficient_data": "#9E9E8E"}
STATUS_LABEL = {"bullish": "🟢 Bullish", "bearish": "🔴 Bearish", "neutral": "🟡 Neutral", "insufficient_data": "⚪ No Data"}
STATUS_SYM   = {"bullish": "▲", "bearish": "▼", "neutral": "●", "insufficient_data": "○"}


@st.cache_data(ttl=3600, show_spinner=False)
def load_all_signals(_v: int = 5):
    results = {}
    for sig_id, cfg in SIGNALS.items():
        try:
            s = fetch_signal_series(cfg, START, END)
            scored = score_signal(s, inverse=cfg.get("inverse", False))
            results[sig_id] = {**scored, "config": cfg, "data": s, "is_synthetic": is_synthetic(s)}
        except Exception:
            results[sig_id] = {
                "score": 50, "status": "insufficient_data", "config": cfg,
                "data": pd.Series(dtype=float), "z_score": 0,
                "percentile": 50, "current": float("nan"), "deviation_pct": 0,
                "trend_4w_pct": 0, "is_synthetic": False,
            }
    return results


_load_ts = datetime.now().strftime("%I:%M %p")
_hdr_col, _ref_col = st.columns([6, 1])
with _hdr_col:
    st.caption(f"Data cached up to 1 hour · computed ~{_load_ts}")
with _ref_col:
    if st.button("↺ Refresh", key="sd_refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with st.spinner("Loading signal data…"):
    all_signals = load_all_signals()

render_synthetic_data_banner(
    sum(1 for sv in all_signals.values() if sv.get("is_synthetic")),
    len(all_signals),
)

# ── Mode Toggle ───────────────────────────────────────────────────────────────
col_mode, col_spacer = st.columns([2, 5])
with col_mode:
    mode = st.radio(
        "View mode",
        ["Simple", "Pro"],
        horizontal=True,
        index=0,
        help="Simple: plain-English signals for any investor. Pro: full z-score and correlation data.",
        key="dash_mode",
    )

st.markdown("")

# ── Category Tabs ─────────────────────────────────────────────────────────────
cat_labels  = ["All"] + [v['name'] for v in CATEGORIES.values()]
cat_keys    = [None]     + list(CATEGORIES.keys())
cat_sel_idx = st.radio(
    "Category",
    cat_labels,
    index=0,
    horizontal=True,
    key="dash_cat",
    label_visibility="collapsed",
)
selected_cat = cat_keys[cat_labels.index(cat_sel_idx)]

# ── Search ────────────────────────────────────────────────────────────────────
search_term = st.text_input(
    "Search signals",
    placeholder="e.g. trucking, uranium, yield…",
    label_visibility="visible",
    key="dash_search",
).strip().lower()

# ── Filtered Signals — sorted by significance (most bullish/bearish first) ────
visible_signals = sorted(
    [
        (sid, sv) for sid, sv in all_signals.items()
        if (selected_cat is None or sv["config"].get("category") == selected_cat)
        and (not search_term or search_term in sv["config"]["name"].lower()
             or search_term in sv["config"].get("description", "").lower())
    ],
    key=lambda x: abs(x[1].get("score", 50) - 50),
    reverse=True,
)

# ── Summary Banner ────────────────────────────────────────────────────────────
_vals     = [sv for _, sv in visible_signals]
bull_n    = sum(1 for v in _vals if v.get("status") == "bullish")
bear_n    = sum(1 for v in _vals if v.get("status") == "bearish")
neut_n    = sum(1 for v in _vals if v.get("status") == "neutral")
total_n   = len(_vals)

scope_lbl = (cat_sel_idx if selected_cat else "All Categories")
if search_term:
    scope_lbl = f'Search: "{search_term}"'

# Overall market temperature
if total_n > 0:
    bull_pct = bull_n / total_n * 100
    temp_color = "#1B5E20" if bull_pct >= 60 else ("#7B1010" if bull_pct <= 35 else "#8B7355")
    temp_label = "Risk-On 🟢" if bull_pct >= 60 else ("Risk-Off 🔴" if bull_pct <= 35 else "Mixed 🟡")
else:
    temp_color, temp_label = "#8B7355", "No Data"

st.markdown(f"""
<div style="background:#F0EBE1;border-radius:8px;padding:16px 20px;border:1px solid #D4C9B0;
            border-left:5px solid {temp_color};font-family:Georgia,serif;margin-bottom:16px;">
    <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
        <div>
            <div style="font-size:0.72rem;color:#9E9E8E;letter-spacing:0.08em;text-transform:uppercase;">
                MARKET TEMPERATURE — {scope_lbl}
            </div>
            <div style="font-size:1.5rem;font-weight:800;color:{temp_color};margin-top:2px;">{temp_label}</div>
        </div>
        <div style="display:flex;gap:28px;text-align:center;">
            <div>
                <div style="font-size:1.6rem;font-weight:700;color:#1B5E20;">{bull_n}</div>
                <div style="font-size:0.72rem;color:#9E9E8E;">Bullish</div>
            </div>
            <div>
                <div style="font-size:1.6rem;font-weight:700;color:#7B1010;">{bear_n}</div>
                <div style="font-size:0.72rem;color:#9E9E8E;">Bearish</div>
            </div>
            <div>
                <div style="font-size:1.6rem;font-weight:700;color:#8B7355;">{neut_n}</div>
                <div style="font-size:0.72rem;color:#9E9E8E;">Neutral</div>
            </div>
            <div>
                <div style="font-size:1.6rem;font-weight:700;color:#1C2B4A;">{total_n}</div>
                <div style="font-size:0.72rem;color:#9E9E8E;">Total</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Signal Flips (since yesterday) ───────────────────────────────────────────
try:
    _flips = get_signal_flips(days_back=1)
    if _flips:
        _FLIP_COLOR = {
            "bullish":  "#1B5E20",
            "bearish":  "#7B1010",
            "neutral":  "#8B7355",
            "insufficient_data": "#9E9E8E",
        }
        _FLIP_SYM = {"bullish": "▲", "bearish": "▼", "neutral": "●", "insufficient_data": "○"}

        st.markdown(
            f'<div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.08em;'
            f'color:#8B7355;margin-bottom:4px;font-family:Georgia,serif;">'
            f'⚡ {len(_flips)} signal{"s" if len(_flips) != 1 else ""} changed status since yesterday'
            f'</div>',
            unsafe_allow_html=True,
        )
        _flip_cols = st.columns(min(len(_flips), 4))
        for _fi, _flip in enumerate(_flips[:4]):
            _fsid   = _flip["signal_id"]
            _fname  = SIGNALS.get(_fsid, {}).get("name", _fsid)
            _from_c = _FLIP_COLOR.get(_flip["from_status"], "#9E9E9E")
            _to_c   = _FLIP_COLOR.get(_flip["to_status"],   "#9E9E9E")
            _from_s = _FLIP_SYM.get(_flip["from_status"],  "●")
            _to_s   = _FLIP_SYM.get(_flip["to_status"],    "●")
            _to_lbl = _flip["to_status"].replace("_", " ").title()
            with _flip_cols[_fi]:
                st.markdown(
                    f'<div style="background:#FAFAFA;border-radius:6px;padding:8px 12px;'
                    f'border:1px solid #E0E0E0;border-top:3px solid {_to_c};'
                    f'margin-bottom:8px;font-family:Georgia,serif;">'
                    f'<div style="font-size:0.75rem;font-weight:700;color:#1A1612;'
                    f'line-height:1.3;margin-bottom:4px;">{_fname[:36]}</div>'
                    f'<div style="font-size:0.80rem;">'
                    f'<span style="color:{_from_c};">{_from_s} {_flip["from_status"].title()}</span>'
                    f' <span style="color:#9E9E8E;">→</span> '
                    f'<span style="color:{_to_c};font-weight:700;">{_to_s} {_to_lbl}</span>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        if len(_flips) > 4:
            st.caption(f"+ {len(_flips) - 4} more flips — see Today's Brief for the full list.")
        st.markdown("")
except Exception:
    pass  # Never crash the dashboard if flip history isn't available yet

# ── Theme Context Banner ──────────────────────────────────────────────────────
st.markdown("""
<div style="background:#EEF3FA;border-radius:8px;padding:14px 20px;
            border-left:5px solid #1C2B4A;margin-bottom:14px;font-family:Georgia,serif;">
    <div style="font-size:0.75rem;color:#1C2B4A;font-weight:700;letter-spacing:0.06em;
                text-transform:uppercase;margin-bottom:4px;">
        What This Dashboard Tracks
    </div>
    <div style="font-size:0.82rem;color:#3A3530;line-height:1.6;">
        Core themes: <b>Natural Gas · Copper · AI Infrastructure · Quantum Computing</b>
        — the four forces reshaping the global economy.
        But every signal here also <b>flows through to mainstream stocks</b>:
        rising copper lifts industrials, energy capex flows move S&amp;P 500 utilities,
        AI power demand reshapes the whole grid sector.
        Any ticker in the Screener or Deep Dive shows you exactly how these forces hit it.
    </div>
</div>
""", unsafe_allow_html=True)

if not visible_signals:
    st.info("No signals match your filter. Try broadening the category or search term.")
    st.stop()

# ── Signal Cards ──────────────────────────────────────────────────────────────
COLS = 3
for row_start in range(0, len(visible_signals), COLS):
    row_items = visible_signals[row_start : row_start + COLS]
    cols = st.columns(COLS)

    for col, (sig_id, sv) in zip(cols, row_items):
        cfg    = sv["config"]
        status = sv.get("status", "neutral")
        score  = sv.get("score", 50)
        dev    = sv.get("deviation_pct", 0)
        trend  = sv.get("trend_4w_pct", 0)
        cat    = CATEGORIES.get(cfg.get("category", "macro"), {})
        border = STATUS_COLOR.get(status, "#9E9E9E")
        sym    = STATUS_SYM.get(status, "●")
        lbl    = STATUS_LABEL.get(status, "●")
        trend_arrow = "↑" if trend > 1 else ("↓" if trend < -1 else "→")

        with col:
            try:
                if mode == "Simple":
                    # ── SIMPLE card: big status + plain English ──────────────
                    _dev_abs   = abs(dev) if dev == dev else 0.0   # guard NaN
                    _lbl_text  = lbl.split(" ", 1)[-1] if " " in lbl else lbl
                    _cat_icon  = cat.get("icon", "")
                    _cat_name  = cat.get("name", "")
                    _sig_name  = cfg["name"][:44]

                    if status == "bullish":
                        _bottom_note = f"Running <b>{_dev_abs:.0f}% above</b> its 52-week average — positive signal."
                    elif status == "bearish":
                        _bottom_note = f"Running <b>{_dev_abs:.0f}% below</b> its 52-week average — negative signal."
                    elif status == "insufficient_data":
                        _bottom_note = "Not enough data yet — check back as more history accumulates."
                    else:
                        _bottom_note = "Within normal range — no clear directional edge right now."

                    _lag_weeks = cfg.get("lag_weeks", 0)
                    _lag_html  = (
                        f"<br><span style='color:#8B7355;font-size:0.72rem;'>"
                        f"Leads related stocks by ~{_lag_weeks} weeks.</span>"
                        if _lag_weeks > 0 else ""
                    )

                    st.markdown(
                        f'<div style="background:#FAFAFA;border-radius:8px;padding:14px 16px;'
                        f'border-left:4px solid {border};border:1px solid #E0E0E0;'
                        f'margin-bottom:10px;font-family:Georgia,serif;min-height:140px;">'
                        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">'
                        f'<div style="font-size:0.78rem;font-weight:700;color:#1A1612;line-height:1.3;flex:1;">{_sig_name}</div>'
                        f'<div style="font-size:1.0rem;font-weight:800;color:{border};'
                        f'background:{border}18;border-radius:4px;padding:2px 8px;'
                        f'white-space:nowrap;margin-left:8px;">{sym} {_lbl_text}</div>'
                        f'</div>'
                        f'<div style="font-size:0.78rem;color:#4A4440;line-height:1.5;margin-bottom:6px;">'
                        f'{_bottom_note}{_lag_html}'
                        f'</div>'
                        f'<div style="font-size:0.68rem;color:#8B7355;">{_cat_icon} {_cat_name}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                else:
                    # ── PRO card: full metrics ───────────────────────────────
                    z_score  = sv.get("z_score", 0.0)
                    pct_rank = sv.get("percentile", 50.0)
                    _dev_fmt = f"{dev:+.1f}" if dev == dev else "n/a"
                    _z_fmt   = f"{z_score:.1f}" if z_score == z_score else "n/a"
                    _trend_fmt = f"{trend:+.1f}" if trend == trend else "n/a"
                    _cat_icon  = cat.get("icon", "")
                    _cat_name  = cat.get("name", "").upper()

                    st.markdown(
                        f'<div style="background:#F0EBE1;border-radius:6px;padding:14px 16px;'
                        f'border-left:4px solid {border};border:1px solid #D4C9B0;'
                        f'margin-bottom:10px;font-family:Georgia,serif;min-height:140px;">'
                        f'<div style="font-size:0.68rem;color:#9E9E8E;letter-spacing:0.03em;margin-bottom:2px;">'
                        f'{_cat_icon} {_cat_name} · PCS {cfg["pcs"]}/10</div>'
                        f'<div style="font-weight:700;font-size:0.88rem;color:#1A1612;margin-bottom:8px;line-height:1.3;">'
                        f'{cfg["name"][:50]}</div>'
                        f'<div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">'
                        f'<div><div style="font-size:1.6rem;font-weight:700;color:{border};">{sym} {score:.0f}</div>'
                        f'<div style="font-size:0.65rem;color:#9E9E8E;">score/100</div></div>'
                        f'<div style="font-size:0.76rem;color:#6B6560;line-height:1.7;">'
                        f'<div>Dev: <b>{_dev_fmt}%</b> vs 52w</div>'
                        f'<div>Z-score: <b>{_z_fmt}σ</b> · P{pct_rank:.0f}</div>'
                        f'<div>Trend: {trend_arrow} {_trend_fmt}% / 4w · Lead ~{cfg.get("lag_weeks", 0)}w</div>'
                        f'</div></div></div>',
                        unsafe_allow_html=True,
                    )
            except Exception as _card_err:
                st.warning(f"Could not render card for **{cfg.get('name', sig_id)}**: {_card_err}")

            # Expander shows in both modes
            with st.expander("Details & chart"):
                if mode == "Simple":
                    st.markdown(f"**What it is:** {cfg.get('description', '')}")
                    st.markdown(f"**Why it matters:** {cfg.get('causal_mechanism', '')}")
                    cases = cfg.get("documented_cases", [])
                    if cases:
                        st.markdown("**Historical examples:**")
                        for c in cases:
                            st.caption(f"→ {c}")
                else:
                    st.markdown(f"**{cfg['name']}**")
                    st.caption(cfg.get("description", ""))
                    st.markdown(f"**Causal mechanism:** {cfg.get('causal_mechanism', '')}")
                    st.markdown(f"""
| Metric | Value |
|---|---|
| Current | {sv.get('current', float('nan')):.3g} {cfg.get('unit','')} |
| 52w avg | {sv.get('mean_52w', float('nan')):.3g} |
| Z-score | {sv.get('z_score', 0):.2f}σ |
| Percentile | {sv.get('percentile', 50):.0f}th |
| PCS | {cfg['pcs']}/10 |
| Lead time | ~{cfg.get('lag_weeks', 0)} weeks |
""")
                    cases = cfg.get("documented_cases", [])
                    if cases:
                        st.markdown("**Historical precedents:**")
                        for c in cases:
                            st.markdown(f"- {c}")

                # Sparkline — both modes
                data = sv.get("data", pd.Series(dtype=float))
                if not data.empty and len(data) > 4:
                    _r = int(border[1:3], 16)
                    _g = int(border[3:5], 16)
                    _b = int(border[5:7], 16)
                    spark = go.Figure(go.Scatter(
                        x=data.index[-104:],
                        y=data.values[-104:],
                        mode="lines",
                        line=dict(color=border, width=2),
                        fill="tozeroy",
                        fillcolor=f"rgba({_r},{_g},{_b},0.09)",
                    ))
                    spark.add_hline(
                        y=float(data.tail(104).mean()),
                        line_dash="dash", line_color="#9E9E9E",
                        annotation_text="2Y avg", annotation_font_size=9,
                    )
                    spark.update_layout(
                        height=140, margin=dict(l=0, r=0, t=8, b=0),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FFFFFF",
                        xaxis=dict(showgrid=False, showticklabels=False),
                        yaxis=dict(showgrid=True, gridcolor="#E8E0CE",
                                   tickfont=dict(size=8, color="#6B6560")),
                        showlegend=False,
                    )
                    st.plotly_chart(spark, use_container_width=True, key=f"spark_{sig_id}_{mode}")

                # Ticker chips
                rel_tickers = cfg.get("relevant_tickers", [])[:6]
                if rel_tickers:
                    st.caption("Related tickers (click to open Deep Dive):")
                    ticker_chips(rel_tickers, key_prefix=f"sd_{sig_id}")

st.divider()

# ── Confluence Heat Map ───────────────────────────────────────────────────────
if mode == "Pro":
    st.markdown('<div class="section-header">MULTI-SIGNAL HEAT MAP</div>', unsafe_allow_html=True)
    st.caption("Which tickers have the most signals aligned in the same direction?")

    ht_tickers = ["SPY", "QQQ", "UNP", "DHI", "CCJ", "CEG", "FCX", "WMB", "VST", "NVDA", "PWR", "NEE"]
    ht_sig_names = {sid: sv["config"]["name"][:24] for sid, sv in all_signals.items()}

    heat_data, heat_rows = [], []
    for tkr in ht_tickers:
        tkr_cfg = TICKERS.get(tkr, {})
        relevant = tkr_cfg.get("signals", list(SIGNALS.keys()))
        row = [
            all_signals[sid]["score"] if sid in all_signals and sid in relevant else None
            for sid in SIGNALS
        ]
        heat_data.append(row)
        heat_rows.append(tkr)

    heat_arr = pd.DataFrame(heat_data, index=heat_rows,
                            columns=list(ht_sig_names.values())).values.astype(float)

    fig_heat = go.Figure(go.Heatmap(
        z=heat_arr, x=list(ht_sig_names.values()), y=heat_rows,
        colorscale=[[0.0, "#5C0A0A"], [0.35, "#B71C1C"], [0.5, "#FAF7F0"],
                    [0.65, "#1B5E20"], [1.0, "#003300"]],
        zmid=50, zmin=0, zmax=100,
        hovertemplate="%{y} × %{x}<br>Score: %{z:.0f}/100<extra></extra>",
        colorbar=dict(title="Score", tickfont=dict(size=10)),
    ))
    fig_heat.update_layout(
        height=380, paper_bgcolor="#FAF7F0",
        xaxis=dict(tickangle=-35, tickfont=dict(size=9, color="#6B6560")),
        yaxis=dict(tickfont=dict(size=10, color="#1C2B4A")),
        margin=dict(l=60, r=20, t=10, b=80),
    )
    st.plotly_chart(fig_heat, use_container_width=True)
else:
    # Simple mode: show a clean ranked list
    st.markdown('<div class="section-header">TOP SIGNALS TO WATCH</div>', unsafe_allow_html=True)
    st.caption("The signals with the strongest current readings — furthest from normal.")

    ranked = sorted(
        [(sid, sv) for sid, sv in visible_signals],
        key=lambda x: abs(x[1].get("score", 50) - 50),
        reverse=True,
    )[:8]

    for sid, sv in ranked:
        cfg    = sv["config"]
        status = sv.get("status", "neutral")
        score  = sv.get("score", 50)
        border = STATUS_COLOR.get(status, "#9E9E9E")
        sym    = STATUS_SYM.get(status, "●")
        dev    = sv.get("deviation_pct", 0)
        direction = "above" if dev > 0 else "below"

        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:16px;padding:10px 14px;
                    background:#FAFAFA;border-radius:6px;border-left:4px solid {border};
                    border:1px solid #E0E0E0;margin-bottom:6px;font-family:Georgia,serif;">
            <div style="font-size:1.3rem;color:{border};font-weight:700;min-width:36px;">{sym}</div>
            <div style="flex:1;">
                <div style="font-weight:700;font-size:0.85rem;color:#1A1612;">{cfg['name']}</div>
                <div style="font-size:0.75rem;color:#6B6560;margin-top:2px;">
                    {abs(dev):.0f}% {direction} average · Score {score:.0f}/100
                    {f" · leads stocks ~{cfg['lag_weeks']}w" if cfg.get('lag_weeks') else ""}
                </div>
            </div>
            <div style="font-size:0.80rem;color:{border};font-weight:700;text-align:right;">
                {STATUS_LABEL.get(status,'').split(' ',1)[-1]}
            </div>
        </div>
        """, unsafe_allow_html=True)
