"""
Page 14 — Stock Viewer
TradingView / Yahoo Finance-style clean candlestick chart viewer.
- Candlestick only (line charts give no actionable information).
- Timeframe selector uses st.pills (Streamlit 1.38+) for a native pill UI.
- Indicators are added via a multiselect dropdown, not checkboxes.
- Gaps (weekends / market holidays) are eliminated via categorical x-axis.
Not a research page — use Ticker Deep Dive for signal analysis.
"""

import numpy as np
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

from utils.config import TICKERS
from utils.header import render_header, render_sidebar_base

st.set_page_config(page_title="Stock Viewer — UA", layout="wide")
render_header("Stock Viewer")
render_sidebar_base()

# ── Dark design system palette ────────────────────────────────────────────────
_BULL  = "#00D566"          # bullish green
_BEAR  = "#FF4444"          # bearish red
_NAVY  = "#E8EEFF"          # primary text (near-white on dark)
_GOLD  = "#F59E0B"          # amber accent (RSI, MA9)
_TAN   = "#8892AA"          # muted text
_CREAM = "#0B0D12"          # page bg (unused in chart, kept for compat)
_GRID  = "rgba(255,255,255,0.05)"  # subtle grid lines
_BG    = "#0F1118"          # chart plot area

# ── Minimal CSS — only what the built-in components can't handle ───────────────
st.markdown("""
<style>
/* Tighten the pills row top-margin so it sits flush in the control bar */
div[data-testid="stPills"] { margin-top: 0 !important; }
div[data-testid="stPills"] div[role="group"] {
    gap: 3px !important;
    flex-wrap: wrap !important;
}
div[data-testid="stPills"] label {
    padding: 3px 11px !important;
    font-size: 0.76rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em !important;
    border-radius: 4px !important;
}
/* Remove extra top margin on the multiselect label row */
div[data-testid="stMultiSelect"] > label { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ── Incoming ticker from Watchlist / other pages ───────────────────────────────
if st.session_state.get("chart_ticker"):
    st.session_state["_sc_ticker"] = st.session_state.pop("chart_ticker")

# ── Timeframe map — period/interval pairs with intuitive labels ────────────────
# 1D → 5-min candles (intraday detail)
# 5D → 15-min candles (short-term swing)
# 1M / 3M / 6M / YTD / 1Y → daily candles (core view)
# 2Y / 5Y → weekly candles (trend view)
# Max → monthly candles (macro view)
TF_MAP: dict[str, tuple] = {
    "1D":  ("1d",  "5m",  True),
    "5D":  ("5d",  "15m", False),
    "1M":  ("1mo", "1d",  False),
    "3M":  ("3mo", "1d",  False),
    "6M":  ("6mo", "1d",  False),
    "YTD": ("ytd", "1d",  False),
    "1Y":  ("1y",  "1d",  False),
    "2Y":  ("2y",  "1wk", False),
    "5Y":  ("5y",  "1wk", False),
    "Max": ("max", "1mo", False),
}

# ── Available indicators (shown in the dropdown) ───────────────────────────────
_IND_OPTIONS = ["MA 9", "MA 20", "MA 50", "MA 200", "RSI (14)", "MACD", "Bollinger Bands"]
_IND_DEFAULT = ["MA 20", "MA 50", "RSI (14)"]

# ── Control bar ────────────────────────────────────────────────────────────────
_c1, _c2, _c3 = st.columns([1.3, 6.2, 2.5])

with _c1:
    _raw   = st.text_input("Symbol", key="_sc_ticker", max_chars=20,
                            label_visibility="collapsed",
                            placeholder="Any symbol: SPY, AAPL, BTC-USD, ^GSPC…",
                            help="Supports any Yahoo Finance symbol worldwide: US stocks, ETFs, indices (^GSPC, ^FTSE), crypto (BTC-USD), FX (EURUSD=X), international (BABA, NVO, MC.PA)")
    TICKER = (_raw or "SPY").strip().upper()

with _c2:
    tf = st.pills(
        "Timeframe",
        list(TF_MAP.keys()),
        default="3M",
        label_visibility="collapsed",
        key="_sc_tf",
    )
    if tf is None:
        tf = "3M"

with _c3:
    selected_inds = st.multiselect(
        "Indicators",
        options=_IND_OPTIONS,
        default=_IND_DEFAULT,
        placeholder="Add indicator…",
        label_visibility="collapsed",
        key="_sc_inds",
    )

period, interval, prepost = TF_MAP[tf]

show_ma9   = "MA 9"           in selected_inds
show_ma20  = "MA 20"          in selected_inds
show_ma50  = "MA 50"          in selected_inds
show_ma200 = "MA 200"         in selected_inds
show_rsi   = "RSI (14)"       in selected_inds
show_macd  = "MACD"           in selected_inds
show_bb    = "Bollinger Bands" in selected_inds

# ── Data fetch ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False, max_entries=30)
def _load(ticker: str, period: str, interval: str, prepost: bool) -> tuple[pd.DataFrame, dict]:
    t   = yf.Ticker(ticker)
    df  = t.history(period=period, interval=interval, prepost=prepost, auto_adjust=True)
    meta: dict = {}
    try:
        fi = t.fast_info
        meta["name"]       = getattr(fi, "long_name",           None) or getattr(fi, "short_name", None)
        meta["pre_price"]  = getattr(fi, "pre_market_price",    None)
        meta["post_price"] = getattr(fi, "post_market_price",   None)
        meta["52w_high"]   = getattr(fi, "fifty_two_week_high", None) or getattr(fi, "year_high", None)
        meta["52w_low"]    = getattr(fi, "fifty_two_week_low",  None) or getattr(fi, "year_low",  None)
        meta["mkt_cap"]    = getattr(fi, "market_cap",          None)
        meta["prev_close"] = getattr(fi, "previous_close",      None)
    except Exception:
        pass
    return df, meta


with st.spinner(f"Loading {TICKER}…"):
    df, meta = _load(TICKER, period, interval, prepost)

if df is None or df.empty:
    st.error(f"No price data for **{TICKER}**. Check the ticker symbol and try again.")
    st.stop()

# ── Strip timezone from index (for consistent string formatting) ───────────────
if hasattr(df.index, "tz") and df.index.tz is not None:
    df.index = df.index.tz_localize(None)

close = df["Close"]
open_ = df["Open"]
high  = df["High"]
low   = df["Low"]
vol   = df["Volume"]

last_price = float(close.iloc[-1])
prev_close = meta.get("prev_close") or (float(close.iloc[-2]) if len(close) > 1 else last_price)
chg        = last_price - prev_close
chg_pct    = (chg / prev_close * 100) if prev_close else 0
chg_color  = _BULL if chg >= 0 else _BEAR
chg_arrow  = "▲" if chg >= 0 else "▼"

company_name = TICKERS.get(TICKER, {}).get("name") or meta.get("name") or TICKER

# Pre/post market labels
pre_price  = meta.get("pre_price")
post_price = meta.get("post_price")
_ext_parts = []
if pre_price and abs(pre_price - last_price) > 0.005:
    _pc = (pre_price - last_price) / last_price * 100
    _cc = _BULL if _pc >= 0 else _BEAR
    _ext_parts.append(
        f'<span style="font-size:0.76rem;color:{_cc};background:rgba(255,255,255,0.06);'
        f'padding:2px 8px;border-radius:6px;margin-left:8px;border:1px solid {_cc}33;">'
        f'Pre ${pre_price:,.2f} ({_pc:+.2f}%)</span>'
    )
if post_price and abs(post_price - last_price) > 0.005:
    _pc = (post_price - last_price) / last_price * 100
    _cc = _BULL if _pc >= 0 else _BEAR
    _ext_parts.append(
        f'<span style="font-size:0.76rem;color:{_cc};background:rgba(255,255,255,0.06);'
        f'padding:2px 8px;border-radius:6px;margin-left:8px;border:1px solid {_cc}33;">'
        f'Post ${post_price:,.2f} ({_pc:+.2f}%)</span>'
    )

# ── Price header ───────────────────────────────────────────────────────────────
_hc1, _hc2 = st.columns([5, 1])
with _hc1:
    st.markdown(
        f'<div style="margin-bottom:2px;font-family:Inter,sans-serif;">'
        f'<span style="font-size:1.3rem;font-weight:700;color:#E8EEFF;">'
        f'{company_name}</span>'
        f'<span style="font-size:0.82rem;color:#8892AA;margin-left:9px;font-weight:500;">'
        f'{TICKER}</span>'
        f'</div>'
        f'<div style="display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;">'
        f'<span style="font-size:2.0rem;font-weight:800;color:#E8EEFF;letter-spacing:-1px;">'
        f'${last_price:,.2f}</span>'
        f'<span style="font-size:0.92rem;font-weight:600;color:{chg_color};">'
        f'{chg_arrow} {abs(chg):,.2f} ({chg_pct:+.2f}%)</span>'
        f'{"".join(_ext_parts)}'
        f'</div>',
        unsafe_allow_html=True,
    )
with _hc2:
    if st.button("→ Full Research", key="_sc_tdd",
                 help="Ticker Deep Dive: signals, earnings, insider data"):
        st.session_state["selected_ticker"] = TICKER
        st.switch_page("pages/3_Ticker_Deep_Dive.py")

# ── X-axis labels — STRING-BASED to eliminate weekend/holiday gaps ─────────────
# Using category-typed x-axis (via string labels) means every candle is evenly
# spaced regardless of gaps in the underlying timestamps. This is the same
# technique used by Bloomberg and TradingView for gap-free charts.
def _xlabels(df: pd.DataFrame, tf: str) -> list[str]:
    idx = df.index
    if tf == "1D":
        return [t.strftime("%-I:%M %p") for t in idx]
    elif tf == "5D":
        return [t.strftime("%a %-I:%M %p") for t in idx]
    elif tf in ("1M",):
        return [t.strftime("%b %-d") for t in idx]
    elif tf in ("3M", "6M", "YTD"):
        return [t.strftime("%b %-d '%y") for t in idx]
    elif tf in ("1Y",):
        return [t.strftime("%b '%y") for t in idx]
    else:  # 2Y, 5Y, Max
        return [t.strftime("%b '%y") for t in idx]

try:
    xax = _xlabels(df, tf)
except Exception:
    # Windows doesn't support %-d / %-I — fall back to zero-padded
    xax = [str(t)[:16] for t in df.index]

# ── Indicator math ─────────────────────────────────────────────────────────────
def _rsi(s: pd.Series, w: int = 14) -> pd.Series:
    d = s.diff()
    g = d.clip(lower=0).ewm(com=w - 1, adjust=False).mean()
    l = (-d.clip(upper=0)).ewm(com=w - 1, adjust=False).mean()
    return 100 - 100 / (1 + g / (l + 1e-9))


def _macd_calc(s: pd.Series, fast: int = 12, slow: int = 26, sig: int = 9):
    ef  = s.ewm(span=fast, adjust=False).mean()
    es  = s.ewm(span=slow, adjust=False).mean()
    ml  = ef - es
    sl  = ml.ewm(span=sig, adjust=False).mean()
    return ml, sl, ml - sl


def _bollinger(s: pd.Series, w: int = 20, n: float = 2.0):
    ma  = s.rolling(w).mean()
    std = s.rolling(w).std()
    return ma + n * std, ma, ma - n * std


# ── Build subplots ─────────────────────────────────────────────────────────────
extra_rows   = int(show_rsi) + int(show_macd)
total_rows   = 2 + extra_rows

_heights = {0: [0.75, 0.25], 1: [0.60, 0.18, 0.22], 2: [0.54, 0.14, 0.16, 0.16]}
row_heights = _heights[extra_rows]

fig = make_subplots(
    rows=total_rows,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.02,
    row_heights=row_heights,
)

# ─── Row 1 — Candlestick ───────────────────────────────────────────────────────
fig.add_trace(go.Candlestick(
    x=xax,
    open=open_, high=high, low=low, close=close,
    name=TICKER,
    increasing=dict(line=dict(color=_BULL, width=1), fillcolor=_BULL),
    decreasing=dict(line=dict(color=_BEAR, width=1), fillcolor=_BEAR),
    showlegend=False,
    whiskerwidth=0.3,
), row=1, col=1)

# Moving averages — bright on dark background
_MA_STYLES = {
    9:   dict(color="#F59E0B", width=1.2, dash="solid"),   # amber — fast
    20:  dict(color="#00C8E0", width=1.3, dash="solid"),   # cyan
    50:  dict(color="#7C3AED", width=1.4, dash="solid"),   # purple
    200: dict(color="#FF8888", width=1.2, dash="dot"),     # soft red
}
for _win, _show in [(9, show_ma9), (20, show_ma20), (50, show_ma50), (200, show_ma200)]:
    if _show and len(close) > _win:
        _s = _MA_STYLES[_win]
        fig.add_trace(go.Scatter(
            x=xax,
            y=close.rolling(_win).mean(),
            mode="lines",
            name=f"MA{_win}",
            line=dict(color=_s["color"], width=_s["width"], dash=_s["dash"]),
            opacity=0.90,
        ), row=1, col=1)

# Bollinger Bands — upper first, then lower with fill, then mid
if show_bb and len(close) >= 20:
    bb_upper, bb_mid, bb_lower = _bollinger(close)
    _BB = "rgba(124,58,237,0.70)"   # purple on dark
    fig.add_trace(go.Scatter(x=xax, y=bb_upper, mode="lines",
                             name="BB Upper", line=dict(color=_BB, width=0.9, dash="dash"),
                             showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=xax, y=bb_lower, mode="lines",
                             name="Bollinger", line=dict(color=_BB, width=0.9, dash="dash"),
                             fill="tonexty", fillcolor="rgba(124,58,237,0.04)"), row=1, col=1)
    fig.add_trace(go.Scatter(x=xax, y=bb_mid, mode="lines",
                             name="BB Mid", line=dict(color=_BB, width=0.7, dash="dot"),
                             showlegend=False), row=1, col=1)

# ─── Row 2 — Volume ────────────────────────────────────────────────────────────
_vol_colors = [
    "rgba(0,213,102,0.45)"  if float(c) >= float(o) else
    "rgba(255,68,68,0.45)"
    for c, o in zip(close, open_)
]
fig.add_trace(go.Bar(
    x=xax, y=vol,
    name="Volume",
    marker_color=_vol_colors,
    showlegend=False,
), row=2, col=1)

# ─── Row 3 — RSI (optional) ────────────────────────────────────────────────────
_next_row = 3
if show_rsi:
    rsi_s = _rsi(close)
    fig.add_trace(go.Scatter(
        x=xax, y=rsi_s,
        mode="lines",
        name="RSI (14)",
        line=dict(color=_GOLD, width=1.5),
        showlegend=True,
    ), row=_next_row, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="#FF4444", line_width=1.0,
                  opacity=0.6, row=_next_row, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="#00D566", line_width=1.0,
                  opacity=0.6, row=_next_row, col=1)
    fig.update_yaxes(range=[0, 100], tickvals=[30, 50, 70], row=_next_row, col=1)
    _next_row += 1

# ─── Row 4 — MACD (optional) ───────────────────────────────────────────────────
if show_macd and len(close) >= 26:
    ml, sl, hist = _macd_calc(close)
    _hist_c = [
        "rgba(0,213,102,0.65)"  if float(h) >= 0 else
        "rgba(255,68,68,0.65)"
        for h in hist
    ]
    fig.add_trace(go.Scatter(x=xax, y=ml, mode="lines", name="MACD",
                             line=dict(color="#00C8E0", width=1.3)), row=_next_row, col=1)
    fig.add_trace(go.Scatter(x=xax, y=sl, mode="lines", name="Signal",
                             line=dict(color=_GOLD, width=1.3)), row=_next_row, col=1)
    fig.add_trace(go.Bar(x=xax, y=hist, name="Histogram",
                         marker_color=_hist_c, showlegend=False), row=_next_row, col=1)

# ── Last-price annotation on the right Y-axis edge ────────────────────────────
fig.add_annotation(
    x=1.0, xref="paper",
    y=last_price, yref="y",
    text=f" ${last_price:,.2f} ",
    showarrow=False,
    xanchor="left",
    font=dict(color="#0B0D12", size=10.5, family="Inter, sans-serif"),
    bgcolor=chg_color,
    borderpad=3,
    bordercolor=chg_color,
)

# ── Layout polish — full dark theme ───────────────────────────────────────────
_has_legend = (
    show_ma9 or show_ma20 or show_ma50 or show_ma200
    or show_bb or show_rsi or show_macd
)
_chart_h = 480 + extra_rows * 115

fig.update_layout(
    height=_chart_h,
    paper_bgcolor="#0B0D12",        # page background
    plot_bgcolor=_BG,               # chart area (#0F1118)
    font=dict(family="Inter, sans-serif", size=11, color="#E8EEFF"),
    margin=dict(l=8, r=72, t=8, b=8),   # r=72 to leave room for price label
    xaxis_rangeslider_visible=False,
    hovermode="x unified",
    showlegend=_has_legend,
    hoverlabel=dict(
        bgcolor="#1A1E2C",
        bordercolor="rgba(255,255,255,0.08)",
        font=dict(family="Inter, sans-serif", size=12, color="#E8EEFF"),
        namelength=-1,
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom", y=1.01,
        xanchor="left", x=0,
        font=dict(size=10, color="#8892AA", family="Inter, sans-serif"),
        bgcolor="rgba(18,21,30,0.90)",
        bordercolor="rgba(255,255,255,0.08)",
        borderwidth=1,
    ),
)

# Shared axis style — readable labels on dark background
_ax_style = dict(
    showgrid=True,
    gridcolor=_GRID,                        # rgba(255,255,255,0.05)
    gridwidth=1,
    zeroline=False,
    showline=True,
    linecolor="rgba(255,255,255,0.08)",
    ticks="outside",
    tickcolor="rgba(255,255,255,0.15)",
    tickfont=dict(size=10, color="#8892AA", family="Inter, sans-serif"),
)
for _r in range(1, total_rows + 1):
    fig.update_xaxes(**_ax_style, row=_r, col=1, nticks=8)
    fig.update_yaxes(**_ax_style, row=_r, col=1)

# Subplot y-axis labels
_ylabels = {1: "Price", 2: "Vol"}
if show_rsi:
    _ylabels[3] = "RSI"
if show_macd:
    _ylabels[2 + int(show_rsi) + 1] = "MACD"
for _r, _lbl in _ylabels.items():
    fig.update_yaxes(
        title_text=_lbl,
        title_font=dict(size=9, color="#6B7FBF", family="Inter, sans-serif"),
        title_standoff=3, row=_r, col=1,
    )

st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ── Stats strip ───────────────────────────────────────────────────────────────
def _fv(v) -> str:
    if v is None: return "—"
    v = float(v)
    if v >= 1e12: return f"${v/1e12:.2f}T"
    if v >= 1e9:  return f"${v/1e9:.2f}B"
    if v >= 1e6:  return f"${v/1e6:.1f}M"
    return f"{v:,.0f}"

_cap  = meta.get("mkt_cap")
_52h  = meta.get("52w_high")
_52l  = meta.get("52w_low")

_stats = [
    ("Open",     f"${float(df['Open'].iloc[-1]):,.2f}"),
    ("High",     f"${float(df['High'].iloc[-1]):,.2f}"),
    ("Low",      f"${float(df['Low'].iloc[-1]):,.2f}"),
    ("Close",    f"${last_price:,.2f}"),
    ("Volume",   _fv(vol.iloc[-1]) if not vol.empty else "—"),
    ("52W High", f"${_52h:,.2f}" if _52h else "—"),
    ("52W Low",  f"${_52l:,.2f}" if _52l else "—"),
    ("Mkt Cap",  _fv(_cap)),
]

_s_cols = st.columns(len(_stats))
for _col, (label, val) in zip(_s_cols, _stats):
    _col.markdown(
        f'<div style="text-align:center;padding:8px 0 4px;font-family:Inter,sans-serif;">'
        f'<div style="font-size:0.62rem;color:#6B7FBF;letter-spacing:0.10em;'
        f'text-transform:uppercase;margin-bottom:3px;font-weight:700;">{label}</div>'
        f'<div style="font-size:0.92rem;font-weight:700;color:#E8EEFF;">{val}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

st.markdown(
    '<div style="font-size:0.68rem;color:#6B7FBF;padding:6px 0;font-family:Inter,sans-serif;">'
    'Price data via Yahoo Finance. Accepts any global symbol: US stocks, ETFs, indices (^GSPC, ^FTSE), '
    'crypto (BTC-USD), FX (EURUSD=X), international equities (MC.PA, 9984.T). '
    'For macro signal analysis, use <b style="color:#8892AA">Ticker Deep Dive</b>.</div>',
    unsafe_allow_html=True,
)
