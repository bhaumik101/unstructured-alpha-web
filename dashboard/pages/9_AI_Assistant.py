"""
Page 9 — AI Research Assistant
Conversational assistant with deep knowledge of the Unstructured Alpha platform.
Answers questions about signals, methodology, pages, tickers, and walkthroughs.
Optionally integrates with Claude API for advanced Q&A.
"""

import streamlit as st
from utils.header import render_header, render_sidebar_base

st.set_page_config(page_title="AI Assistant — UA", layout="wide")
render_header("AI Research Assistant")
render_sidebar_base()


# ─────────────────────────────────────────────────────────────────────────────
# Knowledge base — comprehensive app context injected into every AI response
# ─────────────────────────────────────────────────────────────────────────────
APP_CONTEXT = """
You are the Unstructured Alpha Research Assistant — an expert on the Unstructured Alpha
alternative data intelligence platform. You help users understand the platform's methodology,
interpret signals, navigate pages, and think through investment theses.

PLATFORM OVERVIEW:
Unstructured Alpha uses non-traditional, "alternative" data sources to give investors a
forward-looking edge over conventional financial data. The core idea: alternative data
leads price by weeks or months, while earnings reports and consensus estimates lag reality.

THE PAGES (Signal Analysis and Macro Monitor were consolidated into Ticker Deep
Dive and Market Overview respectively in 2026 to cut down on redundant pages —
if you remember those as separate pages, the same tools are now inside the
pages below):

1. Signal Dashboard — Real-time overview of every tracked macro signal, sorted
   by significance, showing bull/bear/neutral status for each. Simple mode
   (plain-English, traffic-light style) and Pro mode (z-scores, percentiles,
   correlation) toggle. Color-coded, with a banner that flags when any signal
   is showing synthetic demo data instead of real values.

2. Ticker Deep Dive — The flagship page. Enter any ticker for:
   - Confluence Score (0-100) weighted by per-signal correlation with that ticker's price
   - A 30/60/90-day forward probability model (bull/bear/neutral %, price ranges)
   - Bull & Bear Case narrative
   - Signal breakdown table — now filtered to statistically significant signals
     (p<0.05) only, with a separate "Not Statistically Significant" section
     showing what was excluded and why, instead of mixing noise into the score
   - "TOP SIGNAL DRIVERS" cards showing the highest-impact signals
   - Deep Correlation Scan — Lead Time Optimizer: pick one signal and see the
     optimal lag (0-16 week scan), rolling 26-week correlation stability, and
     a signal+price overlay chart (this absorbed the old standalone Signal
     Analysis page)
   - Federal contract award velocity (government revenue visibility)
   - SEC Form 4 insider transaction overlay

3. Power Supercycle — Five-leg thesis tracker (nuclear fuel, grid & copper, gas
   bridge, AI demand, macro backdrop) for the AI infrastructure / nuclear power
   / commodity supercycle. Signal trends shown as small-multiple charts (one
   panel per leg, not all signals crammed onto one unreadable chart), with a
   1H-to-ALL time window selector. Includes real federal contract award data
   and arXiv quantum-paper publication velocity as genuine alternative data —
   not equity-ETF prices repackaged as "signals."

4. Market Overview — Daily snapshot: major indices with sparklines, sector
   performance, rates & fixed income, commodities, normalized performance
   chart, and a Signal Snapshot (VIX, yield curve, HY credit, 10Y yield trend,
   risk appetite). Also now includes the former Macro Monitor content: Growth
   Indicators (ATA Trucking, ISM PMI, Durable Goods), Labor Market (Jobless
   Claims, JOLTS, Rail Traffic), Consumer & Inflation (Consumer Sentiment,
   Retail Sales, Food CPI), the official FRED 10Y-2Y yield curve, and an
   Economic Releases calendar.

5. Stock Screener — Rank all tracked tickers by alternative data confluence
   score. Filters: sector, signal bias, min PCS, score range, text search.
   Click any row for inline preview. "Quick Analyze Any Ticker" box for custom
   tickers outside the universe.

6. About & Methodology — Signal library reference with a "Run Live Backtest"
   button that computes a REAL Predictive Confidence Score from actual
   correlation + significance testing against live data, rather than relying
   only on the hand-assigned static PCS every signal starts with.

7. AI Assistant (this page) — You are here.

KEY SIGNALS EXPLAINED:
- ATA Trucking Tonnage (PCS 9/10): Monthly index of freight weight moved by US trucks.
  Covers ~70% of all domestic freight. Precedes ISM PMI by 6-8 weeks. A drop = early
  warning of inventory drawdowns and spending slowdowns. Source: FRED TRUCKD11.

- Rail Traffic / Intermodal (PCS 9/10): Weekly AAR intermodal container volume.
  Signals import demand 4-8 weeks before trade statistics. Source: FRED RAILFRTINTERMODAL.

- Jobless Claims (PCS 9/10): Weekly initial unemployment claims (FRED IC4WSA). Acts as
  real-time proxy for WARN Act mass layoff activity. INVERSE: rising claims = bearish.

- Yield Curve 10Y-2Y (PCS 9/10): Spread between 10-year and 2-year Treasury yields.
  INVERSE: inversion (negative spread) has preceded every recession since 1955, with
  6-18 month lead time. Source: FRED T10Y2Y (also computed live from ^TNX-^IRX).

- HY Credit Spread (PCS 9/10): ICE BofA US High Yield OAS. Widens when credit markets
  price in default risk — hits leveraged companies 4-8 weeks before equity repricing.
  INVERSE: widening spread = bearish. Source: FRED BAMLH0A0HYM2.

- VIX (PCS 8/10): CBOE Volatility Index — "fear gauge." INVERSE: low VIX = calm = bullish.
  VIX > 25 = elevated stress. VIX > 40 = crisis/potential capitulation low.
  Source: yfinance ^VIX.

- 10-Year Treasury Yield (PCS 8/10): INVERSE: rising yields = headwind for growth stocks
  and real estate. Yield > ~4.5% = growth stock multiple compression.
  Source: yfinance ^TNX.

- ISM PMI (PCS 7/10): Manufacturing PMI above 50 = expansion, below 50 = contraction.
  Leads manufacturing-adjacent stock earnings by one quarter. Source: FRED
  GACDFSA066MSFRBPHI (Philly Fed) — the legacy NAPM series was discontinued by
  FRED in 2016 and has been replaced.

- Crude Oil Inventories (PCS 8/10): Weekly US crude stocks ex-SPR. The single
  fastest-moving oil price signal, released every Wednesday. INVERSE: draws are
  bullish for oil, builds are bearish. Source: EIA series PET.WCESTUS1.W.

- US Natural Gas Storage (PCS 7/10): Weekly Lower-48 working gas in underground
  storage. INVERSE: below the 5-year average is bullish for Henry Hub prices.
  Source: EIA series NG.NW2_EPG0_SWO_R48_BCF.W.

- Senior Loan Officer Survey / Bank Lending Standards (PCS 8/10): Net % of banks
  tightening C&I lending standards, from the Fed's quarterly SLOOS. INVERSE:
  tightening = bearish for credit-sensitive financials. Genuine alt-data
  differentiator — credit desks watch this closely, retail platforms rarely show it.
  Source: FRED DRTSCILM.

- Credit Card Delinquency Rate (PCS 7/10): Quarterly delinquency rate across all
  commercial banks. INVERSE: rising delinquencies = consumer credit stress.
  Source: FRED DRCCLACBS.

- FDA Drug Approval Velocity (PCS 6/10): Weekly count of FDA drug approvals
  industry-wide, pulled live from openFDA. Genuine alt-data differentiator for
  healthcare — the kind of regulatory read analysts normally track by hand.
  Source: openFDA drugsfda endpoint (api.fda.gov, no key required).

- Retail Trade Job Openings (PCS 6/10): Sector-specific JOLTS openings for
  retail trade — a real-time read on retailer hiring confidence ahead of demand.
  Source: FRED JTS4400JOL.

- E-Commerce Share of Retail Sales (PCS 5/10): Structural online-vs-physical
  retail shift, not a tactical signal. Source: FRED ECOMPCTSA.

- Total US Construction Spending (PCS 6/10): Broad industrials demand gauge for
  materials, equipment rental, and heavy-construction names. Source: FRED TTLCONS.

- Hyperscaler CapEx (PCS 8/10): Composite CapEx from MSFT, AMZN, GOOGL, META. The cleanest
  demand signal for power infrastructure. Leads data center power demand by 2-5 years.
  Source: yfinance quarterly financials basket.

- Uranium Proxy (PCS 8/10): Price of Global X Uranium ETF (URA) as proxy for uranium demand.
  Nuclear fuel cycle demand precedes utility revenue by 12-24 months.
  Source: yfinance URA.

- Quantum arXiv Velocity (PCS 5/10 — intentionally low, unbacktested): weekly count of
  arXiv quant-ph preprints on qubit error correction. Real research-output data, not a
  stock price. Replaced the old "Quantum Computing Basket" signal, which was IonQ/Rigetti/
  D-Wave stock prices being used to predict the same IonQ/Rigetti/D-Wave stocks — circular,
  not alternative data. Several other signals (nuclear enrichment basket, SMR sentiment
  basket, lithium/rare-earth/defense/biotech/cybersecurity/robotics/water ETF "proxies")
  were removed for the same reason: an ETF's price is just an aggregate of the stocks it
  claims to predict. Those tickers are still tracked, just mapped to real macro signals
  (copper, dollar index, ISM PMI, yield, credit spreads) instead of their own price.

SCORING METHODOLOGY:
- Each signal is scored 0-100 based on recent trend vs. historical distribution (Z-score percentile)
- Scores below 35 = BEARISH, 35-65 = NEUTRAL, above 65 = BULLISH
- Confluence Score = weighted average across all relevant signals for a ticker
- Weights = max(0.15, |Pearson r|) × (PCS/10) — each signal weighted by its correlation
  with that specific ticker's price × signal quality score
- Statistical significance on Ticker Deep Dive: signals are tested for real p<0.05
  significance against that ticker's price. Only significant signals (plus enough
  non-significant ones to guarantee at least 3 shown, clearly labeled) appear in the
  main driver table; the rest are shown separately under "Not Statistically Significant"
  instead of being silently dropped
- PCS itself can now be backtested rather than taken on faith: the About page's "Run Live
  Backtest" button recomputes PCS from real correlation + significance against live data
- Conviction levels: Extreme Bull/Bear (score >80 or <20), Strong (>70 or <30),
  Moderate (>60 or <40), Neutral otherwise

TICKER CATEGORIES:
- Nuclear/Uranium: CCJ, LEU, UEC, UUUU, URA, NLR, CEG, VST, SMR
- AI Infrastructure: FCX, WMB, GEV, PWR, VRT, NVDA, MSFT, AMZN, GOOGL, META, EQIX, DLR
- Macro/Transport: SPY, QQQ, IWM, UNP, CSX, ODFL, JBHT, UPS, FDX, CAT, DE
- Energy: XOM, CVX, OXY, COP, HAL, SLB, BKR
- Financials: JPM, BAC, GS, KRE
- Agriculture: ADM, BG, MOS, NTR, KR
- Homebuilders: DHI, LEN, PHM, TOL
- Utilities: NEE, D, EXC, DUK, SO

WALKTHROUGH GUIDANCE:
For new users: Start with Signal Dashboard to see what signals are saying broadly.
Then go to Market Overview for the macro picture. Use Stock Screener to find which
tickers have the strongest bull/bear cases right now. Click a row and navigate to
Ticker Deep Dive for the full breakdown.

For a specific thesis (e.g., nuclear): Go to Ticker Deep Dive, select CCJ. Look at the
Confluence Score and signal drivers. Then compare with LEU, CEG, VST for differentiation.
The scores are now differentiated by each ticker's historical price correlation with each signal.

IMPORTANT DISCLAIMERS:
- All signals are research tools, not buy/sell recommendations
- Without a FRED API key, macro signals use synthetic/demo data — add a free FRED key
  in Setup for live data
- Data is delayed; yfinance data typically delayed 15 minutes for equities
"""


