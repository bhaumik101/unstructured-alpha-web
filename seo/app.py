"""
Unstructured Alpha — SEO Service
=================================
FastAPI service serving server-side-rendered ticker analysis pages.
Reads from the same PostgreSQL DB as the main Streamlit app.
Deploy as a separate Render web service at stocks.unstructuredalpha.com.

Routes:
    GET /                       → landing page: top movers + all tracked tickers
    GET /ticker/{symbol}        → individual ticker analysis page
    GET /signals/report         → weekly top movers report
    GET /sitemap.xml            → auto-generated sitemap for Google Search Console
    GET /robots.txt             → search engine directives
    GET /health                 → liveness probe for Render
"""

import os
import time
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

import sqlalchemy as sa
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(title="Unstructured Alpha SEO", docs_url=None, redoc_url=None)
templates = Jinja2Templates(directory="templates")

SEO_BASE_URL = os.environ.get("SEO_BASE_URL", "https://stocks.unstructuredalpha.com")
APP_BASE_URL = "https://unstructuredalpha.com"

# ── DB setup ──────────────────────────────────────────────────────────────────
_DATABASE_URL = os.environ.get("DATABASE_URL", "")
if _DATABASE_URL.startswith("postgres://"):
    _DATABASE_URL = _DATABASE_URL.replace("postgres://", "postgresql://", 1)

_engine: Optional[sa.Engine] = None
if _DATABASE_URL:
    _engine = sa.create_engine(
        _DATABASE_URL,
        pool_size=2,
        max_overflow=3,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={"connect_timeout": 10},
    )

# ── Simple TTL cache (no external deps) ───────────────────────────────────────
_CACHE: dict = {}
_CACHE_EXP: dict = {}


def _cache_get(key: str):
    if key in _CACHE and _CACHE_EXP.get(key, 0) > time.time():
        return _CACHE[key]
    return None


def _cache_set(key: str, value, ttl: int = 3600):
    _CACHE[key] = value
    _CACHE_EXP[key] = time.time() + ttl


