"""
Shared header + CSS injected at the top of every page.
Call render_header() as the very first Streamlit call after st.set_page_config().
"""

import streamlit as st

from utils.config import TICKERS

# ── Modern Dark Design System CSS ────────────────────────────────────────────
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── Base typography ─────────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    font-variant-numeric: tabular-nums;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    line-height: 1.55;
}

/* ── Scrollbar ───────────────────────────────────────────────────────────── */
::-webkit-scrollbar              { width: 4px; height: 4px; }
::-webkit-scrollbar-track        { background: transparent; }
::-webkit-scrollbar-thumb        { background: rgba(0,213,102,0.22); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover  { background: rgba(0,213,102,0.45); }

/* ── Page background ─────────────────────────────────────────────────────── */
.main                 { background-color: #0B0D12 !important; }
.block-container      { background-color: #0B0D12 !important; padding-top: 0.75rem !important; }
[data-testid="stAppViewContainer"] { background-color: #0B0D12 !important; }

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D0F1A 0%, #0A0C14 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.04) !important;
}
section[data-testid="stSidebar"] * { color: #8892AA !important; }
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] a { color: #8892AA !important; }
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #E8EEFF !important;
    border-bottom: 1px solid rgba(255,255,255,0.05) !important;
    padding-bottom: 4px !important;
}
[data-testid="stNavSectionHeader"] {
    background: rgba(0,213,102,0.07) !important;
    border-radius: 6px !important;
    padding: 3px 8px !important;
    margin-top: 12px !important;
    margin-bottom: 3px !important;
}
[data-testid="stNavSectionHeader"] p {
    font-size: 0.62rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: #00D566 !important;
}
[data-testid="stSidebarNavItems"] a[aria-selected="true"],
[data-testid="stSidebarNavItems"] [aria-selected="true"] {
    background: rgba(0,213,102,0.09) !important;
    border-radius: 6px !important;
}
[data-testid="stSidebarNavItems"] a[aria-selected="true"] p,
[data-testid="stSidebarNavItems"] [aria-selected="true"] p { color: #00D566 !important; }
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(0,213,102,0.09) !important;
    border: 1px solid rgba(0,213,102,0.22) !important;
    color: #00D566 !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(0,213,102,0.16) !important;
    box-shadow: 0 0 12px rgba(0,213,102,0.14) !important;
}
section[data-testid="stSidebar"] .stButton > button span,
section[data-testid="stSidebar"] .stButton > button p { color: #00D566 !important; }

/* ── Masthead ────────────────────────────────────────────────────────────── */
.market-status-badge {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 0.62rem; font-weight: 700; letter-spacing: 0.07em;
    padding: 3px 8px; border-radius: 5px;
    font-family: 'Inter', sans-serif !important;
}
.market-status-dot { width: 5px; height: 5px; border-radius: 50%; display: inline-block; }
.ua-header {
    display: flex; align-items: flex-end; justify-content: space-between;
    padding-bottom: 12px; margin-bottom: 0;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    position: relative;
}
.ua-header::after {
    content: '';
    position: absolute;
    bottom: -1px; left: 0;
    width: 140px; height: 2px;
    background: linear-gradient(90deg, #00D566, #00C8E0, #7C3AED);
    border-radius: 1px;
}
.ua-wordmark {
    font-size: 1.75rem; font-weight: 800; color: #E8EEFF;
    font-family: 'Inter', sans-serif; letter-spacing: -0.6px; line-height: 1.1;
}
.ua-wordmark span {
    background: linear-gradient(135deg, #00D566 0%, #00C8E0 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}
.ua-tagline {
    font-size: 0.73rem; color: #8892AA; font-family: 'Inter', sans-serif;
    margin-top: 2px; letter-spacing: 0.01em;
}
.ua-header-right {
    text-align: right; font-size: 0.73rem; color: #8892AA; font-family: 'Inter', sans-serif;
}
.ua-header-right b { color: #C8D0E4; font-weight: 600; }
.gold-rule {
    height: 1px;
    background: linear-gradient(90deg, rgba(0,213,102,0.5), rgba(0,200,224,0.3) 40%, rgba(124,58,237,0.3) 70%, transparent);
    border: none; margin: 0 0 14px 0;
}

/* ── Cards ───────────────────────────────────────────────────────────────── */
.metric-card {
    background: rgba(18,21,30,0.8);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px; padding: 16px 18px; margin-bottom: 10px;
    font-family: 'Inter', sans-serif;
    transition: all 0.2s cubic-bezier(0.4,0,0.2,1);
    position: relative; overflow: hidden;
}
.metric-card::before {
    content: ''; position: absolute; left: 0; top: 0; bottom: 0;
    width: 3px; background: rgba(255,255,255,0.08);
    border-radius: 12px 0 0 12px;
}
.metric-card.bull::before  { background: #00D566; }
.metric-card.bear::before  { background: #FF4444; }
.metric-card.neutral::before { background: #6B7FBF; }
.metric-card:hover {
    border-color: rgba(0,213,102,0.22);
    box-shadow: 0 0 24px rgba(0,213,102,0.07), 0 8px 24px rgba(0,0,0,0.4);
    transform: translateY(-2px);
}
.metric-card b { color: #E8EEFF; }
.metric-card span { color: #8892AA; }

.page-card {
    background: rgba(18,21,30,0.7);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px; padding: 18px 20px; margin-bottom: 10px;
    font-family: 'Inter', sans-serif;
    transition: all 0.22s cubic-bezier(0.4,0,0.2,1);
    position: relative; overflow: hidden;
}
.page-card::before {
    content: ''; position: absolute; left: 0; top: 0; bottom: 0;
    width: 3px;
    background: linear-gradient(180deg, #00D566, #7C3AED);
    border-radius: 12px 0 0 12px;
    opacity: 0; transition: opacity 0.2s ease;
}
.page-card:hover::before { opacity: 1; }
.page-card:hover {
    border-color: rgba(0,213,102,0.18);
    box-shadow: 0 0 24px rgba(0,213,102,0.07), 0 12px 32px rgba(0,0,0,0.5);
    transform: translateY(-2px);
}
.page-card .page-title { font-size: 0.94rem; font-weight: 600; color: #E8EEFF; margin-bottom: 4px; letter-spacing: -0.1px; }
.page-card .page-desc  { font-size: 0.79rem; color: #8892AA; line-height: 1.55; }

/* ── Section header ──────────────────────────────────────────────────────── */
.section-header {
    font-size: 0.63rem; font-weight: 700; color: #8892AA;
    font-family: 'Inter', sans-serif; letter-spacing: 0.13em;
    text-transform: uppercase;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    padding-bottom: 8px; margin-bottom: 14px;
}

/* ── Score numbers ───────────────────────────────────────────────────────── */
.score-number { font-size: 2.8rem; font-weight: 800; line-height: 1.0; font-family: 'Inter', sans-serif; letter-spacing: -1.5px; }
.score-bull {
    background: linear-gradient(135deg, #00D566, #00C8E0);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.score-bear {
    background: linear-gradient(135deg, #FF4444, #FF8888);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.score-neutral { color: #6B7FBF; }

/* ── Stat boxes ──────────────────────────────────────────────────────────── */
.stat-box {
    background: rgba(18,21,30,0.8); border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px; padding: 14px 16px; text-align: center;
    font-family: 'Inter', sans-serif;
    transition: all 0.2s cubic-bezier(0.4,0,0.2,1);
}
.stat-box:hover {
    border-color: rgba(0,213,102,0.2);
    box-shadow: 0 0 16px rgba(0,213,102,0.07);
    transform: translateY(-1px);
}
.stat-box .stat-label  { font-size: 0.60rem; text-transform: uppercase; letter-spacing: 0.11em; color: #8892AA; margin-bottom: 6px; font-weight: 700; }
.stat-box .stat-value  { font-size: 1.4rem; font-weight: 700; color: #E8EEFF; letter-spacing: -0.5px; }
.stat-box .stat-change { font-size: 0.76rem; margin-top: 3px; font-weight: 500; }
.stat-box .stat-change.pos  { color: #00D566; }
.stat-box .stat-change.neg  { color: #FF4444; }
.stat-box .stat-change.flat { color: #6B7FBF; }

/* ── Info / disclaimer ───────────────────────────────────────────────────── */
.disclaimer {
    background: rgba(18,21,30,0.6); border: 1px solid rgba(255,255,255,0.05);
    border-radius: 8px; padding: 10px 14px; font-size: 0.72rem;
    color: #8892AA; margin-top: 16px; font-family: 'Inter', sans-serif;
}
.info-box {
    background: rgba(0,213,102,0.05); border: 1px solid rgba(0,213,102,0.15);
    border-radius: 8px; padding: 12px 16px; margin-bottom: 12px;
    font-size: 0.83rem; color: #A8E8C0; font-family: 'Inter', sans-serif;
}

/* ── Tables ──────────────────────────────────────────────────────────────── */
.comparison-table { width: 100%; border-collapse: collapse; font-family: 'Inter', sans-serif; font-size: 0.83rem; }
.comparison-table th {
    background: rgba(0,213,102,0.08); color: #00D566;
    padding: 9px 12px; text-align: left; font-weight: 700;
    font-size: 0.62rem; letter-spacing: 0.08em; text-transform: uppercase;
    border-bottom: 1px solid rgba(0,213,102,0.18);
}
.comparison-table td { padding: 8px 12px; border-bottom: 1px solid rgba(255,255,255,0.04); color: #C8D0E4; }
.comparison-table tr:hover td { background: rgba(255,255,255,0.02); }
.comparison-table tr.highlight td { background: rgba(0,213,102,0.06); color: #E8EEFF; font-weight: 600; }

.ua-data-table { width: 100%; border-collapse: collapse; font-family: 'Inter', sans-serif; font-size: 0.81rem; }
.ua-data-table th {
    background: rgba(18,21,30,0.95); color: #8892AA;
    padding: 9px 12px; text-align: left; font-weight: 700;
    font-size: 0.60rem; letter-spacing: 0.10em; text-transform: uppercase;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
.ua-data-table td { padding: 9px 12px; border-bottom: 1px solid rgba(255,255,255,0.04); color: #B8C0D4; vertical-align: middle; }
.ua-data-table tr:hover td { background: rgba(255,255,255,0.02); transition: background 0.1s ease; }
.ua-data-table .bull    { color: #00D566; font-weight: 600; }
.ua-data-table .bear    { color: #FF4444; font-weight: 600; }
.ua-data-table .neutral { color: #6B7FBF; }

/* ── Streamlit native overrides ──────────────────────────────────────────── */
/* Metrics */
.stMetric label { color: #8892AA !important; font-size: 0.70rem !important; letter-spacing: 0.06em !important; font-family: 'Inter', sans-serif !important; text-transform: uppercase !important; font-weight: 600 !important; }
.stMetric [data-testid="stMetricValue"] { color: #E8EEFF !important; font-family: 'Inter', sans-serif !important; font-size: 1.65rem !important; font-weight: 700 !important; letter-spacing: -0.5px !important; }
.stMetric [data-testid="stMetricDelta"] { font-size: 0.78rem !important; font-weight: 500 !important; }

/* Expanders */
div[data-testid="stExpander"] { background: rgba(18,21,30,0.6) !important; border: 1px solid rgba(255,255,255,0.06) !important; border-radius: 10px !important; }
.streamlit-expanderHeader { color: #C8D0E4 !important; font-family: 'Inter', sans-serif !important; font-weight: 600 !important; font-size: 0.86rem !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"]  { border-bottom: 1px solid rgba(255,255,255,0.06) !important; gap: 0 !important; background: transparent !important; }
.stTabs [data-baseweb="tab"]       { font-family: 'Inter', sans-serif !important; font-size: 0.83rem !important; font-weight: 500 !important; padding: 8px 18px !important; color: #8892AA !important; background: transparent !important; border: none !important; }
.stTabs [aria-selected="true"]     { color: #E8EEFF !important; border-bottom: 2px solid #00D566 !important; font-weight: 600 !important; }
.stTabs [data-baseweb="tab-highlight"] { background: #00D566 !important; height: 2px !important; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 16px !important; }

/* Buttons */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    border-radius: 8px !important; font-weight: 500 !important; font-size: 0.83rem !important;
    transition: all 0.18s cubic-bezier(0.4,0,0.2,1) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    background: rgba(18,21,30,0.8) !important; color: #C8D0E4 !important;
}
.stButton > button:hover {
    border-color: rgba(0,213,102,0.4) !important; color: #00D566 !important;
    box-shadow: 0 0 14px rgba(0,213,102,0.12) !important;
    transform: translateY(-1px);
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #00D566, #00A847) !important;
    color: #001A0D !important; border: none !important; font-weight: 700 !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 0 22px rgba(0,213,102,0.35) !important; filter: brightness(1.05);
}

/* Inputs */
.stTextInput > div > div > input {
    background: rgba(18,21,30,0.8) !important; border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important; color: #E8EEFF !important;
    font-family: 'Inter', sans-serif !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.stTextInput > div > div > input:focus {
    border-color: rgba(0,213,102,0.5) !important;
    box-shadow: 0 0 0 3px rgba(0,213,102,0.08) !important; outline: none !important;
}
.stTextInput > div > div > input::placeholder { color: #8892AA !important; }

/* Selectbox */
.stSelectbox > div > div {
    background: rgba(18,21,30,0.8) !important; border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important; color: #E8EEFF !important; font-family: 'Inter', sans-serif !important;
}

/* Multiselect */
.stMultiSelect > div > div {
    background: rgba(18,21,30,0.8) !important; border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
}
.stMultiSelect span[data-baseweb="tag"] {
    background: rgba(0,213,102,0.10) !important; border-color: rgba(0,213,102,0.25) !important;
    color: #00D566 !important;
}

/* Number / Date input */
.stNumberInput > div > div > input,
.stDateInput > div > div > input {
    background: rgba(18,21,30,0.8) !important; border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important; color: #E8EEFF !important; font-family: 'Inter', sans-serif !important;
}

/* Sliders */
.stSlider [data-baseweb="slider"] [role="progressbar"] { background: linear-gradient(90deg, #00D566, #00C8E0) !important; }
.stSlider [data-baseweb="thumb"] { background: #00D566 !important; border-color: #00D566 !important; box-shadow: 0 0 8px rgba(0,213,102,0.5) !important; }

/* Toggle */
.stToggle [data-baseweb="switch"] [data-checked="true"] { background: #00D566 !important; }

/* Progress bars */
.stProgress > div > div > div { background: linear-gradient(90deg, #00D566, #00C8E0) !important; border-radius: 4px !important; }
.stProgress > div > div { background: rgba(255,255,255,0.05) !important; border-radius: 4px !important; }

/* Dividers */
hr { border-color: rgba(255,255,255,0.05) !important; opacity: 1 !important; }

/* Spinner */
.stSpinner > div { border-top-color: #00D566 !important; }

/* H1/H2/H3 */
h1, h2, h3 { color: #E8EEFF !important; font-family: 'Inter', sans-serif !important; font-weight: 700 !important; letter-spacing: -0.3px !important; }
h1 { font-size: 1.75rem !important; }
h2 { font-size: 1.3rem !important; }
h3 { font-size: 1.05rem !important; }
p  { color: #B8C0D4 !important; font-family: 'Inter', sans-serif !important; }

/* Radio / Checkbox */
.stRadio label, .stCheckbox label { color: #B8C0D4 !important; font-family: 'Inter', sans-serif !important; }

/* Caption */
.stCaption, small { color: #8892AA !important; font-family: 'Inter', sans-serif !important; }

/* Dataframe */
[data-testid="stDataFrame"] { border: 1px solid rgba(255,255,255,0.06) !important; border-radius: 10px !important; overflow: hidden !important; }

/* Alerts */
.stAlert { border-radius: 10px !important; border: none !important; }

/* Success/Info/Warning/Error alerts (dark-friendly backgrounds) */
div[data-testid="stAlertContainer"][data-baseweb="notification"][kind="success"] { background: rgba(0,213,102,0.08) !important; border: 1px solid rgba(0,213,102,0.2) !important; }
div[data-testid="stAlertContainer"][data-baseweb="notification"][kind="info"]    { background: rgba(0,200,224,0.08) !important; border: 1px solid rgba(0,200,224,0.2) !important; }
div[data-testid="stAlertContainer"][data-baseweb="notification"][kind="warning"] { background: rgba(245,158,11,0.08) !important; border: 1px solid rgba(245,158,11,0.2) !important; }
div[data-testid="stAlertContainer"][data-baseweb="notification"][kind="error"]   { background: rgba(255,68,68,0.08) !important; border: 1px solid rgba(255,68,68,0.2) !important; }

/* ── Mobile responsiveness ───────────────────────────────────────────────── */
/* Streamlit renders columns as flex on desktop; these overrides stack them
   gracefully on narrow viewports (phones / portrait tablets). */
@media (max-width: 768px) {
    /* Stack 4-col grids to 2 columns */
    [data-testid="stHorizontalBlock"] > [data-testid="stVerticalBlock"] {
        min-width: 45% !important;
    }
    /* Shrink hero headline on mobile */
    .hero-title { font-size: 1.9rem !important; }
    /* Reduce block-container padding on mobile */
    .block-container { padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
    /* Hide the live ticker strip on very narrow screens to prevent jank */
    .ticker-strip-outer { display: none !important; }
}
</style>
"""

# _DARK_CSS is kept for backward compat but no longer needed — dark IS the default.
_DARK_CSS = "<style>/* dark mode is now the default design */</style>"

_DARK_JS = ""  # No longer needed — dark is the permanent design.


def render_dark_mode_toggle() -> None:
    """No-op: dark mode is now the permanent base design, toggle removed."""
    pass


def render_synthetic_data_banner(n_synthetic: int, n_total: int) -> None:
    """
    Render an unmissable banner when any FRED-sourced data on the page is
    synthetic placeholder data (shown whenever no FRED API key is configured,
    or a live fetch failed). Intentionally loud — a quiet caption is how a
    user mistakes a fabricated chart for a real one.
    """
    if n_synthetic <= 0:
        return
    st.markdown(f"""
    <div style="background:rgba(255,68,68,0.08);color:#FF8888;border-radius:10px;padding:12px 18px;
                margin-bottom:14px;font-family:Inter,sans-serif;font-size:0.83rem;
                border:1px solid rgba(255,68,68,0.3);border-left:3px solid #FF4444;">
        <b style="color:#FF4444;">⚠ DEMO DATA</b> — {n_synthetic} of {n_total} signals on this page are showing
        synthetic placeholder data, not real values. This happens when no FRED API
        key is configured or a live fetch fails. Add a free key in the sidebar under
        "Setup" for real data — until then, treat any bullish/bearish reading from
        these signals as illustrative only.
    </div>
    """, unsafe_allow_html=True)


def ticker_label(ticker: str) -> str:
    """'TICKER (Full Company Name)' when the company name is known, else just the ticker."""
    company = TICKERS.get(ticker, {}).get("name", "")
    return f"{ticker} ({company})" if company else ticker


def go_to_ticker(ticker: str, key: str) -> None:
    """
    Render a clickable ticker chip showing "TICKER (Company Name)".
    On click: set session_state.selected_ticker and switch to Ticker Deep Dive.
    `key` must be globally unique across the page.
    """
    if st.button(ticker_label(ticker), key=key, help=f"Deep dive: {ticker}", use_container_width=True):
        st.session_state["selected_ticker"] = ticker
        st.switch_page("pages/3_Ticker_Deep_Dive.py")


def ticker_chips(tickers: list, key_prefix: str, per_row: int = 3) -> None:
    """
    Render clickable ticker chip buttons in a grid (default 3 per row, since
    each chip now shows the full company name and needs more width than a
    bare ticker symbol). `key_prefix` must be unique per call site.
    """
    if not tickers:
        return
    for row_start in range(0, len(tickers), per_row):
        row_tickers = tickers[row_start:row_start + per_row]
        cols = st.columns(per_row)
        for col, t in zip(cols, row_tickers):
            with col:
                go_to_ticker(t, key=f"chip_{key_prefix}_{t}")


def render_global_ticker_search() -> None:
    """
    Persistent, type-to-filter ticker search shown in the header on every
    page — jumps straight to Ticker Deep Dive on selection. Plain
    st.selectbox over every tracked ticker; Streamlit's selectbox already
    supports typing to filter a long option list, so this needed no
    custom component or JS.

    NAVIGATION-LOOP GUARD, verified live (not assumed) before shipping:
    a naive "if picked: switch_page()" would redirect every single time
    the header re-renders afterward, forever -- the selectbox's own
    session_state value persists across reruns, so `picked` stays truthy
    on every subsequent page load too. The fix is NOT to del the widget's
    session_state key after navigating -- that was tried first and
    crashes Streamlit's own widget-state bookkeeping on the next rerun
    (confirmed against a real AppTest run, not a guess). Instead, this
    compares the picked value against the last value actually acted on
    and only navigates when it's genuinely new.
    """
    options = sorted(TICKERS.keys())
    _, search_col, _ = st.columns([3, 2.2, 1.4])
    with search_col:
        picked = st.selectbox(
            "Jump to a ticker",
            options,
            index=None,
            placeholder="🔍 Search any ticker…",
            key="global_ticker_search",
            label_visibility="collapsed",
            format_func=ticker_label,
        )
    if picked and picked != st.session_state.get("_last_global_ticker_search"):
        st.session_state["_last_global_ticker_search"] = picked
        st.session_state["selected_ticker"] = picked
        st.switch_page("pages/3_Ticker_Deep_Dive.py")


def render_header(page_subtitle: str = "") -> None:
    """
    Inject global CSS and render the Unstructured Alpha masthead.
    Call this immediately after st.set_page_config() on every page.

    Args:
        page_subtitle: Short section name shown on the right side of the header bar
                       (e.g. "Signal Dashboard", "Market Overview").
    """
    from datetime import datetime

    st.markdown(_CSS, unsafe_allow_html=True)

    # ── OpenGraph / social meta tags (JS injection) ────────────────────────────
    # Reddit's link scraper is server-side and won't execute this JS, but
    # Googlebot (which does execute JS) and Twitter's card validator will.
    # The title tag set by st.set_page_config IS visible to all scrapers.
    st.markdown("""
<script>
(function() {
    var metas = [
        {property: 'og:site_name',    content: 'Unstructured Alpha'},
        {property: 'og:type',         content: 'website'},
        {property: 'og:url',          content: 'https://unstructuredalpha.com'},
        {property: 'og:title',        content: 'Unstructured Alpha — 43-Signal Macro Intelligence'},
        {property: 'og:description',  content: 'Score insider trades, credit spreads, energy inventories and 40 other signals daily. Free to browse. Pro $20/mo.'},
        {name:     'description',     content: 'Score insider trades, credit spreads, energy inventories and 40 other macro signals daily. Confluence Score for any stock. Free to browse.'},
        {name:     'twitter:card',    content: 'summary'},
        {name:     'twitter:title',   content: 'Unstructured Alpha — Alternative Data Intelligence'},
        {name:     'twitter:description', content: '43 macro signals scored daily. Free to browse. Insider trades, credit spreads, VIX term structure, copper/gold ratio and more.'},
    ];
    metas.forEach(function(m) {
        var el = document.createElement('meta');
        Object.keys(m).forEach(function(k) { el.setAttribute(k, m[k]); });
        document.head.appendChild(el);
    });
})();
</script>
""", unsafe_allow_html=True)

    # ── Live ticker strip ──────────────────────────────────────────────────────
    _render_live_ticker_strip()

    # Market open/closed status — NYSE regular hours, Mon-Fri 9:30-16:00 ET.
    # Best-effort only (no holiday calendar) — falls back to local time if
    # zoneinfo's tz database isn't available in the runtime environment.
    try:
        from zoneinfo import ZoneInfo
        _now_et = datetime.now(ZoneInfo("America/New_York"))
    except Exception:
        _now_et = datetime.now()
    _mins_et = _now_et.hour * 60 + _now_et.minute
    _market_open = (_now_et.weekday() < 5) and (9 * 60 + 30) <= _mins_et < 16 * 60
    _status_label = "MARKET OPEN" if _market_open else "MARKET CLOSED"
    _status_bg    = "rgba(0,213,102,0.10)" if _market_open else "rgba(255,68,68,0.08)"
    _status_fg    = "#00D566" if _market_open else "#FF4444"
    _status_dot   = "#00D566" if _market_open else "#FF4444"
    _time_str     = _now_et.strftime("%-I:%M %p ET")
    _date_str     = _now_et.strftime("%A, %B %-d, %Y")

    status_badge_html = (
        f'<span class="market-status-badge" style="background:{_status_bg};color:{_status_fg};">'
        f'<span class="market-status-dot" style="background:{_status_dot};"></span>{_status_label} · {_time_str}'
        f'</span>'
    )
    right_html = (
        f"<b>{page_subtitle}</b><br>{_date_str}<br>{status_badge_html}"
        if page_subtitle else f"{_date_str}<br>{status_badge_html}"
    )

    st.markdown(f"""
    <div class="ua-header">
        <div class="ua-header-left">
            <div class="ua-wordmark">UNSTRUCTURED <span>ALPHA</span></div>
            <div class="ua-tagline">Alternative Data Intelligence &mdash; what&rsquo;s coming, not what happened</div>
        </div>
        <div class="ua-header-right">{right_html}</div>
    </div>
    <div class="gold-rule"></div>
    """, unsafe_allow_html=True)

    # ── Sticky Macro Regime Bar ────────────────────────────────────────────────
    # One slim line visible on every page so users never lose macro context.
    # Uses the shared 2h cache — zero extra API cost.
    try:
        from utils.signals_cache import get_all_signal_scores as _gss
        _rs = _gss()
        _rb  = sum(1 for v in _rs.values() if not v.get("error") and v.get("status") == "bullish")
        _rr  = sum(1 for v in _rs.values() if not v.get("error") and v.get("status") == "bearish")
        _rn  = sum(1 for v in _rs.values() if not v.get("error") and v.get("status") == "neutral")
        _rto = max(1, _rb + _rr + _rn)
        _rbp = _rb / _rto
        _rrp = _rr / _rto
        if _rbp >= 0.58:
            _regime_lbl, _regime_col, _regime_bg = "RISK-ON", "#00D566", "rgba(0,213,102,0.06)"
        elif _rrp >= 0.52:
            _regime_lbl, _regime_col, _regime_bg = "RISK-OFF", "#FF4444", "rgba(255,68,68,0.06)"
        elif _rbp >= 0.48:
            _regime_lbl, _regime_col, _regime_bg = "LEANING BULLISH", "#00A847", "rgba(0,168,71,0.05)"
        elif _rrp >= 0.44:
            _regime_lbl, _regime_col, _regime_bg = "LEANING BEARISH", "#CC3333", "rgba(204,51,51,0.05)"
        else:
            _regime_lbl, _regime_col, _regime_bg = "MIXED SIGNALS", "#6B7FBF", "rgba(107,127,191,0.05)"
        st.markdown(
            f'<div style="background:{_regime_bg};border:1px solid rgba(255,255,255,0.06);'
            f'border-left:3px solid {_regime_col};'
            f'border-radius:8px;padding:6px 14px;margin-bottom:12px;'
            f'display:flex;align-items:center;gap:16px;font-family:Inter,sans-serif;">'
            f'<span style="font-size:0.60rem;color:#8892AA;text-transform:uppercase;letter-spacing:0.11em;font-weight:700;">MACRO REGIME</span>'
            f'<span style="font-size:0.75rem;font-weight:700;color:{_regime_col};">● {_regime_lbl}</span>'
            f'<span style="font-size:0.68rem;color:#8892AA;">'
            f'<span style="color:#00D566;">▲ {_rb}</span>'
            f' · <span style="color:#FF4444;">▼ {_rr}</span>'
            f' · <span style="color:#6B7FBF;">→ {_rn}</span>'
            f'</span>'
            f'<span style="font-size:0.60rem;color:#6B7FBF;margin-left:auto;">38 signals · 2h cache</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    except Exception:
        pass  # never crash the header for a cosmetic bar

    # Global ticker search -- same reasoning as the account widget below:
    # a real Streamlit widget can't live inside the markdown block above,
    # so it's rendered here in its own row, automatically on every page
    # that calls render_header() (all of them).
    render_global_ticker_search()

    # Top-right Sign In / account widget -- a real Streamlit popover, not
    # raw HTML, so it can't live inside the markdown block above (Streamlit
    # widgets don't render inside injected HTML). Rendered here so every
    # page gets it automatically just by calling render_header(), which
    # they all already do -- no per-page wiring needed, and no risk of a
    # page forgetting to add it.
    from utils.auth_ui import render_account_widget
    render_account_widget()

    # ── Notification Bell ──────────────────────────────────────────────────────
    # Shows unread system notification count + popover feed.
    # Best-effort — never crashes the header if DB is unavailable.
    try:
        from utils.prediction_log import (
            get_unread_notification_count, get_recent_notifications, mark_all_read
        )
        _uid = (st.session_state.get("user") or {}).get("id")
        _unread = get_unread_notification_count(_uid)
        _badge_html = (
            f'<sup style="background:#FF4444;color:#fff;font-size:0.55rem;'
            f'padding:1px 4px;border-radius:6px;margin-left:1px;">{min(_unread, 99)}</sup>'
            if _unread > 0 else ""
        )
        # Render bell using a popover (Streamlit ≥1.32)
        _bell_col, _pad = st.columns([0.12, 0.88])
        with _bell_col:
            with st.popover(f"🔔{_badge_html if _unread else ''}", use_container_width=True):
                st.markdown(
                    '<div style="font-size:0.62rem;font-weight:700;color:#8892AA;letter-spacing:0.12em;'
                    'text-transform:uppercase;margin-bottom:10px;border-bottom:1px solid rgba(255,255,255,0.06);'
                    'padding-bottom:6px;font-family:Inter,sans-serif;">System Notifications</div>',
                    unsafe_allow_html=True,
                )
                _notifs = get_recent_notifications(limit=15)
                if not _notifs:
                    st.caption("No notifications yet. Convergence events and prediction resolutions will appear here.")
                else:
                    _NOTIF_ICONS = {
                        "convergence":          "⚡",
                        "regime_change":        "📈",
                        "near_flip":            "⏳",
                        "prediction_resolved":  "📊",
                    }
                    for _n in _notifs:
                        _icon = _NOTIF_ICONS.get(_n.get("notif_type", ""), "●")
                        _n_bg = "rgba(0,213,102,0.06)" if _n.get("direction") == "bull" else (
                                "rgba(255,68,68,0.06)" if _n.get("direction") == "bear" else "rgba(18,21,30,0.6)"
                        )
                        _n_border = "#00D566" if _n.get("direction") == "bull" else (
                                    "#FF4444" if _n.get("direction") == "bear" else "rgba(255,255,255,0.07)"
                        )
                        _n_ts = _n.get("created_at", "")[:10]
                        st.markdown(
                            f'<div style="background:{_n_bg};border-radius:8px;padding:8px 10px;'
                            f'margin-bottom:6px;border-left:3px solid {_n_border};font-family:Inter,sans-serif;">'
                            f'<div style="font-size:0.76rem;font-weight:600;color:#E8EEFF;">'
                            f'{_icon} {_n.get("title","")}</div>'
                            f'<div style="font-size:0.70rem;color:#8892AA;margin-top:3px;line-height:1.4;">'
                            f'{_n.get("body","")}</div>'
                            f'<div style="font-size:0.60rem;color:#8892AA;margin-top:4px;">{_n_ts}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                if _unread > 0 and _uid:
                    if st.button("Mark all read", key="_notif_mark_read", use_container_width=True):
                        mark_all_read(_uid)
                        st.rerun()
    except Exception:
        pass  # Never crash the header for a notification badge


@st.cache_data(ttl=60, max_entries=1, show_spinner=False)
def _fetch_ticker_strip():
    """Fetch live prices for the header ticker strip. 60s TTL, one set of symbols."""
    import yfinance as yf
    _SYMBOLS = [
        ("SPY",    "S&P 500"),
        ("QQQ",    "Nasdaq"),
        ("BTC-USD","Bitcoin"),
        ("GC=F",   "Gold"),
        ("CL=F",   "WTI Oil"),
        ("^VIX",   "VIX"),
    ]
    results = []
    try:
        tickers = yf.Tickers(" ".join(s for s, _ in _SYMBOLS))
        for sym, label in _SYMBOLS:
            try:
                info = tickers.tickers[sym].fast_info
                price = getattr(info, "last_price", None)
                prev  = getattr(info, "previous_close", None)
                if price and prev and prev > 0:
                    chg_pct = (price - prev) / prev * 100
                    results.append((sym, label, price, chg_pct))
            except Exception:
                pass
    except Exception:
        pass
    return results


def _render_live_ticker_strip() -> None:
    """
    Render a horizontal live price ticker strip above the UA masthead.
    Bloomberg/CNBC-style: symbol · price · ▲/▼ ±x.xx%, green=up red=down.
    Updates every 60 seconds via TTL cache.
    """
    items = _fetch_ticker_strip()
    if not items:
        return

    chips = []
    for sym, label, price, chg in items:
        arrow = "▲" if chg >= 0 else "▼"
        color = "#00D566" if chg >= 0 else "#FF4444"
        # Format price (crypto needs more decimals)
        p_fmt = f"${price:,.0f}" if price >= 100 else f"${price:,.2f}"
        chips.append(
            f'<span style="display:inline-flex;align-items:center;gap:6px;'
            f'padding:0 14px;border-right:1px solid rgba(255,255,255,0.06);">'
            f'<span style="color:#8892AA;font-weight:600;font-size:0.68rem;">{sym}</span>'
            f'<span style="color:#E8EEFF;font-weight:700;font-size:0.70rem;">{p_fmt}</span>'
            f'<span style="color:{color};font-size:0.68rem;font-weight:600;">{arrow} {abs(chg):.2f}%</span>'
            f'</span>'
        )

    inner = "".join(chips)
    # Duplicate for seamless marquee loop
    ticker_html = f"""
<div style="background:rgba(12,14,20,0.95);border-bottom:1px solid rgba(255,255,255,0.05);
             overflow:hidden;white-space:nowrap;padding:5px 0;margin-bottom:0;
             font-family:Inter,sans-serif;">
  <div style="display:inline-flex;animation:tickerScroll 28s linear infinite;">
    {inner}{inner}
  </div>
</div>
<style>
@keyframes tickerScroll {{
  0%   {{ transform: translateX(0); }}
  100% {{ transform: translateX(-50%); }}
}}
</style>
"""
    st.markdown(ticker_html, unsafe_allow_html=True)


def render_page_header(title: str, subtitle: str = "",
                       icon: str = "", live_stat: str = "") -> None:
    """
    Bold gradient page title with subtitle and optional live right-side stat.
    Call after render_header() at the top of each page.

    Args:
        title:     Page title — displayed with bold gradient text.
        subtitle:  One-line description of what the page does.
        icon:      Optional emoji/icon prefix for the title (e.g. "📊").
        live_stat: Optional right-aligned stat string (e.g. "38 signals active").
    """
    icon_html = f'<span style="margin-right:8px;">{icon}</span>' if icon else ""
    stat_html = (
        f'<div style="text-align:right;font-size:0.72rem;color:#6B7FBF;font-weight:600;'
        f'letter-spacing:0.06em;">{live_stat}</div>'
    ) if live_stat else ""
    sub_html = (
        f'<div style="font-size:0.85rem;color:#8892AA;margin-top:3px;line-height:1.4;'
        f'font-weight:400;">{subtitle}</div>'
    ) if subtitle else ""

    st.markdown(f"""
<div style="display:flex;align-items:flex-start;justify-content:space-between;
            margin:10px 0 18px;padding-bottom:14px;
            border-bottom:1px solid rgba(255,255,255,0.06);">
    <div>
        <div style="font-size:1.85rem;font-weight:800;letter-spacing:-0.6px;line-height:1.15;
                    font-family:Inter,sans-serif;">
            {icon_html}<span style="background:linear-gradient(135deg,#E8EEFF 0%,#B8C0D4 100%);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">{title}</span>
        </div>
        {sub_html}
    </div>
    {stat_html}
</div>
""", unsafe_allow_html=True)


def render_sidebar_base() -> None:
    """
    Render the standard sidebar content (account info, FRED key input, AI
    assistant link, disclaimer). Call inside a `with st.sidebar:` block or
    standalone.
    """
    with st.sidebar:
        # Account info — most pages no longer require login (per explicit
        # user request), so an anonymous visitor is a completely normal,
        # expected case here, not an edge case. This sidebar block is just
        # a secondary "you're logged in" indicator + quick Log Out; the
        # actual sign-in entry point is the top-right widget rendered by
        # render_header() (utils.auth_ui.render_account_widget()).
        user = st.session_state.get("user")
        if user:
            st.markdown(
                f'<div style="font-size:0.78rem;color:#8892AA;margin-bottom:4px;">'
                f'Logged in as<br><b style="color:#E8EEFF;">{user["email"]}</b></div>',
                unsafe_allow_html=True,
            )
            if st.button("Log Out", key="sidebar_logout", use_container_width=True):
                from utils.auth_ui import logout
                logout()
                st.rerun()
            st.divider()

        # Dark mode toggle — persists preference in localStorage
        render_dark_mode_toggle()
        st.divider()

        # AI Assistant quick-access
        st.markdown(
            '<div style="background:rgba(184,134,11,0.13);border-radius:6px;padding:10px 12px;'
            'border:1px solid rgba(184,134,11,0.35);margin-bottom:10px;">'
            '<div style="font-size:0.68rem;color:#C9A84C;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;">AI Research Assistant</div>'
            '<div style="font-size:0.79rem;color:#D4C9B0;margin-top:3px;line-height:1.4;">'
            'Questions about signals, tickers, or methodology?</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.page_link("pages/9_AI_Assistant.py", label="Open AI Assistant")

        st.divider()
        st.markdown(
            '<div style="font-size:0.72rem;color:rgba(201,168,76,0.55);line-height:1.5;padding:0 2px;">'
            '<b style="color:rgba(201,168,76,0.70);">Not financial advice.</b> '
            'All signals are interpretations of publicly available data. '
            'Do your own research before making any investment decision.'
            '</div>',
            unsafe_allow_html=True,
        )