# ─────────────────────────────────────────────────────────────────────────────
# Rule-based fallback answers (fast, no API needed)
# ─────────────────────────────────────────────────────────────────────────────
QUICK_ANSWERS = {
    # How to use
    ("how do i start", "where do i begin", "getting started", "new user", "first time"): """
**Welcome to Unstructured Alpha!** Here's how to get started:

1. **Signal Dashboard** — Start here. See all 20+ macro signals color-coded by status.
2. **Market Overview** — Get the daily macro snapshot: indices, sectors, rates, commodities.
3. **Stock Screener** — Find tickers ranked by alternative data strength. Filter by sector or bias.
4. **Ticker Deep Dive** — Enter any ticker for a full signal breakdown and confluence score.

Tip: Add a free **FRED API key** in the sidebar Setup section for live macro data instead of demo data.
""",

    # Signal Dashboard
    ("signal dashboard", "what is signal dashboard", "explain signal dashboard"): """
**Signal Dashboard** is your real-time macro signal overview.

It shows every tracked alternative data signal with a **bullish/bearish/neutral** status based on recent trend vs. history.

- **Green (Bull)**: Signal is pointing positive for equities
- **Red (Bear)**: Signal is pointing negative — risk-off
- **Gold (Neutral)**: Signal in normal range, no strong directional read

Use it to quickly assess the macro environment before diving into individual tickers. Think of it like a weather dashboard — is the macro backdrop supportive or hostile?
""",

    # Ticker Deep Dive
    ("ticker deep dive", "deep dive", "how does the analysis work", "explain the score"): """
**Ticker Deep Dive** is the flagship page. Here's what it shows:

**Confluence Score (0–100):**
- 0–35 = BEAR case
- 35–65 = NEUTRAL
- 65–100 = BULL case

The score is a **weighted average** of all signals assigned to that ticker. Weights combine:
- Signal quality (PCS, 1-10 scale)
- Historical Pearson correlation of that signal with the ticker's price

So two tickers in the same sector (e.g. CCJ and LEU, both uranium miners) get **different scores** because each signal's weight is calibrated to how strongly that signal historically moved *that specific stock's price*.

**TOP SIGNAL DRIVERS** shows the 3 signals with the highest impact (|r| × |score-50|).

Below that is the full signal table, sorted by impact, with correlation (r) and status for each.

IMPORTANT: this score describes how many signals currently agree, not a validated forecast.
See the "confluence score" topic below for the backtest finding.
""",

    # Confluence score
    ("confluence score", "what does score mean", "how is score calculated"): """
The **Confluence Score** (0-100) measures how many alternative data signals are CURRENTLY aligning bullishly or bearishly for a specific ticker.

**Formula:**
```
Weight per signal = max(0.15, |Pearson r|) × (PCS / 10)
Confluence = weighted average of individual signal scores
```

Where:
- **PCS** = Predictive Capability Score (1-10), our assessment of how reliable this signal is historically
- **Pearson r** = correlation between the signal's trend and the ticker's price return over the past 2 years
- **0.15 floor** ensures no signal is completely nullified even with low correlation

**Thresholds:**
- **> 65** = BULL (positive confluence)
- **< 35** = BEAR (negative confluence)
- **35–65** = NEUTRAL or MIXED

**Conviction levels:** Extreme Bull/Bear > 80/<20, Strong > 70/<30, Moderate > 60/<40 — these
measure AGREEMENT among signals, not proven accuracy.

**Has this been backtested?** Yes, honestly: we walk-forward backtested the real Confluence and
Power Supercycle scoring functions against 6 tickers (CEG, VST, NEE, ETN, VRT, PWR), ~19 monthly
checkpoints, no lookahead. Pooled result: no statistically significant relationship with 1/2/3-month
forward returns (all |r| < 0.07). Two tickers showed a significant negative relationship in
isolation before pooling washed it out. Conclusion: treat this score as a real-time read of signal
agreement, not a forecast, until a bigger backtest proves otherwise. Full numbers on the About page.
""",

    # VIX
    ("vix", "fear index", "volatility index"): """
**VIX — CBOE Volatility Index** (PCS 8/10)

The "fear gauge." Measures implied 30-day volatility of S&P 500 options. **Inverse signal**: low VIX = calm markets = bullish for equities.

**Level thresholds:**
- VIX < 15 = Complacency / Calm → Bullish
- VIX 15-25 = Normal range → Neutral
- VIX > 25 = Elevated stress → Bearish
- VIX > 40 = Crisis / Capitulation (contrarian BUY signal historically)

**Key history:** VIX hit 66 in March 2020 — the peak marked a generational buying opportunity within 3 trading days.

In the app: VIX is used as an inverse signal for most tickers. It's most impactful for financials (GS, XLF), uranium miners (CCJ, LEU), and levered plays (OXY, SMR).
""",

    # Yield curve
    ("yield curve", "10y 2y", "inversion", "inverted", "spread"): """
**Yield Curve Spread (10Y–2Y)** (PCS 9/10)

The 10-year minus 2-year Treasury yield spread. **The most reliable recession predictor** in modern history.

- **Positive spread** (normal): Banks earn more lending long than borrowing short → credit expansion → growth
- **Inverted (negative)**: The market expects the Fed to cut rates as growth slows → credit tightening → recession watch

**Historical accuracy:** Every U.S. recession since 1955 was preceded by a yield curve inversion, typically 6-18 months in advance.

**In the app:** Scored as INVERSE (inversion = bearish). The lag is ~52 weeks (12 months), the longest of any signal.

**Live in Market Overview:** The "Yield Curve Spread" card shows real-time TNX - IRX spread with color-coded normal/inverted label.
""",

    # ATA trucking
    ("ata trucking", "trucking", "freight", "tonnage"): """
**ATA Trucking Tonnage Index** (PCS 9/10)

Monthly index of freight weight moved by U.S. Class-8 trucks. Covers approximately 70% of all domestic freight by value. Formally included in the Conference Board Leading Economic Indicators.

**Why it leads:** Trucks move almost everything. A drop in tonnage precedes inventory drawdowns and consumer spending slowdowns by 6-8 weeks — before the slowdown shows up in ISM or retail sales.

**Key cases:**
- March 2018 peak → 14 months before manufacturing ISM entered contraction (Aug 2019)
- Feb 2020 drop of 5.7% → First COVID signal before any official economic data showed it

**Relevant tickers:** JBHT, ODFL, SAIA, WERN, UPS, FDX, XLI, SPY

**Source:** FRED series TRUCKD11. Requires FRED API key for live data; demo mode uses synthetic data.
""",

    # Stock screener
    ("stock screener", "screener", "how do i find stocks", "best tickers"): """
**Stock Screener** ranks all 80+ tracked tickers by their alternative data confluence score.

**How to use:**
1. Use the sidebar filters: select sectors, signal bias (bull/bear/neutral), min signal quality (PCS), and score range
2. Use the **text search box** to filter by ticker symbol or company name
3. Click any row to see an inline preview with score, case, and bull/bear signal count
4. Click the Ticker Deep Dive link to go deep on any selected ticker

**"Quick Analyze Any Ticker"** at the top — enter *any* ticker (TSLA, BRK-B, PLTR, etc.) even if it's outside our tracked universe. The app auto-maps signals by sector for a quick confluence score.

**Reading the results:**
- Sorted by score descending (strongest bull cases first)
- ProgressColumn bar shows score visually
- "Bull" and "Bear" columns show how many signals point each direction
""",

    # Nuclear thesis
    ("nuclear", "uranium", "nuclear power", "ccj", "leu", "smr"): """
**Nuclear/Uranium Thesis in Unstructured Alpha**

The app tracks 9 nuclear/uranium tickers across the thesis:

**Miners:** CCJ (Cameco), UEC (Uranium Energy), UUUU (Energy Fuels), LEU (Centrus)
**ETFs:** URA (Global X Uranium), NLR (VanEck Nuclear)
**Utilities:** CEG (Constellation), VST (Vistra), SMR (NuScale)

**Key signals for nuclear:**
- `uranium_proxy` (URA ETF price) — direct demand signal
- `hyperscaler_capex` — AI data center power demand drives nuclear offtake agreements
- `natural_gas` — competing power source; gas price affects nuclear economics
- `ten_year_yield` — rate-sensitive capital projects
- `hy_spread` — credit conditions for capital-intensive companies
- `vix` — risk-on/off affects speculative names (UUUU, SMR)

**Score differentiation:** Each nuclear ticker gets a unique score because the signal weights are calibrated by historical price correlation. CCJ (pure uranium miner) responds more to uranium_proxy. VST (power generator) responds more to natural_gas and hyperscaler_capex.
""",

    # HY spread / credit
    ("hy spread", "credit spread", "high yield", "hyg"): """
**High-Yield Credit Spread** (PCS 9/10) — The market's forward-looking stress detector.

**What it is:** ICE BofA US High Yield Option-Adjusted Spread (OAS) — the extra yield investors demand to hold junk bonds vs. equivalent-maturity Treasuries.

**Why it leads equities:** HY spreads widen when credit markets price in default risk *before* equity analysts downgrade companies. This hits leveraged companies, banks, and growth stocks first — typically 4-8 weeks before the equity repricing.

**Inverse signal:** Widening spread = bearish for equities. Tightening = bullish.

**Current read (in Market Overview):** The HYG ETF price is used as a live yfinance proxy — HYG rising = spreads tightening = bullish.

**Source:** FRED series BAMLH0A0HYM2. Live data requires FRED API key.
""",

    # FRED API key
    ("fred", "fred api", "api key", "fred key", "live data", "real data"): """
**FRED API Key Setup**

FRED (Federal Reserve Economic Data) provides the live data for signals like:
- ATA Trucking Tonnage
- Yield Curve Spread
- HY Credit Spread (ICE BofA OAS)
- Jobless Claims
- Housing Starts
- Consumer Sentiment
- Retail Sales
- ISM PMI

**Without a key:** The app runs in "demo mode" with synthetic data that mimics signal patterns. All pages work, but macro signal scores will be neutral/synthetic.

**To get a free key:**
1. Go to https://fred.stlouisfed.org/docs/api/api_key.html
2. Create a free St. Louis Fed account
3. Request an API key (instant)
4. Paste it in the **Setup > Configure API Keys** section in the sidebar on any page

Once added, all FRED-sourced signals refresh every hour with live data.
""",

    # EIA API key
    ("eia", "eia api", "eia key", "crude inventories", "gas storage"): """
**EIA API Key Setup**

EIA (Energy Information Administration) provides the live data for two signals:
- US Crude Oil Inventories ex-SPR (series PET.WCESTUS1.W)
- US Natural Gas Storage, Lower-48 (series NG.NW2_EPG0_SWO_R48_BCF.W)

**Without a key:** these two signals run in "demo mode" with synthetic data, same as FRED signals without a FRED key.

**To get a free key:**
1. Go to https://www.eia.gov/opendata/register.php
2. Enter your email — EIA emails the key instantly, no account password needed
3. Paste it in the **Setup > Configure API Keys** section in the sidebar on any page

Note: EIA does not publish a free, API-queryable Baker Hughes rig count — that figure is licensed data only available inside their static Drilling Productivity Report, so it was removed from the signal library rather than faked.
""",

    # Power supercycle
    ("power supercycle", "supercycle", "ai power", "energy demand"): """
**Power Supercycle Thesis**

The Power Supercycle page tracks the multi-year thesis that AI infrastructure buildout is driving unprecedented electricity demand growth — the largest grid upgrade since rural electrification in the 1930s.

**Three linked catalysts:**
1. **AI Compute Demand** — Hyperscaler CapEx (MSFT+AMZN+GOOGL+META) is at all-time highs. Each AI training cluster requires 50-100MW+ of dedicated power.
2. **Nuclear Renaissance** — Data center companies (Microsoft, Google, Amazon) are signing direct nuclear offtake agreements. CEG, VST, SMR are benefiting.
3. **Grid Infrastructure Build** — Copper, transformers, transmission lines, and grid construction (FCX, PWR, GEV) are in multi-year supercycle.

**Key signals:** hyperscaler_capex (primary), uranium_proxy, copper, natural_gas, ten_year_yield (financing cost).
""",

    # Market overview
    ("market overview", "overview page", "indices", "sector performance"): """
**Market Overview** — Bloomberg-style daily snapshot.

**What's on the page:**

1. **Major Indices** (SPY, QQQ, DIA, IWM, VIX) — Current price, 1-day change, and a 30-day sparkline showing the trend

2. **Sector Performance** — 1-month return for all 11 SPDR sector ETFs in a horizontal bar chart (green = positive, red = negative)

3. **Rates & Fixed Income** — Table showing 10Y, 2Y, TLT, HYG, LQD with 1-day, 1-month, and 1-year returns. Plus a live yield curve spread card.

4. **Commodities & Currencies** — Gold, Silver, Oil (USO), Copper (COPX), Natural Gas (UNG), Dollar Index (DX-Y.NYB), Bitcoin

5. **1-Year Performance Chart** — Normalized return chart (SPY, QQQ, IWM, GLD) showing who's winning the year

6. **Signal Snapshot** — 5 key signals from live yfinance data: VIX level, yield curve spread, HYG credit trend, 10Y yield direction, risk appetite (SPY vs Gold)
""",
}