# ── Ticker registry (extracted from dashboard/utils/config.py) ────────────────
# symbol → {name, sector, theme}
TICKERS: dict[str, dict] = {
    # ETFs
    "SPY":  {"name": "SPDR S&P 500 ETF Trust",               "sector": "ETF",               "theme": "macro"},
    "QQQ":  {"name": "Invesco QQQ Trust (Nasdaq-100)",        "sector": "ETF",               "theme": "macro"},
    "IWM":  {"name": "iShares Russell 2000 ETF",              "sector": "ETF",               "theme": "macro"},
    "XLI":  {"name": "Industrial Select Sector SPDR",         "sector": "ETF",               "theme": "macro"},
    "XLE":  {"name": "Energy Select Sector SPDR",             "sector": "ETF",               "theme": "macro"},
    "XLY":  {"name": "Consumer Discretionary SPDR",           "sector": "ETF",               "theme": "macro"},
    "XLP":  {"name": "Consumer Staples SPDR",                 "sector": "ETF",               "theme": "macro"},
    "XLF":  {"name": "Financial Select Sector SPDR",          "sector": "ETF",               "theme": "macro"},
    "XLU":  {"name": "Utilities Select Sector SPDR",          "sector": "ETF",               "theme": "nuclear"},
    "HYG":  {"name": "iShares iBoxx High Yield ETF",          "sector": "ETF",               "theme": "macro"},
    "TLT":  {"name": "iShares 20+ Year Treasury ETF",         "sector": "ETF",               "theme": "macro"},
    "GLD":  {"name": "SPDR Gold Shares ETF",                  "sector": "ETF",               "theme": "macro"},
    "URA":  {"name": "Global X Uranium ETF",                  "sector": "ETF",               "theme": "nuclear"},
    "NLR":  {"name": "VanEck Uranium+Nuclear Energy ETF",     "sector": "ETF",               "theme": "nuclear"},
    "LIT":  {"name": "Global X Lithium & Battery Tech ETF",   "sector": "ETF",               "theme": "critical_minerals"},
    "ITA":  {"name": "iShares U.S. Aerospace & Defense ETF",  "sector": "ETF",               "theme": "defense"},
    "XBI":  {"name": "SPDR S&P Biotech ETF",                  "sector": "ETF",               "theme": "healthcare"},
    "CIBR": {"name": "First Trust NASDAQ Cybersecurity ETF",  "sector": "ETF",               "theme": "cybersecurity"},
    "BOTZ": {"name": "Global X Robotics & AI ETF",            "sector": "ETF",               "theme": "robotics"},
    "PHO":  {"name": "Invesco Water Resources ETF",           "sector": "ETF",               "theme": "water"},
    "COPX": {"name": "Global X Copper Miners ETF",            "sector": "ETF",               "theme": "ai_infrastructure"},
    "REMX": {"name": "VanEck Rare Earth/Strategic Metals ETF","sector": "ETF",               "theme": "critical_minerals"},
    "KRE":  {"name": "SPDR S&P Regional Banking ETF",         "sector": "ETF",               "theme": "financials"},
    "TBF":  {"name": "ProShares Short 20+ Year Treasury",     "sector": "ETF",               "theme": "macro"},
    "SHY":  {"name": "iShares 1-3 Year Treasury Bond ETF",    "sector": "ETF",               "theme": "macro"},
    "TMF":  {"name": "Direxion Daily 20+ Yr Treasury Bull 3X","sector": "ETF",               "theme": "macro"},
    "VNQ":  {"name": "Vanguard Real Estate ETF",              "sector": "ETF",               "theme": "macro"},
    # Railroads
    "UNP":  {"name": "Union Pacific Corporation",             "sector": "Transportation",    "theme": "macro"},
    "CSX":  {"name": "CSX Corporation",                       "sector": "Transportation",    "theme": "macro"},
    "NSC":  {"name": "Norfolk Southern Corporation",          "sector": "Transportation",    "theme": "macro"},
    "CP":   {"name": "Canadian Pacific Kansas City",          "sector": "Transportation",    "theme": "macro"},
    "CNI":  {"name": "Canadian National Railway",             "sector": "Transportation",    "theme": "macro"},
    # Trucking
    "ODFL": {"name": "Old Dominion Freight Line",             "sector": "Transportation",    "theme": "macro"},
    "JBHT": {"name": "J.B. Hunt Transport Services",          "sector": "Transportation",    "theme": "macro"},
    "SAIA": {"name": "Saia Inc.",                             "sector": "Transportation",    "theme": "macro"},
    "WERN": {"name": "Werner Enterprises",                    "sector": "Transportation",    "theme": "macro"},
    "UPS":  {"name": "United Parcel Service",                 "sector": "Transportation",    "theme": "macro"},
    "FDX":  {"name": "FedEx Corporation",                     "sector": "Transportation",    "theme": "macro"},
    # Industrial
    "CAT":  {"name": "Caterpillar Inc.",                      "sector": "Industrial",        "theme": "industrials"},
    "DE":   {"name": "Deere & Company",                       "sector": "Industrial",        "theme": "industrials"},
    "HON":  {"name": "Honeywell International",               "sector": "Industrial",        "theme": "industrials"},
    "ETN":  {"name": "Eaton Corporation",                     "sector": "Power Management",  "theme": "ai_infrastructure"},
    "EMR":  {"name": "Emerson Electric",                      "sector": "Industrial",        "theme": "macro"},
    "ROK":  {"name": "Rockwell Automation",                   "sector": "Industrial",        "theme": "macro"},
    "ITW":  {"name": "Illinois Tool Works",                   "sector": "Industrial",        "theme": "macro"},
    "GE":   {"name": "GE Aerospace",                          "sector": "Industrial",        "theme": "macro"},
    "MMM":  {"name": "3M Company",                            "sector": "Industrial",        "theme": "industrials"},
    # Homebuilders
    "DHI":  {"name": "D.R. Horton Inc.",                      "sector": "Homebuilders",      "theme": "macro"},
    "LEN":  {"name": "Lennar Corporation",                    "sector": "Homebuilders",      "theme": "macro"},
    "PHM":  {"name": "PulteGroup Inc.",                       "sector": "Homebuilders",      "theme": "macro"},
    "TOL":  {"name": "Toll Brothers Inc.",                    "sector": "Homebuilders",      "theme": "macro"},
    "NVR":  {"name": "NVR Inc.",                              "sector": "Homebuilders",      "theme": "macro"},
    "MAS":  {"name": "Masco Corporation",                     "sector": "Building Products", "theme": "macro"},
    # Consumer
    "COST": {"name": "Costco Wholesale Corporation",          "sector": "Consumer Staples",  "theme": "consumer"},
    "TGT":  {"name": "Target Corporation",                    "sector": "Consumer Disc.",    "theme": "consumer"},
    "WMT":  {"name": "Walmart Inc.",                          "sector": "Consumer Staples",  "theme": "consumer"},
    "HD":   {"name": "Home Depot Inc.",                       "sector": "Consumer Disc.",    "theme": "consumer"},
    "LOW":  {"name": "Lowe's Companies Inc.",                 "sector": "Consumer Disc.",    "theme": "consumer"},
    "AMZN": {"name": "Amazon.com Inc.",                       "sector": "Technology",        "theme": "ai_infrastructure"},
    "KR":   {"name": "Kroger Company",                        "sector": "Consumer Staples",  "theme": "macro"},
    # Financial
    "JPM":  {"name": "JPMorgan Chase & Co.",                  "sector": "Banking",           "theme": "financials"},
    "BAC":  {"name": "Bank of America Corporation",           "sector": "Banking",           "theme": "financials"},
    "GS":   {"name": "Goldman Sachs Group",                   "sector": "Banking",           "theme": "financials"},
    # Energy
    "XOM":  {"name": "Exxon Mobil Corporation",               "sector": "Energy",            "theme": "energy"},
    "CVX":  {"name": "Chevron Corporation",                   "sector": "Energy",            "theme": "energy"},
    "OXY":  {"name": "Occidental Petroleum",                  "sector": "Energy",            "theme": "energy"},
    "COP":  {"name": "ConocoPhillips",                        "sector": "Energy",            "theme": "energy"},
    "HAL":  {"name": "Halliburton Company",                   "sector": "Oil Services",      "theme": "energy"},
    "SLB":  {"name": "Schlumberger (SLB)",                    "sector": "Oil Services",      "theme": "energy"},
    "BKR":  {"name": "Baker Hughes Company",                  "sector": "Oil Services",      "theme": "energy"},
    "EQT":  {"name": "EQT Corporation",                       "sector": "Natural Gas E&P",   "theme": "energy"},
    "AR":   {"name": "Antero Resources Corp.",                "sector": "Natural Gas E&P",   "theme": "energy"},
    "LNG":  {"name": "Cheniere Energy Inc.",                  "sector": "LNG Export",        "theme": "energy"},
    # Nuclear
    "CCJ":  {"name": "Cameco Corporation",                    "sector": "Uranium Mining",    "theme": "nuclear"},
    "LEU":  {"name": "Centrus Energy Corp.",                  "sector": "Nuclear Enrichment","theme": "nuclear"},
    "UEC":  {"name": "Uranium Energy Corp.",                  "sector": "Uranium Mining",    "theme": "nuclear"},
    "UUUU": {"name": "Energy Fuels Inc.",                     "sector": "Uranium Mining",    "theme": "nuclear"},
    "CEG":  {"name": "Constellation Energy Corporation",      "sector": "Utilities/Nuclear", "theme": "nuclear"},
    "VST":  {"name": "Vistra Corp.",                          "sector": "Utilities",         "theme": "nuclear"},
    "SMR":  {"name": "NuScale Power Corporation",             "sector": "Nuclear (SMR)",     "theme": "nuclear"},
    "OKLO": {"name": "Oklo Inc.",                             "sector": "Nuclear (SMR)",     "theme": "nuclear"},
    "BWXT": {"name": "BWX Technologies Inc.",                 "sector": "Nuclear Services",  "theme": "nuclear"},
    # Utilities
    "NEE":  {"name": "NextEra Energy Inc.",                   "sector": "Utilities",         "theme": "nuclear"},
    "D":    {"name": "Dominion Energy Inc.",                  "sector": "Utilities",         "theme": "nuclear"},
    "EXC":  {"name": "Exelon Corporation",                    "sector": "Utilities/Nuclear", "theme": "nuclear"},
    "DUK":  {"name": "Duke Energy Corporation",               "sector": "Utilities",         "theme": "nuclear"},
    "SO":   {"name": "Southern Company",                      "sector": "Utilities",         "theme": "nuclear"},
    # AI Infrastructure
    "FCX":  {"name": "Freeport-McMoRan Inc.",                 "sector": "Copper Mining",     "theme": "ai_infrastructure"},
    "SCCO": {"name": "Southern Copper Corporation",           "sector": "Copper Mining",     "theme": "ai_infrastructure"},
    "TECK": {"name": "Teck Resources Limited",                "sector": "Diversified Mining","theme": "ai_infrastructure"},
    "BHP":  {"name": "BHP Group Limited",                     "sector": "Diversified Mining","theme": "ai_infrastructure"},
    "WMB":  {"name": "Williams Companies Inc.",               "sector": "Energy/Pipelines",  "theme": "ai_infrastructure"},
    "KMI":  {"name": "Kinder Morgan Inc.",                    "sector": "Energy/Pipelines",  "theme": "ai_infrastructure"},
    "OKE":  {"name": "ONEOK Inc.",                            "sector": "Energy/Pipelines",  "theme": "ai_infrastructure"},
    "ET":   {"name": "Energy Transfer LP",                    "sector": "Energy/Pipelines",  "theme": "ai_infrastructure"},
    "PWR":  {"name": "Quanta Services Inc.",                  "sector": "Grid Construction", "theme": "ai_infrastructure"},
    "VRT":  {"name": "Vertiv Holdings Co.",                   "sector": "Data Center Infra", "theme": "ai_infrastructure"},
    "ACLS": {"name": "Axcelis Technologies Inc.",             "sector": "Semiconductors",    "theme": "ai_infrastructure"},
    "EQIX": {"name": "Equinix Inc.",                          "sector": "Data Centers REIT", "theme": "ai_infrastructure"},
    "DLR":  {"name": "Digital Realty Trust",                  "sector": "Data Centers REIT", "theme": "ai_infrastructure"},
    "NVDA": {"name": "NVIDIA Corporation",                    "sector": "Semiconductors",    "theme": "ai_infrastructure"},
    "AMD":  {"name": "Advanced Micro Devices",                "sector": "Semiconductors",    "theme": "ai_infrastructure"},
    "AVGO": {"name": "Broadcom Inc.",                         "sector": "Semiconductors",    "theme": "ai_infrastructure"},
    "SMCI": {"name": "Super Micro Computer Inc.",             "sector": "AI Servers",        "theme": "ai_infrastructure"},
    "DELL": {"name": "Dell Technologies Inc.",                "sector": "AI Servers",        "theme": "ai_infrastructure"},
    "HPE":  {"name": "Hewlett Packard Enterprise",            "sector": "AI Servers",        "theme": "ai_infrastructure"},
    "MSFT": {"name": "Microsoft Corporation",                 "sector": "Technology",        "theme": "ai_infrastructure"},
    "AAPL": {"name": "Apple Inc.",                            "sector": "Technology",        "theme": "macro"},
    # Quantum
    "IONQ": {"name": "IonQ Inc.",                             "sector": "Quantum Computing", "theme": "quantum"},
    "RGTI": {"name": "Rigetti Computing Inc.",                "sector": "Quantum Computing", "theme": "quantum"},
    "QBTS": {"name": "D-Wave Quantum Inc.",                   "sector": "Quantum Computing", "theme": "quantum"},
    "IBM":  {"name": "International Business Machines",       "sector": "Technology",        "theme": "quantum"},
    "GOOGL":{"name": "Alphabet Inc.",                         "sector": "Technology",        "theme": "quantum"},
    # Agriculture
    "ADM":  {"name": "Archer-Daniels-Midland Company",        "sector": "Agriculture",       "theme": "macro"},
    "BG":   {"name": "Bunge Global SA",                       "sector": "Agriculture",       "theme": "macro"},
    "MOS":  {"name": "Mosaic Company",                        "sector": "Fertilizers",       "theme": "macro"},
    "NTR":  {"name": "Nutrien Ltd.",                          "sector": "Fertilizers",       "theme": "macro"},
    # Critical Minerals
    "ALB":  {"name": "Albemarle Corporation",                 "sector": "Lithium Mining",    "theme": "critical_minerals"},
    "SQM":  {"name": "Sociedad Quimica y Minera",             "sector": "Lithium Mining",    "theme": "critical_minerals"},
    "LAC":  {"name": "Lithium Americas Corp.",                "sector": "Lithium Mining",    "theme": "critical_minerals"},
    "PLL":  {"name": "Piedmont Lithium Inc.",                 "sector": "Lithium Mining",    "theme": "critical_minerals"},
    "MP":   {"name": "MP Materials Corp.",                    "sector": "Rare Earth Mining", "theme": "critical_minerals"},
    "USAR": {"name": "USA Rare Earth Inc.",                   "sector": "Rare Earth Mining", "theme": "critical_minerals"},
    "TMC":  {"name": "TMC the metals company Inc.",           "sector": "Deep-Sea Minerals", "theme": "critical_minerals"},
    # Defense
    "LMT":  {"name": "Lockheed Martin Corporation",           "sector": "Defense",           "theme": "defense"},
    "RTX":  {"name": "RTX Corporation",                       "sector": "Defense",           "theme": "defense"},
    "NOC":  {"name": "Northrop Grumman Corporation",          "sector": "Defense",           "theme": "defense"},
    "GD":   {"name": "General Dynamics Corporation",          "sector": "Defense",           "theme": "defense"},
    "LHX":  {"name": "L3Harris Technologies Inc.",            "sector": "Defense",           "theme": "defense"},
    # Healthcare
    "LLY":  {"name": "Eli Lilly and Company",                 "sector": "Pharmaceuticals",   "theme": "healthcare"},
    "NVO":  {"name": "Novo Nordisk A/S",                      "sector": "Pharmaceuticals",   "theme": "healthcare"},
    "REGN": {"name": "Regeneron Pharmaceuticals Inc.",        "sector": "Biotechnology",     "theme": "healthcare"},
    "VRTX": {"name": "Vertex Pharmaceuticals Inc.",           "sector": "Biotechnology",     "theme": "healthcare"},
    # Cybersecurity
    "CRWD": {"name": "CrowdStrike Holdings Inc.",             "sector": "Cybersecurity",     "theme": "cybersecurity"},
    "PANW": {"name": "Palo Alto Networks Inc.",               "sector": "Cybersecurity",     "theme": "cybersecurity"},
    "FTNT": {"name": "Fortinet Inc.",                         "sector": "Cybersecurity",     "theme": "cybersecurity"},
    "ZS":   {"name": "Zscaler Inc.",                          "sector": "Cybersecurity",     "theme": "cybersecurity"},
    # Robotics
    "ISRG": {"name": "Intuitive Surgical Inc.",               "sector": "Medical Robotics",  "theme": "robotics"},
    "ABB":  {"name": "ABB Ltd.",                              "sector": "Industrial Automation","theme": "robotics"},
    "TER":  {"name": "Teradyne Inc.",                         "sector": "Automation Equip.", "theme": "robotics"},
    # Water
    "AWK":  {"name": "American Water Works Company",          "sector": "Water Utilities",   "theme": "water"},
    "WTRG": {"name": "Essential Utilities Inc.",              "sector": "Water Utilities",   "theme": "water"},
    "XYL":  {"name": "Xylem Inc.",                            "sector": "Water Technology",  "theme": "water"},
    "ECL":  {"name": "Ecolab Inc.",                           "sector": "Water Technology",  "theme": "water"},
}

