"""
Page 25 — Market Heatmap
S&P 500 sector treemap colored by Unstructured Alpha Confluence Score.
Each tile = a sector; sub-tiles = individual tickers in that sector.
Green = bullish confluence, red = bearish. Instantly shows where
macro signals are clustered — which sectors the machine favors today.
"""

import streamlit as st
import plotly.graph_objects as go
import yfinance as yf

from utils.header import render_header, render_sidebar_base, render_page_header
from utils.theme import style_chart, BG_PAGE, BG_PLOT, TEXT_PRIMARY, TEXT_SECONDARY, BORDER_LIGHT
from utils.ticker_score import compute_full_ticker_score

st.set_page_config(page_title="Market Heatmap — UA", layout="wide")
render_header("Market Heatmap")
render_sidebar_base()

render_page_header(
    "Market Heatmap",
    "S&P 500 sectors and stocks colored by Confluence Score — where the machine sees strength today.",
    icon="🗺️",
)

# ── Sector → Tickers mapping ──────────────────────────────────────────────────
# Key representative tickers per sector — these feed the confluence scores.
# Using well-known liquid names so yfinance data is reliable.
SECTOR_TICKERS = {
    "Technology":          ["AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMD", "AVGO", "ORCL"],
    "Financials":          ["JPM", "BAC", "GS", "MS", "BLK", "WFC", "C", "AXP"],
    "Healthcare":          ["JNJ", "UNH", "LLY", "ABBV", "MRK", "PFE", "TMO", "ABT"],
    "Consumer Discret.":   ["AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "TGT", "LOW"],
    "Industrials":         ["CAT", "BA", "GE", "HON", "UPS", "RTX", "LMT", "DE"],
    "Energy":              ["XOM", "CVX", "COP", "SLB", "EOG", "PSX", "VLO", "OXY"],
    "Communication Svcs":  ["GOOGL", "META", "NFLX", "DIS", "CMCSA", "T", "VZ", "ATVI"],
    "Consumer Staples":    ["PG", "KO", "PEP", "WMT", "COST", "PM", "MO", "MDLZ"],
    "Utilities":           ["NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "XEL"],
    "Real Estate":         ["AMT", "PLD", "CCI", "EQIX", "PSA", "SPG", "O", "DLR"],
    "Materials":           ["LIN", "APD", "SHW", "FCX", "NEM", "NUE", "PKG", "CF"],
}

SECTOR_ETFS = {
    "Technology": "XLK", "Financials": "XLF", "Healthcare": "XLV",
    "Consumer Discret.": "XLY", "Industrials": "XLI", "Energy": "XLE",
    "Communication Svcs": "XLC", "Consumer Staples": "XLP", "Utilities": "XLU",
    "Real Estate": "XLRE", "Materials": "XLB",
}


@st.cache_data(ttl=1800, max_entries=1, show_spinner=False)
def _score_all_tickers():
    """Score every ticker in the heatmap. Cached 30 min."""
    results = {}
    all_tickers = list({t for tickers in SECTOR_TICKERS.values() for t in tickers})
    for sym in all_tickers:
        try:
            r = compute_full_ticker_score(sym)
            conf = r.get("confluence", {})
            results[sym] = {
                "score": float(conf.get("overall_score", 50)),
                "case":  conf.get("case", "NEUTRAL"),
            }
        except Exception:
            results[sym] = {"score": 50.0, "case": "NEUTRAL"}
    return results


@st.cache_data(ttl=300, max_entries=1, show_spinner=False)
def _fetch_prices(tickers_list):
    """Fetch latest close prices + 1-day % change. 5-min TTL."""
    data = {}
    try:
        raw = yf.download(
            " ".join(tickers_list), period="2d", auto_adjust=True, progress=False
        )["Close"]
        for sym in tickers_list:
            try:
                if sym in raw.columns:
                    series = raw[sym].dropna()
                elif len(tickers_list) == 1:
                    series = raw.dropna()
                else:
                    continue
                if len(series) >= 2:
                    price = float(series.iloc[-1])
                    prev  = float(series.iloc[-2])
                    chg   = (price - prev) / prev * 100 if prev > 0 else 0.0
                else:
                    price, chg = float(series.iloc[-1]) if len(series) else 0.0, 0.0
                data[sym] = {"price": price, "chg": chg}
            except Exception:
                pass
    except Exception:
        pass
    return data


def _score_to_color(score: float) -> str:
    """Map 0-100 confluence score to a hex color on a red→gray→green scale."""
    if score >= 75:  return "#00D566"
    if score >= 65:  return "#00A847"
    if score >= 55:  return "#34D399"
    if score >= 45:  return "#6B7FBF"
    if score >= 35:  return "#CC3333"
    if score >= 25:  return "#FF4444"
    return "#FF2222"


# ── Page ──────────────────────────────────────────────────────────────────────
view_mode = st.segmented_control(
    "View",
    options=["Sectors", "Individual Stocks", "Both"],
    default="Both",
    key="heatmap_view",
)

with st.spinner("Scoring sectors… (30-min cache)"):
    scores = _score_all_tickers()

all_syms = list(scores.keys())
with st.spinner("Fetching prices…"):
    prices = _fetch_prices(all_syms)

# ── Build treemap data ────────────────────────────────────────────────────────
labels, parents, values, colors, customdata = [], [], [], [], []

# Root node
labels.append("S&P 500")
parents.append("")
values.append(0)
colors.append("#12151E")
customdata.append(("", 0, 0, "", ""))

for sector, tickers in SECTOR_TICKERS.items():
    # Sector node
    sector_scores = [scores.get(t, {}).get("score", 50) for t in tickers]
    sector_avg    = sum(sector_scores) / max(len(sector_scores), 1)
    sector_case   = "BULL" if sector_avg >= 65 else ("BEAR" if sector_avg <= 35 else "NEUTRAL")
    sector_etf    = SECTOR_ETFS.get(sector, "")
    etf_chg       = prices.get(sector_etf, {}).get("chg", 0.0)

    labels.append(sector)
    parents.append("S&P 500")
    values.append(len(tickers) * 100)   # uniform sizing for sector tiles
    colors.append(_score_to_color(sector_avg))
    customdata.append((sector, round(sector_avg, 1), round(etf_chg, 2), sector_case, sector_etf))

    if view_mode in ("Individual Stocks", "Both"):
        for sym in tickers:
            s = scores.get(sym, {})
            sc   = s.get("score", 50)
            case = s.get("case", "NEUTRAL")
            p    = prices.get(sym, {}).get("price", 0)
            chg  = prices.get(sym, {}).get("chg", 0)

            labels.append(sym)
            parents.append(sector)
            values.append(100)
            colors.append(_score_to_color(sc))
            customdata.append((sym, round(sc, 1), round(chg, 2), case, f"${p:,.2f}"))

# ── Plotly treemap ────────────────────────────────────────────────────────────
fig = go.Figure(go.Treemap(
    labels=labels,
    parents=parents,
    values=values,
    marker=dict(
        colors=colors,
        line=dict(width=2, color="#0B0D12"),
    ),
    customdata=customdata,
    hovertemplate=(
        "<b>%{label}</b><br>"
        "Confluence: <b>%{customdata[1]}/100</b><br>"
        "Signal Case: %{customdata[3]}<br>"
        "Price: %{customdata[4]}<br>"
        "1-Day Δ: %{customdata[2]:+.2f}%<br>"
        "<extra></extra>"
    ),
    texttemplate=(
        "<b>%{label}</b><br>"
        "<span style='font-size:11px;'>%{customdata[1]}</span>"
    ),
    textfont=dict(family="Inter, sans-serif", size=13, color="#E8EEFF"),
    root_color="#0B0D12",
    tiling=dict(packing="squarify"),
    pathbar=dict(visible=True, thickness=20,
                 textfont=dict(family="Inter,sans-serif", size=11, color="#8892AA")),
))

fig.update_layout(
    height=620,
    paper_bgcolor=BG_PAGE,
    font=dict(family="Inter, sans-serif", color=TEXT_PRIMARY),
    margin=dict(l=0, r=0, t=8, b=0),
)

st.plotly_chart(fig, use_container_width=True)

# ── Sector score table ─────────────────────────────────────────────────────────
st.markdown('<div class="section-header">SECTOR CONFLUENCE SCORES</div>', unsafe_allow_html=True)

sector_rows = []
for sector, tickers in SECTOR_TICKERS.items():
    sector_scores  = [scores.get(t, {}).get("score", 50) for t in tickers]
    sector_avg     = sum(sector_scores) / max(len(sector_scores), 1)
    sector_case    = "BULL" if sector_avg >= 65 else ("BEAR" if sector_avg <= 35 else "NEUTRAL")
    etf_sym        = SECTOR_ETFS.get(sector, "")
    etf_chg        = prices.get(etf_sym, {}).get("chg", 0.0)
    bull_ct        = sum(1 for s in sector_scores if s >= 65)
    bear_ct        = sum(1 for s in sector_scores if s <= 35)
    col = "#00D566" if sector_case == "BULL" else ("#FF4444" if sector_case == "BEAR" else "#6B7FBF")
    arrow = "▲" if etf_chg >= 0 else "▼"
    chg_col = "#00D566" if etf_chg >= 0 else "#FF4444"
    sector_rows.append(
        f'<tr style="border-bottom:1px solid rgba(255,255,255,0.04);">'
        f'<td style="padding:8px 12px;color:#E8EEFF;font-weight:600;">{sector}</td>'
        f'<td style="padding:8px 12px;text-align:center;">'
        f'<span style="font-size:1.1rem;font-weight:800;color:{col};">{sector_avg:.0f}</span>'
        f'<span style="font-size:0.68rem;color:#6B7FBF;"> /100</span></td>'
        f'<td style="padding:8px 12px;text-align:center;color:{col};font-weight:700;">{sector_case}</td>'
        f'<td style="padding:8px 12px;text-align:center;color:{chg_col};font-weight:600;">'
        f'{arrow} {abs(etf_chg):.2f}%</td>'
        f'<td style="padding:8px 12px;text-align:center;color:#00D566;">{bull_ct}</td>'
        f'<td style="padding:8px 12px;text-align:center;color:#FF4444;">{bear_ct}</td>'
        f'</tr>'
    )

st.markdown(f"""
<table style="width:100%;border-collapse:collapse;font-family:Inter,sans-serif;font-size:0.83rem;">
  <thead>
    <tr style="border-bottom:1px solid rgba(0,213,102,0.2);">
      <th style="padding:9px 12px;text-align:left;color:#00D566;font-size:0.62rem;letter-spacing:0.08em;text-transform:uppercase;">Sector</th>
      <th style="padding:9px 12px;text-align:center;color:#00D566;font-size:0.62rem;letter-spacing:0.08em;text-transform:uppercase;">Score</th>
      <th style="padding:9px 12px;text-align:center;color:#00D566;font-size:0.62rem;letter-spacing:0.08em;text-transform:uppercase;">Case</th>
      <th style="padding:9px 12px;text-align:center;color:#00D566;font-size:0.62rem;letter-spacing:0.08em;text-transform:uppercase;">ETF 1D</th>
      <th style="padding:9px 12px;text-align:center;color:#00D566;font-size:0.62rem;letter-spacing:0.08em;text-transform:uppercase;">▲ Bull</th>
      <th style="padding:9px 12px;text-align:center;color:#00D566;font-size:0.62rem;letter-spacing:0.08em;text-transform:uppercase;">▼ Bear</th>
    </tr>
  </thead>
  <tbody>{''.join(sector_rows)}</tbody>
</table>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.caption(
    "Confluence Scores are derived from Unstructured Alpha's 38 macro signals. "
    "Prices update every 5 minutes · Scores update every 30 minutes. "
    "NOT investment advice — for research and education only."
)