def find_quick_answer(query: str) -> str | None:
    """Match query against known Q&A patterns. Returns answer or None."""
    q = query.lower()
    for triggers, answer in QUICK_ANSWERS.items():
        if any(t in q for t in triggers):
            return answer.strip()
    return None


def try_claude_api(messages: list, system: str) -> str | None:
    """Try to call Claude API if anthropic library and key are available."""
    try:
        import anthropic
        api_key = st.session_state.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            return None
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=system,
            messages=messages,
        )
        return response.content[0].text
    except Exception:
        return None


def get_fallback_response(query: str) -> str:
    """Generate a helpful fallback response for unrecognized queries."""
    q = query.lower()

    if any(w in q for w in ["hello", "hi", "hey", "greetings"]):
        return "Hello! I'm the Unstructured Alpha research assistant. Ask me about any signal, ticker, page, or methodology — I'm here to help you get the most out of the platform."

    if any(w in q for w in ["thanks", "thank you", "great", "perfect", "awesome"]):
        return "You're welcome! Let me know if you have any other questions about the platform."

    if any(w in q for w in ["buy", "sell", "trade", "invest", "position", "recommend"]):
        return (
            "I can't give personalized investment advice — this platform is a research tool, not a trading advisor. "
            "What I can do is explain what the signals are saying and how to interpret confluence scores. "
            "Always do your own due diligence before any investment decision."
        )

    # Generic fallback
    return (
        "I don't have a specific answer for that yet, but I know the Unstructured Alpha platform well. "
        "Try asking about:\n"
        "- A specific signal (VIX, ATA Trucking, Yield Curve, HY Spread...)\n"
        "- A page (Signal Dashboard, Ticker Deep Dive, Stock Screener...)\n"
        "- A ticker theme (Nuclear, AI Infrastructure, Energy...)\n"
        "- The scoring methodology (Confluence Score, PCS weights, correlation...)\n"
        "- How to get started or use a specific feature\n\n"
        "Or add a Claude API key in Setup for more open-ended answers."
    )