THEME_LABELS = {
    "macro": "Macro",
    "ai_infrastructure": "AI Infrastructure",
    "nuclear": "Nuclear & Power",
    "energy": "Energy",
    "industrials": "Industrials",
    "consumer": "Consumer",
    "financials": "Financials",
    "critical_minerals": "Critical Minerals",
    "defense": "Defense",
    "healthcare": "Healthcare",
    "cybersecurity": "Cybersecurity",
    "robotics": "Robotics & AI",
    "water": "Water",
    "quantum": "Quantum",
}


# ── DB query helpers ───────────────────────────────────────────────────────────

def _get_latest_score(ticker: str) -> Optional[dict]:
    """Return the most recent score snapshot for a ticker."""
    cache_key = f"latest:{ticker}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    if not _engine:
        return None
    with _engine.connect() as conn:
        row = conn.execute(sa.text(
            "SELECT ticker, snapshot_date, score, \"case\", conviction "
            "FROM score_snapshots WHERE ticker = :ticker "
            "ORDER BY snapshot_date DESC LIMIT 1"
        ), {"ticker": ticker.upper()}).fetchone()
    result = dict(row._mapping) if row else None
    _cache_set(cache_key, result, ttl=1800)
    return result


def _get_score_history(ticker: str, days: int = 90) -> list[dict]:
    """Return up to `days` of score history for a ticker, oldest first."""
    cache_key = f"history:{ticker}:{days}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    if not _engine:
        return []
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    with _engine.connect() as conn:
        rows = conn.execute(sa.text(
            "SELECT snapshot_date, score, \"case\" FROM score_snapshots "
            "WHERE ticker = :ticker AND snapshot_date >= :cutoff "
            "ORDER BY snapshot_date ASC"
        ), {"ticker": ticker.upper(), "cutoff": cutoff}).fetchall()
    result = [dict(r._mapping) for r in rows]
    _cache_set(cache_key, result, ttl=1800)
    return result


