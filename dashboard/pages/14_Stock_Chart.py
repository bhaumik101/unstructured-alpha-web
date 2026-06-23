"""
Page 14 — Stock Viewer
Clean, fast, Webull-style chart viewer. Price, volume, and configurable
technical indicators. Deliberately NOT a research page — that's Ticker Deep
Dive (pages/3_Ticker_Deep_Dive.py). Navigated to from the Watchlist via
session_state["chart_ticker"], or visited directly for any ticker.
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

# ── Brand palette ──────────────────────────────────────────────────────────────
_NAVY = "#1C2B4A"
_GOLD = "#B8860B"
_BULL = "#1B5E20"
_BEAR = "#7B1010"
_TAN  = "#8B7355"
_GRID = "#EDE8DE"

# ── Incoming ticker from Watchlist / other pages ───────────────────────────────
# session_state["chart_ticker"] is set by Watchlist when user clicks a row.
# We move it into the text_input key ("_sc_ticker") immediately so that
# subsequent reruns (timeframe change, indicator toggle) don't reset the input.
if st.session_state.get("chart_ticker"):
    st.session_state["_sc_ticker"] = st.session_state.pop("chart_ticker")

# ── Top control bar ────────────────────────────────────────────────────────────
_col_sym, _col_tf, _col_type = st.columns([1.4, 5.2, 1.4])

with _col_sym:
    _raw = st.text_input(
        "Symbol",
        key="_sc_ticker",
        max_chars=10,
        label_visibility="collapsed",
        placeholder="Ticker…",
    )
    TICKER = (_raw or "SPY").strip().upper()

TF_MAP = {
    "1D":  ("1d",   "5m",  True),
    "5D":  ("5d",   "30m", False),
    "1M":  ("1mo",  "1d",  False),
    "3M":  ("3mo",  "1d",  False),
    "6M":  ("6mo",  "1d",  False),
    "1Y":  ("1y",   "1d",  False),
    "YTD": ("ytd",  "1d",  False),
    "5Y":  ("5y",   "1wk", False),
    "ALL": ("max",  "1wk", False),
}

with _col_tf:
    tf = st.radio(
        "Timeframe",
        list(TF_MAP.keys()),
        index=2,
        horizontal=True,
        label_visibility="collapsed",
        key="_sc_tf",
    )

with _col_type:
    chart_type = st.radio(
        "Chart type",
        ["Line", "Candles"],
        horizontal=True,
        label_visibility="collapsed",
        key="_sc_ctype",
    )

period, interval, prepost = TF_MAP[tf]

# ── Indicator toggles ──────────────────────────────────────────────────────────
_ic = st.columns(6)
with _ic[0]: show_ma20  = st.checkbox("MA 20",     value=True,  key="_sc_ma20")
with _ic[1]: show_ma50  = st.checkbox("MA 50",     value=True,  key="_sc_ma50")
with _ic[2]: show_ma200 = st.checkbox("MA 200",    value=False, key="_sc_ma200")
with _ic[3]: show_rsi   = st.checkbox("RSI 14",    value=True,  key="_sc_rsi")
with _ic[4]: show_macd  = st.checkbox("MACD",      value=False, key="_sc_macd")
with _ic[5]: show_bb    = st.checkbox("Bollinger", value=False, key="_sc_bb")

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

close = df["Close"]
open_ = df["Open"]
high  = df["High"]
low   = df["Low"]
vol   = df["Volume"]
xax   = df.index

last_price = float(close.iloc[-1])
prev_close = meta.get("prev_close") or (float(close.iloc[-2]) if len(close) > 1 else last_price)
chg        = last_price - prev_close
chg_pct    = (chg / prev_close * 100) if prev_close else 0
chg_color  = _BULL if chg >= 0 else _BEAR
chg_arrow  = "▲" if chg >= 0 else "▼"

company_name = TICKERS.get(TICKER, {}).get("name") or meta.get("name") or TICKER

# Pre/post market labels (only show when price differs meaningfully)
pre_price  = meta.get("pre_price")
post_price = meta.get("post_price")
_ext_parts = []
if pre_price and abs(pre_price - last_price) > 0.005:
    _pc  = (pre_price - last_price) / last_price * 100
    _cc  = _BULL if _pc >= 0 else _BEAR
    _ext_parts.append(
        f'<span style="font-size:0.78rem;color:{_cc};background:rgba(0,0,0,0.04);'
        f'padding:1px 6px;border-radius:4px;margin-left:10px;">'
        f'Pre ${pre_price:,.2f} ({_pc:+.2f}%)</span>'
    )
if post_price and abs(post_price - last_price) > 0.005:
    _pc  = (post_price - last_price) / last_price * 100
    _cc  = _BULL if _pc >= 0 else _BEAR
    _ext_parts.append(
        f'<span style="font-size:0.78rem;color:{_cc};background:rgba(0,0,0,0.04);'
        f'padding:1px 6px;border-radius:4px;margin-left:10px;">'
        f'Post ${post_price:,.2f} ({_pc:+.2f}%)</span>'
    )
_ext_html = "".join(_ext_parts)

# ── Price header ───────────────────────────────────────────────────────────────
_h1, _h2 = st.columns([5, 1])
with _h1:
    st.markdown(
        f'<div style="margin-bottom:2px;">'
        f'<span style="font-size:1.5rem;font-weight:700;color:{_NAVY};font-family:Georgia,serif;">'
        f'{company_name}</span>'
        f'<span style="font-size:0.9rem;color:{_TAN};margin-left:10px;font-family:Georgia,serif;">'
        f'{TICKER}</span>'
        f'</div>'
        f'<div style="display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;">'
        f'<span style="font-size:2.0rem;font-weight:700;color:{_NAVY};font-family:Georgia,serif;">'
        f'${last_price:,.2f}</span>'
        f'<span style="font-size:0.95rem;font-weight:600;color:{chg_color};">'
        f'{chg_arrow} {abs(chg):,.2f} ({chg_pct:+.2f}%)</span>'
        f'{_ext_html}'
        f'</div>',
        unsafe_allow_html=True,
    )
with _h2:
    # Offer quick path to research for users who want more depth
    if st.button("→ Full Research", key="_sc_goto_tdd",
                 help="Open Ticker Deep Dive for signal analysis, earnings, and insider data"):
        st.session_state["selected_ticker"] = TICKER
        st.switch_page("pages/3_Ticker_Deep_Dive.py")

# ── Indicator math ─────────────────────────────────────────────────────────────
def _rsi(s: pd.Series, w: int = 14) -> pd.Series:
    d = s.diff()
    g = d.clip(lower=0).ewm(com=w - 1, adjust=False).mean()
    l = (-d.clip(upper=0)).ewm(com=w - 1, adjust=False).mean()
    return 100 - 100 / (1 + g / (l + 1e-9))


def _macd(s: pd.Series, fast: int = 12, slow: int = 26, sig: int = 9):
    ef  = s.ewm(span=fast, adjust=False).mean()
    es  = s.ewm(span=slow, adjust=False).mean()
    ml  = ef - es
    sl  = ml.ewm(span=sig, adjust=False).mean()
    return ml, sl, ml - sl


def _bollinger(s: pd.Series, w: int = 20, n: float = 2.0):
    ma  = s.rolling(w).mean()
    std = s.rolling(w).std()
    return ma + n * std, ma, ma - n * std


# ── Build Plotly subplots dynamically ─────────────────────────────────────────
extra_rows  = int(show_rsi) + int(show_macd)
total_rows  = 2 + extra_rows

_height_map = {0: [0.73, 0.27], 1: [0.60, 0.20, 0.20], 2: [0.54, 0.14, 0.16, 0.16]}
row_heights  = _height_map[extra_rows]

fig = make_subplots(
    rows=total_rows,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.025,
    row_heights=row_heights,
)

# ─── Row 1 — Price ─────────────────────────────────────────────────────────────
if chart_type == "Candles":
    fig.add_trace(go.Candlestick(
        x=xax, open=open_, high=high, low=low, close=close,
        name=TICKER,
        increasing=dict(line=dict(color=_BULL), fillcolor=_BULL),
        decreasing=dict(line=dict(color=_BEAR), fillcolor=_BEAR),
        showlegend=False,
    ), row=1, col=1)
else:
    _lc   = _BULL if chg >= 0 else _BEAR
    _fill = "rgba(27,94,32,0.06)" if chg >= 0 else "rgba(123,16,16,0.06)"
    fig.add_trace(go.Scatter(
        x=xax, y=close,
        mode="lines",
        name=TICKER,
        line=dict(color=_lc, width=1.8),
        fill="tozeroy",
        fillcolor=_fill,
        showlegend=False,
    ), row=1, col=1)

# Moving averages
_MA_STYLES = {
    20:  dict(color="#C9A84C", width=1.2, dash="solid"),
    50:  dict(color="#1C2B4A", width=1.2, dash="solid"),
    200: dict(color="#7B1010", width=1.0, dash="dot"),
}
for _win, _show in [(20, show_ma20), (50, show_ma50), (200, show_ma200)]:
    if _show and len(close) > _win:
        _s = _MA_STYLES[_win]
        fig.add_trace(go.Scatter(
            x=xax,
            y=close.rolling(_win).mean(),
            mode="lines",
            name=f"MA{_win}",
            line=dict(color=_s["color"], width=_s["width"], dash=_s["dash"]),
            opacity=0.85,
        ), row=1, col=1)

# Bollinger Bands — upper first, lower second with fill="tonexty" so the
# filled region spans between upper and lower, not lower→mid.
if show_bb and len(close) >= 20:
    bb_upper, bb_mid, bb_lower = _bollinger(close)
    _BB_COLOR = "rgba(139,115,85,0.75)"
    fig.add_trace(go.Scatter(x=xax, y=bb_upper, mode="lines", name="BB Upper",
                             line=dict(color=_BB_COLOR, width=0.9, dash="dash"),
                             showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=xax, y=bb_lower, mode="lines", name="Bollinger",
                             line=dict(color=_BB_COLOR, width=0.9, dash="dash"),
                             fill="tonexty", fillcolor="rgba(139,115,85,0.06)"),  row=1, col=1)
    fig.add_trace(go.Scatter(x=xax, y=bb_mid,   mode="lines", name="BB Mid",
                             line=dict(color=_BB_COLOR, width=0.8, dash="dot"),
                             showlegend=False), row=1, col=1)

# ─── Row 2 — Volume ────────────────────────────────────────────────────────────
_vol_colors = [_BULL if float(c) >= float(o) else _BEAR
               for c, o in zip(close, open_)]
fig.add_trace(go.Bar(
    x=xax, y=vol,
    name="Volume",
    marker_color=_vol_colors,
    opacity=0.5,
    showlegend=False,
), row=2, col=1)

# ─── Row 3 — RSI ───────────────────────────────────────────────────────────────
_next_row = 3
if show_rsi:
    rsi_s = _rsi(close)
    fig.add_trace(go.Scatter(
        x=xax, y=rsi_s,
        mode="lines",
        name="RSI 14",
        line=dict(color=_GOLD, width=1.5),
        showlegend=True,
    ), row=_next_row, col=1)
    # Overbought / oversold bands via add_hline (supports row/col directly)
    fig.add_hline(y=70, line_dash="dot", line_color=_BEAR, line_width=0.8,
                  opacity=0.6, row=_next_row, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color=_BULL, line_width=0.8,
                  opacity=0.6, row=_next_row, col=1)
    fig.update_yaxes(range=[0, 100], tickvals=[30, 50, 70], row=_next_row, col=1)
    _next_row += 1

# ─── Row 4 — MACD ──────────────────────────────────────────────────────────────
if show_macd and len(close) >= 26:
    ml, sl, hist = _macd(close)
    _hist_c = [_BULL if float(h) >= 0 else _BEAR for h in hist]
    fig.add_trace(go.Scatter(x=xax, y=ml,   mode="lines", name="MACD",
                             line=dict(color=_NAVY, width=1.3)),         row=_next_row, col=1)
    fig.add_trace(go.Scatter(x=xax, y=sl,   mode="lines", name="Signal",
                             line=dict(color=_GOLD, width=1.3)),         row=_next_row, col=1)
    fig.add_trace(go.Bar(x=xax, y=hist, name="Histogram",
                         marker_color=_hist_c, opacity=0.55,
                         showlegend=False),                               row=_next_row, col=1)

# ── Layout styling ─────────────────────────────────────────────────────────────
_has_legend = (show_ma20 or show_ma50 or show_ma200 or show_bb or show_rsi or show_macd)
fig.update_layout(
    height=500 + extra_rows * 110,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Georgia, serif", size=11, color=_NAVY),
    margin=dict(l=4, r=4, t=8, b=8),
    xaxis_rangeslider_visible=False,
    hovermode="x unified",
    showlegend=_has_legend,
    legend=dict(
        orientation="h",
        yanchor="bottom", y=1.01,
        xanchor="left", x=0,
        font=dict(size=10),
        bgcolor="rgba(250,247,240,0.85)",
        borderwidth=0,
    ),
)

# Shared axis styling across all rows
_axis_style = dict(showgrid=True, gridcolor=_GRID, gridwidth=0.5, zeroline=False, showline=False)
for _r in range(1, total_rows + 1):
    fig.update_xaxes(**_axis_style, row=_r, col=1)
    fig.update_yaxes(**_axis_style, row=_r, col=1)

# Axis labels
_row_labels = {1: "Price", 2: "Vol"}
if show_rsi:  _row_labels[3] = "RSI"
if show_macd: _row_labels[2 + int(show_rsi) + 1] = "MACD"
for _r, _lbl in _row_labels.items():
    fig.update_yaxes(
        title_text=_lbl,
        title_font=dict(size=8, color=_TAN),
        title_standoff=2,
        row=_r, col=1,
    )

st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ── Key stats strip ────────────────────────────────────────────────────────────
def _fmt_vol(v) -> str:
    if v is None: return "—"
    v = float(v)
    if v >= 1e9: return f"{v/1e9:.2f}B"
    if v >= 1e6: return f"{v/1e6:.1f}M"
    return f"{v:,.0f}"


def _fmt_cap(v) -> str:
    if v is None: return "—"
    v = float(v)
    if v >= 1e12: return f"${v/1e12:.2f}T"
    if v >= 1e9:  return f"${v/1e9:.1f}B"
    if v >= 1e6:  return f"${v/1e6:.0f}M"
    return f"${v:,.0f}"


_52h = meta.get("52w_high")
_52l = meta.get("52w_low")
_cap = meta.get("mkt_cap")

_stats = [
    ("Open",     f"${float(df['Open'].iloc[-1]):,.2f}"),
    ("High",     f"${float(df['High'].iloc[-1]):,.2f}"),
    ("Low",      f"${float(df['Low'].iloc[-1]):,.2f}"),
    ("Close",    f"${last_price:,.2f}"),
    ("Volume",   _fmt_vol(vol.iloc[-1]) if not vol.empty else "—"),
    ("52W High", f"${_52h:,.2f}" if _52h else "—"),
    ("52W Low",  f"${_52l:,.2f}" if _52l else "—"),
    ("Mkt Cap",  _fmt_cap(_cap)),
]

_sc = st.columns(len(_stats))
for _col, (label, val) in zip(_sc, _stats):
    _col.markdown(
        f'<div style="text-align:center;padding:6px 0;">'
        f'<div style="font-size:0.67rem;color:{_TAN};letter-spacing:0.07em;text-transform:uppercase;">'
        f'{label}</div>'
        f'<div style="font-size:0.92rem;font-weight:600;color:{_NAVY};">{val}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

st.markdown(
    '<div class="disclaimer">'
    'Price data via Yahoo Finance. This page shows charts and indicators only — '
    'no signal analysis. For research signals, earnings data, and insider activity, '
    'use <b>Ticker Deep Dive</b>.'
    '</div>',
    unsafe_allow_html=True,
)