# ─────────────────────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("## AI Research Assistant")
st.caption(
    "Ask anything about signals, tickers, methodology, or how to use the platform. "
    "Add a Claude API key in Setup for unrestricted AI-powered answers."
)

# Claude API key setup (separate from FRED key)
with st.sidebar:
    st.divider()
    st.markdown("### AI Assistant Setup")
    with st.expander("Claude API Key (optional)"):
        st.markdown("Add a Claude API key for open-ended AI answers. Free tier available at console.anthropic.com.")
        claude_key = st.text_input(
            "Claude (Anthropic) API Key",
            type="password",
            value=st.session_state.get("ANTHROPIC_API_KEY", ""),
            key="claude_api_key_input",
        )
        if claude_key:
            st.session_state["ANTHROPIC_API_KEY"] = claude_key
            st.success("Claude API key saved")
        st.caption("[Get API key](https://console.anthropic.com)")

    has_claude = bool(st.session_state.get("ANTHROPIC_API_KEY", ""))
    if has_claude:
        st.success("Claude API connected")
    else:
        st.info("Using built-in knowledge base. Add Claude API key for unrestricted Q&A.")


# Quick topic buttons
st.markdown("**Quick topics:**")
topic_cols = st.columns(4)
quick_topics = [
    ("Getting started", "How do I get started with the platform?"),
    ("Confluence Score", "How is the confluence score calculated?"),
    ("Nuclear thesis", "Tell me about the nuclear/uranium thesis"),
    ("FRED API key", "How do I add a FRED API key for live data?"),
]
for i, (label, prompt) in enumerate(quick_topics):
    if topic_cols[i % 4].button(label, key=f"qt_{i}", use_container_width=True):
        if "messages" not in st.session_state:
            st.session_state.messages = []
        st.session_state.messages.append({"role": "user", "content": prompt})
        answer = find_quick_answer(prompt) or try_claude_api(
            [{"role": "user", "content": prompt}], APP_CONTEXT
        ) or get_fallback_response(prompt)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()