def _get_all_latest_scores() -> list[dict]:
    """Return the latest score for every tracked ticker in score_snapshots."""
    cache_key = "all_latest"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    if not _engine:
        return []
    with _engine.connect() as conn:
        rows = conn.execute(sa.text(
            "SELECT DISTINCT ON (ticker) ticker, snapshot_date, score, \"case\", conviction "
            "FROM score_snapshots ORDER BY ticker, snapshot_date DESC"
        )).fetchall()
    result = [dict(r._mapping) for r in rows]
    _cache_set(cache_key, result, ttl=1800)
    return result


def _get_weekly_movers() -> dict:
    """Return biggest score changes in the last 7 days."""
    cache_key = "weekly_movers"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    if not _engine:
        return {"risers": [], "fallers": []}
    cutoff_7d = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    cutoff_14d = (datetime.now(timezone.utc) - timedelta(days=14)).strftime("%Y-%m-%d")
    with _engine.connect() as conn:
        # Latest score per ticker in last 7 days
        now_rows = conn.execute(sa.text(
            "SELECT DISTINCT ON (ticker) ticker, snapshot_date, score, \"case\" "
            "FROM score_snapshots WHERE snapshot_date >= :cutoff "
            "ORDER BY ticker, snapshot_date DESC"
        ), {"cutoff": cutoff_7d}).fetchall()
        # Score from ~7-14 days ago per ticker
        then_rows = conn.execute(sa.text(
            "SELECT DISTINCT ON (ticker) ticker, score "
            "FROM score_snapshots WHERE snapshot_date >= :c14 AND snapshot_date < :c7 "
            "ORDER BY ticker, snapshot_date DESC"
        ), {"c14": cutoff_14d, "c7": cutoff_7d}).fetchall()

    then_map = {r.ticker: r.score for r in then_rows}
    changes = []
    for r in now_rows:
        t = r.ticker
        if t in then_map:
            delta = round(r.score - then_map[t], 1)
            changes.append({
                "ticker": t,
                "name": TICKERS.get(t, {}).get("name", t),
                "sector": TICKERS.get(t, {}).get("sector", ""),
                "score": round(r.score, 1),
                "case": r.case,
                "delta": delta,
                "snapshot_date": r.snapshot_date,
            })

    changes.sort(key=lambda x: x["delta"], reverse=True)
    result = {
        "risers": changes[:10],
        "fallers": list(reversed(changes))[:10],
        "as_of": datetime.now(timezone.utc).strftime("%B %d, %Y"),
    }
    _cache_set(cache_key, result, ttl=3600)
    return result