st.divider()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Greeting
    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            "Hello! I'm the Unstructured Alpha research assistant. "
            "I can explain any signal, walk you through pages, help you interpret confluence scores, "
            "or discuss the Power Supercycle thesis.\n\n"
            "**Try asking:**\n"
            "- *What does the yield curve signal mean?*\n"
            "- *How is the confluence score calculated?*\n"
            "- *Walk me through the Ticker Deep Dive page*\n"
            "- *Which signals matter most for nuclear tickers?*\n"
            "- *What does a VIX of 16 mean for my portfolio?*"
        )
    })

# Render chat history
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ask about signals, tickers, methodology, or how to use the platform…"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            # 1) Try rule-based quick answers first (instant)
            answer = find_quick_answer(prompt)

            # 2) If no quick answer, try Claude API
            if not answer:
                claude_messages = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages[:-1]  # exclude latest user msg
                ] + [{"role": "user", "content": prompt}]
                answer = try_claude_api(claude_messages, APP_CONTEXT)

            # 3) Fallback to rule-based generic
            if not answer:
                answer = get_fallback_response(prompt)

        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})

# Clear chat button
if st.session_state.messages and len(st.session_state.messages) > 1:
    if st.button("Clear conversation", key="clear_chat"):
        st.session_state.messages = []
        st.rerun()

# ── Suggested questions ────────────────────────────────────────────────────────
with st.expander("More suggested questions"):
    suggestions = [
        "What signals are most important for energy tickers like XOM and CVX?",
        "Explain the HY credit spread and why it matters",
        "What is the ATA Trucking index and why is it a leading indicator?",
        "How do I find the most bullish tickers in the screener right now?",
        "What's the difference between PCS and correlation weight?",
        "Walk me through using the Stock Screener to find AI infrastructure plays",
        "Why might two uranium tickers have different confluence scores?",
        "What does it mean when the yield curve is inverted?",
        "How do federal contract awards relate to stock performance?",
        "What is the Power Supercycle thesis?",
    ]
    for s in suggestions:
        if st.button(s, key=f"sug_{s[:20]}", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": s})
            answer = find_quick_answer(s) or try_claude_api(
                [{"role": "user", "content": s}], APP_CONTEXT
            ) or get_fallback_response(s)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()