# ── Score display helpers ──────────────────────────────────────────────────────

def case_color(case: Optional[str]) -> str:
    m = {"BULL": "#00D566", "BEAR": "#FF4444", "NEUTRAL": "#FFB800"}
    return m.get((case or "").upper(), "#8892AA")


def case_label(case: Optional[str]) -> str:
    m = {"BULL": "Bullish", "BEAR": "Bearish", "NEUTRAL": "Neutral"}
    return m.get((case or "").upper(), "Unknown")


# Register helpers in Jinja2 environment
templates.env.globals["case_color"] = case_color
templates.env.globals["case_label"] = case_label
templates.env.globals["APP_BASE_URL"] = APP_BASE_URL
templates.env.globals["SEO_BASE_URL"] = SEO_BASE_URL
templates.env.globals["json"] = json
templates.env.globals["now_year"] = datetime.now(timezone.utc).year


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots():
    return (
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {SEO_BASE_URL}/sitemap.xml\n"
    )


@app.get("/sitemap.xml", response_class=PlainTextResponse)
def sitemap():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls = [
        f"  <url><loc>{SEO_BASE_URL}/</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>",
        f"  <url><loc>{SEO_BASE_URL}/signals/report</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>",
    ]
    for sym in sorted(TICKERS.keys()):
        urls.append(
            f"  <url><loc>{SEO_BASE_URL}/ticker/{sym}</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq><priority>0.7</priority></url>"
        )
    body = "\n".join(urls)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n"
        "</urlset>"
    )


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    all_scores = _get_all_latest_scores()
    # Enrich with ticker metadata
    enriched = []
    for row in all_scores:
        t = row["ticker"]
        meta = TICKERS.get(t, {})
        enriched.append({
            **row,
            "score": round(row["score"], 1),
            "name": meta.get("name", t),
            "sector": meta.get("sector", ""),
            "theme": meta.get("theme", "macro"),
            "theme_label": THEME_LABELS.get(meta.get("theme", "macro"), ""),
        })
    enriched.sort(key=lambda x: x["score"], reverse=True)
    # Only show tickers present in score_snapshots
    tracked_symbols = {r["ticker"] for r in all_scores}
    all_ticker_list = [
        {"symbol": sym, **meta, "theme_label": THEME_LABELS.get(meta.get("theme", ""), "")}
        for sym, meta in sorted(TICKERS.items())
        if sym not in tracked_symbols
    ]
    return templates.TemplateResponse("index.html", {
        "request": request,
        "top_tickers": enriched[:20],
        "bull_count": sum(1 for r in enriched if (r.get("case") or "").upper() == "BULL"),
        "bear_count": sum(1 for r in enriched if (r.get("case") or "").upper() == "BEAR"),
        "neut_count": sum(1 for r in enriched if (r.get("case") or "").upper() == "NEUTRAL"),
        "all_tickers": all_ticker_list,
        "as_of": datetime.now(timezone.utc).strftime("%B %d, %Y"),
    })


@app.get("/ticker/{symbol}", response_class=HTMLResponse)
def ticker_page(request: Request, symbol: str):
    symbol = symbol.upper().strip()
    meta = TICKERS.get(symbol)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Ticker {symbol} not tracked.")

    latest = _get_latest_score(symbol)
    history = _get_score_history(symbol, days=90)

    # Prepare chart data
    chart_labels = [r["snapshot_date"] for r in history]
    chart_scores = [round(r["score"], 1) for r in history]
    chart_cases = [r.get("case", "NEUTRAL") for r in history]

    # Score delta vs 30 days ago
    delta = None
    delta_label = ""
    if len(history) >= 2:
        delta = round(chart_scores[-1] - chart_scores[0], 1)
        delta_label = f"+{delta}" if delta > 0 else str(delta)

    theme_label = THEME_LABELS.get(meta.get("theme", ""), "")
    score = round(latest["score"], 1) if latest else None
    case = (latest.get("case") or "NEUTRAL").upper() if latest else "NEUTRAL"
    conviction = (latest.get("conviction") or "").replace("_", " ").title() if latest else ""

    # Similar tickers (same theme, excluding current)
    similar = [
        {"symbol": sym, "name": m["name"], "sector": m["sector"]}
        for sym, m in TICKERS.items()
        if m.get("theme") == meta.get("theme") and sym != symbol
    ][:6]

    return templates.TemplateResponse("ticker.html", {
        "request": request,
        "symbol": symbol,
        "name": meta["name"],
        "sector": meta["sector"],
        "theme": meta.get("theme", ""),
        "theme_label": theme_label,
        "score": score,
        "case": case,
        "conviction": conviction,
        "delta": delta,
        "delta_label": delta_label,
        "latest_date": latest["snapshot_date"] if latest else None,
        "history_count": len(history),
        "chart_labels": json.dumps(chart_labels),
        "chart_scores": json.dumps(chart_scores),
        "chart_cases": json.dumps(chart_cases),
        "similar": similar,
        "has_data": latest is not None,
    })


@app.get("/signals/report", response_class=HTMLResponse)
def weekly_report(request: Request):
    movers = _get_weekly_movers()
    all_scores = _get_all_latest_scores()
    bull = [r for r in all_scores if (r.get("case") or "").upper() == "BULL"]
    bear = [r for r in all_scores if (r.get("case") or "").upper() == "BEAR"]
    neut = [r for r in all_scores if (r.get("case") or "").upper() == "NEUTRAL"]

    return templates.TemplateResponse("report.html", {
        "request": request,
        "risers": movers.get("risers", []),
        "fallers": movers.get("fallers", []),
        "as_of": movers.get("as_of", ""),
        "total": len(all_scores),
        "bull_count": len(bull),
        "bear_count": len(bear),
        "neut_count": len(neut),
        "bull_pct": round(len(bull) / len(all_scores) * 100) if all_scores else 0,
        "bear_pct": round(len(bear) / len(all_scores) * 100) if all_scores else 0,
    })
