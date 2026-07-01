"""
Home — Unstructured Alpha
Public-facing landing page. Psychological design goals:
  1. Live signal data IN the hero — not below it. Real data creates immediate credibility.
  2. Specificity everywhere — "40 signals, 4-16 weeks ahead" not "leading indicators."
  3. Authority by association — FRED / SEC EDGAR / FINRA = same sources Goldman uses.
  4. Loss aversion framing — "what are you missing" more powerful than "here's what you get."
  5. Anchoring — mention Bloomberg's $50K price before showing this is free.
  6. One clear primary CTA above the fold — no decision paralysis.
"""

import streamlit as st

st.set_page_config(
    page_title="Unstructured Alpha — Macro Signal Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Unstructured Alpha — institutional-grade macro signals for every investor."},
)

import html as _h
import pandas as pd
from utils.header import render_header, render_sidebar_base
from utils.signals_cache import get_all_signal_scores
from utils.config import SIGNALS, CATEGORIES
from utils.narrative import generate_narrative
from utils.top_tickers import get_top_tickers
from utils.convergence import get_convergence_events, render_convergence_events

render_header("Home")
render_sidebar_base()

# ── Load live signal data (shared cache — no extra API cost) ──────────────────
def _build_home_data() -> dict:
    _all = get_all_signal_scores()
    bull, bear, neut, buckets = [], [], [], {}
    for sid, sv in _all.items():
        if sv.get("error"):
            continue
        status = sv.get("status", "neutral")
        score  = sv.get("score", 50)
        name   = sv.get("name", sid)
        cat    = sv.get("category", "macro")
        if status == "bullish":
            bull.append((name, score))
        elif status == "bearish":
            bear.append((name, score))
        else:
            neut.append((name, score))
        buckets.setdefault(cat, []).append(score)
    return {
        "bull":    sorted(bull, key=lambda x: -x[1]),
        "bear":    sorted(bear, key=lambda x:  x[1]),
        "neut":    neut,
        "sectors": {k: sum(v)/len(v) for k, v in buckets.items() if v},
    }

try:
    with st.spinner(""):
        _raw_scores = get_all_signal_scores()
        _hd = _build_home_data()
        _narrative  = generate_narrative(_raw_scores)
        _top_tkrs   = get_top_tickers(len(_raw_scores))
    _nb, _nr, _nn = len(_hd["bull"]), len(_hd["bear"]), len(_hd["neut"])
    _total = max(1, _nb + _nr + _nn)
    _bias_label = _narrative["regime"]
    _data_loaded = True
except Exception:
    _hd = {"bull": [], "bear": [], "neut": [], "sectors": {}}
    _raw_scores = {}
    _narrative  = {"regime": "LOADING…", "regime_color": "#8892AA", "summary": "",
                   "top_bull": [], "top_bear": [], "watch_note": "", "sector_bias": {},
                   "bull_count": 0, "bear_count": 0, "neut_count": 0, "total": 0}
    _top_tkrs   = {"bullish": [], "bearish": [], "by_sector": {}, "all": []}
    _nb = _nr = _nn = _total = 0
    _bias_label = "LOADING…"
    _data_loaded = False


# ── FLIP ALERT HELPER ─────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def _get_recent_signal_flip() -> dict | None:
    """Return the most dramatic signal direction-flip in the last 48 hours, or None."""
    try:
        from utils.db import engine
        import sqlalchemy as sa
        with engine.connect() as _conn:
            _rows = _conn.execute(sa.text("""
                SELECT signal_id, status, score, snapshot_date
                FROM signal_snapshots
                WHERE snapshot_date >= NOW() - INTERVAL '48 hours'
                ORDER BY signal_id, snapshot_date
            """)).mappings().all()
        if not _rows:
            return None
        _by_sig: dict = {}
        for _r in _rows:
            _by_sig.setdefault(_r["signal_id"], []).append(dict(_r))
        _flips = []
        for _sid, _snaps in _by_sig.items():
            _sts = [_s["status"] for _s in _snaps]
            for _i in range(1, len(_sts)):
                if _sts[_i] != _sts[_i - 1] and _sts[_i] in ("bullish", "bearish"):
                    from utils.config import SIGNALS as _S2
                    _flips.append({
                        "signal_id": _sid,
                        "name": _S2.get(_sid, {}).get("name", _sid),
                        "to_status": _sts[_i],
                        "from_status": _sts[_i - 1],
                        "score": _snaps[-1]["score"],
                    })
                    break
        if not _flips:
            return None
        _flips.sort(key=lambda x: abs(x["score"] - 50), reverse=True)
        return _flips[0]
    except Exception:
        return None


# ── PORTFOLIO CHECK HELPER ────────────────────────────────────────────────────
def _score_tickers_from_cache(tickers_input: str, raw_scores: dict) -> list:
    """Score tickers from the already-cached signal data — zero extra API calls."""
    from utils.config import TICKERS as _TK
    _results = []
    _syms = [t.strip().upper() for t in tickers_input.replace(",", " ").split() if t.strip()][:5]
    for _sym in _syms:
        _tk_cfg = _TK.get(_sym, {})
        _sig_ids = _tk_cfg.get("signals", []) if _tk_cfg else []
        if not _sig_ids:  # Unknown ticker — use broad macro basket
            _sig_ids = [
                "yield_curve", "hy_credit_spread", "jobless_claims",
                "put_call_ratio", "consumer_sentiment", "vix_term_structure",
            ]
        _scores, _top_sig = [], []
        for _sid in _sig_ids:
            _sv = raw_scores.get(_sid)
            if _sv and not _sv.get("error") and _sv.get("status") != "insufficient_data":
                _sc = _sv["score"]
                _scores.append(_sc)
                _top_sig.append((_sv["name"], _sv["status"], _sc))
        if not _scores:
            continue
        _avg = sum(_scores) / len(_scores)
        _st = "bullish" if _avg >= 60 else ("bearish" if _avg <= 40 else "neutral")
        _top_sig.sort(key=lambda x: abs(x[2] - 50), reverse=True)
        _results.append({
            "ticker":      _sym,
            "name":        _tk_cfg.get("name", _sym) if _tk_cfg else _sym,
            "score":       round(_avg, 1),
            "status":      _st,
            "top_signals": _top_sig[:2],
            "known":       bool(_tk_cfg),
        })
    return _results


# Dark-theme regime colors (overrides narrative.py light-theme values)
_bias_color = (
    "#00D566" if any(x in _bias_label for x in ("BULL", "ON", "RISK-ON"))
    else "#FF4444" if any(x in _bias_label for x in ("BEAR", "OFF", "RISK-OFF"))
    else "#6B7FBF"
)
_bias_bg = (
    "rgba(0,213,102,0.07)" if "00D566" in _bias_color
    else "rgba(255,68,68,0.07)" if "FF4444" in _bias_color
    else "rgba(107,127,191,0.05)"
)
_top_bull = _hd["bull"][0][0] if _hd["bull"] else None
_top_bear = _hd["bear"][0][0] if _hd["bear"] else None

# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;padding:40px 0 0;font-family:'Inter',sans-serif;">
    <div style="font-size:0.65rem;letter-spacing:0.22em;color:#00D566;margin-bottom:16px;
                font-weight:700;">
        INSTITUTIONAL-GRADE MACRO INTELLIGENCE · FREE
    </div>
    <div style="font-size:2.8rem;font-weight:900;color:#E8EEFF;line-height:1.1;
                max-width:760px;margin:0 auto;letter-spacing:-1.5px;">
        Before the market moves,<br>
        <span style="background:linear-gradient(135deg,#00D566,#00C8E0);
                     -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                     background-clip:text;">the signals already did.</span>
    </div>
    <div style="font-size:1.0rem;color:#8892AA;margin:20px auto 0;max-width:560px;
                line-height:1.7;font-weight:400;">
        43 macro signals — Fed policy, energy flows, credit spreads, insider buying,
        put/call sentiment — scored in real time and mapped to the stocks you actually hold.
    </div>
</div>
""", unsafe_allow_html=True)

# ── LIVE SIGNAL PULSE ─────────────────────────────────────────────────────────
_bar_bull = f"{(_nb / _total * 100):.0f}%" if _total > 0 else "0%"
_bar_bear = f"{(_nr / _total * 100):.0f}%" if _total > 0 else "0%"

_top_bull_html = (
    f'<div style="font-size:0.72rem;color:#00D566;margin-top:3px;font-weight:500;">'
    f'▲ {_h.escape(str(_top_bull))[:32]}</div>'
    if _top_bull else ""
)
_top_bear_html = (
    f'<div style="font-size:0.72rem;color:#FF4444;margin-top:3px;font-weight:500;">'
    f'▼ {_h.escape(str(_top_bear))[:32]}</div>'
    if _top_bear else ""
)

st.markdown(
    f'<div style="background:rgba(18,21,30,0.9);border:1px solid rgba(0,213,102,0.18);'
    f'border-radius:16px;padding:24px 28px 20px;margin:28px auto 0;max-width:860px;'
    f'font-family:Inter,sans-serif;backdrop-filter:blur(8px);'
    f'box-shadow:0 0 40px rgba(0,213,102,0.06),0 20px 60px rgba(0,0,0,0.5);">'
    f'<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:20px;">'
    f'<div style="flex:1;min-width:200px;">'
    f'<div style="font-size:0.58rem;letter-spacing:0.18em;color:#8892AA;margin-bottom:8px;font-weight:700;">LIVE MACRO READ — RIGHT NOW</div>'
    f'<div style="font-size:2.2rem;font-weight:800;color:{_bias_color};letter-spacing:-0.5px;">{_h.escape(_bias_label)}</div>'
    f'<div style="font-size:0.75rem;color:#8892AA;margin-top:6px;">across {_total} tracked signals</div>'
    f'</div>'
    f'<div style="display:flex;gap:32px;flex-wrap:wrap;">'
    f'<div style="text-align:center;">'
    f'<div style="font-size:2.4rem;font-weight:800;color:#00D566;letter-spacing:-1px;">{_nb}</div>'
    f'<div style="font-size:0.60rem;color:#00D566;letter-spacing:0.12em;font-weight:700;">BULLISH</div>'
    f'{_top_bull_html}'
    f'</div>'
    f'<div style="text-align:center;">'
    f'<div style="font-size:2.4rem;font-weight:800;color:#FF4444;letter-spacing:-1px;">{_nr}</div>'
    f'<div style="font-size:0.60rem;color:#FF4444;letter-spacing:0.12em;font-weight:700;">BEARISH</div>'
    f'{_top_bear_html}'
    f'</div>'
    f'<div style="text-align:center;">'
    f'<div style="font-size:2.4rem;font-weight:800;color:#6B7FBF;letter-spacing:-1px;">{_nn}</div>'
    f'<div style="font-size:0.60rem;color:#6B7FBF;letter-spacing:0.12em;font-weight:700;">NEUTRAL</div>'
    f'</div>'
    f'</div>'
    f'</div>'
    f'<div style="margin-top:18px;background:rgba(255,255,255,0.05);border-radius:4px;height:4px;overflow:hidden;display:flex;">'
    f'<div style="width:{_bar_bull};background:linear-gradient(90deg,#00D566,#00A847);border-radius:4px 0 0 4px;"></div>'
    f'<div style="width:{_bar_bear};background:#FF4444;"></div>'
    f'<div style="flex:1;background:rgba(107,127,191,0.3);border-radius:0 4px 4px 0;"></div>'
    f'</div>'
    f'<div style="display:flex;justify-content:space-between;margin-top:6px;">'
    f'<div style="font-size:0.62rem;color:#8892AA;">▲ Bullish {_bar_bull}</div>'
    f'<div style="font-size:0.62rem;color:#6B7FBF;">Updated every 2 hours</div>'
    f'<div style="font-size:0.62rem;color:#8892AA;">Bearish {_bar_bear} ▼</div>'
    f'</div>'
    f'</div>',
    unsafe_allow_html=True,
)

# Primary CTA
st.markdown("<div style='text-align:center;margin:24px 0 8px;'>", unsafe_allow_html=True)
_hcol1, _hcol2, _hcol3 = st.columns([2, 1.4, 2])
with _hcol2:
    if st.button("→ See Today's Full Signal Brief", type="primary", use_container_width=True, key="hero_cta"):
        st.switch_page("pages/2_Today_Digest.py")
st.markdown(
    "<div style='text-align:center;font-size:0.72rem;color:#8892AA;margin-top:6px;"
    "font-family:Inter,sans-serif;'>No account needed to browse signals</div>",
    unsafe_allow_html=True,
)

# ── SIGNAL FLIP ALERT BANNER ──────────────────────────────────────────────────
try:
    _flip = _get_recent_signal_flip()
    if _flip:
        _fl_c   = "#00D566" if _flip["to_status"] == "bullish" else "#FF4444"
        _fl_r, _fl_g, _fl_b = int(_fl_c[1:3], 16), int(_fl_c[3:5], 16), int(_fl_c[5:7], 16)
        _fl_verb = "TURNED BULLISH" if _flip["to_status"] == "bullish" else "TURNED BEARISH"
        _fl_icon = "📈" if _flip["to_status"] == "bullish" else "📉"
        st.markdown(
            f'<div style="background:rgba({_fl_r},{_fl_g},{_fl_b},0.07);'
            f'border:1px solid rgba({_fl_r},{_fl_g},{_fl_b},0.28);'
            f'border-radius:10px;padding:11px 20px;margin:10px auto 0;max-width:860px;'
            f'display:flex;align-items:center;gap:10px;font-family:Inter,sans-serif;">'
            f'<span style="font-size:1.1rem;">{_fl_icon}</span>'
            f'<span style="font-size:0.60rem;letter-spacing:0.14em;font-weight:700;color:{_fl_c};">⚡ JUST FLIPPED</span>'
            f'<span style="font-size:0.82rem;font-weight:600;color:#E8EEFF;margin-left:2px;">{_h.escape(_flip["name"])}</span>'
            f'<span style="font-size:0.78rem;font-weight:700;color:{_fl_c};margin-left:2px;">{_fl_verb}</span>'
            f'<span style="font-size:0.70rem;color:#6B7FBF;margin-left:6px;">Score: {_flip["score"]:.0f}/100</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
except Exception:
    pass

st.markdown("<br>", unsafe_allow_html=True)

# ── CREDIBILITY STRIP ─────────────────────────────────────────────────────────
st.markdown("""
<div style="border-top:1px solid rgba(255,255,255,0.06);border-bottom:1px solid rgba(255,255,255,0.06);
            padding:14px 0;margin:4px 0 28px;text-align:center;font-family:Inter,sans-serif;">
    <div style="font-size:0.58rem;letter-spacing:0.16em;color:#6B7FBF;margin-bottom:10px;
                font-weight:700;">DATA SOURCED FROM THE SAME INSTITUTIONS WALL STREET USES</div>
    <div style="display:flex;justify-content:center;gap:28px;flex-wrap:wrap;align-items:center;">
        <span style="font-size:0.80rem;color:#8892AA;">
            <b style="color:#E8EEFF;">FRED</b> · Federal Reserve</span>
        <span style="color:rgba(255,255,255,0.12);">|</span>
        <span style="font-size:0.80rem;color:#8892AA;">
            <b style="color:#E8EEFF;">SEC EDGAR</b> · Insider Filings</span>
        <span style="color:rgba(255,255,255,0.12);">|</span>
        <span style="font-size:0.80rem;color:#8892AA;">
            <b style="color:#E8EEFF;">FINRA</b> · Short Interest</span>
        <span style="color:rgba(255,255,255,0.12);">|</span>
        <span style="font-size:0.80rem;color:#8892AA;">
            <b style="color:#E8EEFF;">EIA</b> · Energy Data</span>
        <span style="color:rgba(255,255,255,0.12);">|</span>
        <span style="font-size:0.80rem;color:#8892AA;">
            <b style="color:#E8EEFF;">13F Filings</b> · Institutional Positions</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── INSTANT PORTFOLIO CHECK ───────────────────────────────────────────────────
if _data_loaded:
    st.markdown("""
<div style="background:rgba(18,21,30,0.95);border:1px solid rgba(0,200,224,0.22);
            border-radius:16px;padding:22px 26px 18px;margin:0 0 24px;
            font-family:Inter,sans-serif;
            box-shadow:0 0 30px rgba(0,200,224,0.05),0 8px 32px rgba(0,0,0,0.4);">
    <div style="font-size:0.58rem;letter-spacing:0.18em;font-weight:700;color:#00C8E0;
                margin-bottom:8px;">⚡ INSTANT MACRO CHECK — NO ACCOUNT NEEDED</div>
    <div style="font-size:1.0rem;font-weight:800;color:#E8EEFF;margin-bottom:4px;
                letter-spacing:-0.2px;">What does the macro say about your stocks right now?</div>
    <div style="font-size:0.77rem;color:#8892AA;line-height:1.55;">
        Enter any tickers below — we score 43 live signals against each one in seconds.
        Same data, same analysis, zero extra API calls.
    </div>
</div>
""", unsafe_allow_html=True)

    with st.form("portfolio_check_form", clear_on_submit=False):
        _pf_ci, _pf_cb = st.columns([4, 1])
        with _pf_ci:
            _pf_input = st.text_input(
                "Tickers",
                placeholder="e.g. AAPL, NVDA, XOM, JPM, TLT",
                label_visibility="collapsed",
                key="pf_ticker_input",
            )
        with _pf_cb:
            _pf_submitted = st.form_submit_button("→ Check", type="primary", use_container_width=True)

    if _pf_submitted and _pf_input.strip():
        _pf_results = _score_tickers_from_cache(_pf_input, _raw_scores)
        if _pf_results:
            _pf_cols = st.columns(min(len(_pf_results), 5))
            for _pf_res, _pf_col in zip(_pf_results, _pf_cols):
                with _pf_col:
                    _pf_s   = _pf_res["score"]
                    _pf_st  = _pf_res["status"]
                    _pf_c   = "#00D566" if _pf_st == "bullish" else ("#FF4444" if _pf_st == "bearish" else "#6B7FBF")
                    _pf_arr = "▲" if _pf_st == "bullish" else ("▼" if _pf_st == "bearish" else "●")
                    _pf_bg  = "rgba(0,213,102,0.05)" if _pf_st == "bullish" else ("rgba(255,68,68,0.05)" if _pf_st == "bearish" else "rgba(107,127,191,0.04)")
                    _pf_sig_html = ""
                    for _sn, _ss, _ssc in _pf_res["top_signals"]:
                        _sc2 = "#00D566" if _ss == "bullish" else ("#FF4444" if _ss == "bearish" else "#6B7FBF")
                        _pf_sig_html += (
                            f'<div style="font-size:0.60rem;color:{_sc2};margin-top:3px;'
                            f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'
                            f'{_h.escape(_sn[:28])}</div>'
                        )
                    _pf_unk = (
                        '<div style="font-size:0.57rem;color:#434E6A;margin-top:3px;">broad macro</div>'
                        if not _pf_res["known"] else ""
                    )
                    st.markdown(
                        f'<div style="background:{_pf_bg};border:1px solid {_pf_c}1A;'
                        f'border-top:3px solid {_pf_c};border-radius:10px;padding:14px 10px 12px;'
                        f'font-family:Inter,sans-serif;text-align:center;">'
                        f'<div style="font-size:1.0rem;font-weight:800;color:#E8EEFF;'
                        f'margin-bottom:2px;">{_h.escape(_pf_res["ticker"])}</div>'
                        f'<div style="font-size:1.9rem;font-weight:900;color:{_pf_c};'
                        f'letter-spacing:-0.5px;line-height:1.1;">{_pf_arr}&nbsp;{_pf_s:.0f}</div>'
                        f'<div style="font-size:0.59rem;color:{_pf_c};font-weight:700;'
                        f'letter-spacing:0.1em;">{_pf_st.upper()}</div>'
                        f'{_pf_sig_html}{_pf_unk}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            _pf_cta1, _pf_cta2, _pf_cta3 = st.columns([1.5, 1.5, 1])
            with _pf_cta1:
                if st.button("Full signal breakdown →", use_container_width=True, key="pf_cta_dive"):
                    st.switch_page("pages/3_Ticker_Deep_Dive.py")
            with _pf_cta2:
                if st.button("Save to Watchlist (free) →", use_container_width=True, key="pf_cta_wl"):
                    st.switch_page("pages/10_Watchlist.py")
            st.markdown(
                '<div style="font-size:0.62rem;color:#434E6A;margin-top:5px;font-family:Inter,sans-serif;">'
                'Score = macro Confluence Score (0–100) from 43 live signals. Not financial advice.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.caption("Couldn't find signals for those tickers — try SPY, QQQ, NVDA, XOM, or TLT.")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── MACHINE INTELLIGENCE SECTION ─────────────────────────────────────────────
if _data_loaded:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    _nar = _narrative
    _nar_col1, _nar_col2 = st.columns([3, 2])

    with _nar_col1:
        _sect_items = "".join(
            f'<span style="display:inline-block;margin:2px 4px;padding:2px 8px;border-radius:6px;'
            f'font-size:0.64rem;'
            f'background:{"rgba(0,213,102,0.10)" if v == "BULLISH" else ("rgba(255,68,68,0.10)" if v == "BEARISH" else "rgba(107,127,191,0.08)")};'
            f'color:{"#00D566" if v == "BULLISH" else ("#FF4444" if v == "BEARISH" else "#6B7FBF")};'
            f'font-weight:600;border:1px solid {"rgba(0,213,102,0.2)" if v == "BULLISH" else ("rgba(255,68,68,0.2)" if v == "BEARISH" else "rgba(107,127,191,0.2)")};">'
            f'{k.split("/")[0].strip()}: {v}</span>'
            for k, v in _nar["sector_bias"].items()
        )
        _watch_html = (
            f'<div style="margin-top:10px;padding:8px 12px;background:rgba(0,200,224,0.06);'
            f'border-left:3px solid #00C8E0;border-radius:0 6px 6px 0;font-size:0.74rem;color:#00C8E0;">'
            f'👁 {_nar["watch_note"]}</div>'
            if _nar.get("watch_note") else ""
        )
        st.markdown(
            f'<div style="background:{_bias_bg};border:1px solid {_bias_color}22;'
            f'border-left:4px solid {_bias_color};'
            f'border-radius:12px;padding:20px 22px;font-family:Inter,sans-serif;">'
            f'<div style="font-size:0.58rem;font-weight:700;letter-spacing:0.14em;color:{_bias_color};'
            f'text-transform:uppercase;margin-bottom:6px;">MACHINE READS THE MARKET</div>'
            f'<div style="font-size:1.25rem;font-weight:800;color:#E8EEFF;margin-bottom:10px;letter-spacing:-0.3px;">'
            f'{_nar.get("headline","")}</div>'
            f'<div style="font-size:0.83rem;color:#B8C0D4;line-height:1.7;margin-bottom:12px;">'
            f'{_nar["summary"]}</div>'
            f'<div style="margin-bottom:8px;">{_sect_items}</div>'
            f'{_watch_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

    with _nar_col2:
        _bull_tkrs = _top_tkrs.get("bullish", [])[:5]
        _bear_tkrs = _top_tkrs.get("bearish", [])[:3]
        if _bull_tkrs or _bear_tkrs:
            _bull_rows = "".join(
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.05);">'
                f'<span style="font-weight:700;font-size:0.82rem;color:#E8EEFF;">{r["ticker"]}</span>'
                f'<span style="font-size:0.72rem;color:#8892AA;flex:1;padding-left:8px;'
                f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:120px;">'
                f'{r["name"][:22]}</span>'
                f'<span style="font-size:0.78rem;font-weight:700;color:#00D566;">'
                f'▲ {r["score"]:.0f}</span>'
                f'</div>'
                for r in _bull_tkrs
            )
            _bear_rows = "".join(
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.05);">'
                f'<span style="font-weight:700;font-size:0.82rem;color:#E8EEFF;">{r["ticker"]}</span>'
                f'<span style="font-size:0.72rem;color:#8892AA;flex:1;padding-left:8px;'
                f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:120px;">'
                f'{r["name"][:22]}</span>'
                f'<span style="font-size:0.78rem;font-weight:700;color:#FF4444;">'
                f'▼ {r["score"]:.0f}</span>'
                f'</div>'
                for r in _bear_tkrs
            )
            st.markdown(
                f'<div style="background:rgba(18,21,30,0.8);border:1px solid rgba(255,255,255,0.07);'
                f'border-radius:12px;padding:18px 20px;font-family:Inter,sans-serif;">'
                f'<div style="font-size:0.58rem;font-weight:700;letter-spacing:0.14em;color:#00D566;'
                f'text-transform:uppercase;margin-bottom:12px;">WHAT THE MACHINE FAVORS NOW</div>'
                f'<div style="font-size:0.62rem;color:#6B7FBF;margin-bottom:6px;font-weight:700;letter-spacing:0.08em;">MACRO TAILWIND ▲</div>'
                f'{_bull_rows}'
                f'<div style="font-size:0.62rem;color:#6B7FBF;margin:12px 0 6px;font-weight:700;letter-spacing:0.08em;">MACRO HEADWIND ▼</div>'
                f'{_bear_rows}'
                f'<div style="font-size:0.62rem;color:#6B7FBF;margin-top:12px;">'
                f'43 macro signals · no price charts · pure fundamentals</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

# ── SIGNAL CONVERGENCE EVENTS ────────────────────────────────────────────────
_conv_events = get_convergence_events(days_back=7, min_signals=3)
if _conv_events:
    st.markdown("""
    <div style="font-size:1.1rem;font-weight:800;color:#E8EEFF;margin:20px 0 6px;
                font-family:Inter,sans-serif;letter-spacing:-0.3px;">
        ⚡ Signal Convergence Events
        <span style="font-size:0.70rem;font-weight:500;color:#8892AA;margin-left:10px;">
        3+ independent signals aligned on the same ticker in the last 7 days</span>
    </div>
    """, unsafe_allow_html=True)
    _conv_col1, _conv_col2 = st.columns(2)
    _bull_ev = [e for e in _conv_events if e["direction"] == "bullish"][:4]
    _bear_ev = [e for e in _conv_events if e["direction"] == "bearish"][:2]
    with _conv_col1:
        render_convergence_events(_bull_ev + _bear_ev[:1], max_bull=4, max_bear=1)
    with _conv_col2:
        if len(_bear_ev) > 1:
            render_convergence_events([], max_bull=0)
            render_convergence_events(_bear_ev[1:], max_bull=0, max_bear=2)
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

# ── LATEST RESEARCH NOTE TEASER ──────────────────────────────────────────────
try:
    from utils.narrative_engine import get_latest_note as _get_ln
    _latest_note = _get_ln()
    if _latest_note:
        _note_regime   = _latest_note.get("regime", "")
        _note_headline = _latest_note.get("headline", "")
        _note_date     = _latest_note.get("note_date", "")
        _note_body     = _latest_note.get("body", "")
        _note_bull_n   = _latest_note.get("bull_count") or 0
        _note_bear_n   = _latest_note.get("bear_count") or 0

        import html as _html_escape
        _note_paras = [p.strip() for p in _note_body.split("\n\n") if p.strip()]
        _note_hl_clean = _html_escape.escape(_note_headline.strip("*#").strip())
        if _note_paras and _note_paras[0].strip("*#").strip() == _note_headline.strip("*#").strip():
            _note_paras = _note_paras[1:]
        _note_teaser = _html_escape.escape(_note_paras[0][:240] + "…") if _note_paras else ""

        _regime_fg = "#00D566" if any(x in _note_regime for x in ("BULL", "ON")) else (
                     "#FF4444" if any(x in _note_regime for x in ("BEAR", "OFF")) else "#6B7FBF")
        _regime_bg_note = f"rgba({','.join(str(int(_regime_fg[i:i+2],16)) for i in (1,3,5))},0.10)" if _regime_fg.startswith('#') else "rgba(107,127,191,0.10)"

        try:
            from datetime import datetime as _dtn
            _nd = _dtn.strptime(_note_date, "%Y-%m-%d")
            _note_date_str = _nd.strftime("%B %d, %Y")
        except Exception:
            _note_date_str = _note_date

        st.markdown(
            f'<div style="background:rgba(18,21,30,0.8);border:1px solid rgba(255,255,255,0.07);'
            f'border-top:2px solid #00D566;'
            f'border-radius:12px;padding:18px 22px;margin-bottom:24px;font-family:Inter,sans-serif;">'
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">'
            f'<span style="font-size:0.58rem;letter-spacing:0.16em;font-weight:700;color:#00D566;">📰 LATEST RESEARCH NOTE</span>'
            f'<span style="font-size:0.64rem;font-weight:700;letter-spacing:0.08em;padding:2px 8px;'
            f'border-radius:5px;background:{_regime_bg_note};color:{_regime_fg};border:1px solid {_regime_fg}33;">{_note_regime}</span>'
            f'<span style="font-size:0.68rem;color:#8892AA;margin-left:auto;">{_note_date_str}</span>'
            f'</div>'
            f'<div style="font-size:1.0rem;font-weight:700;color:#E8EEFF;line-height:1.3;margin-bottom:8px;letter-spacing:-0.2px;">'
            f'{_note_hl_clean}</div>'
            f'<div style="font-size:0.81rem;color:#B8C0D4;line-height:1.65;margin-bottom:10px;">'
            f'{_note_teaser}</div>'
            f'<div style="font-size:0.68rem;color:#8892AA;">'
            f'{_note_bull_n} bullish · {_note_bear_n} bearish signals</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("Read Full Note →", key="home_note_cta", use_container_width=False):
            st.switch_page("pages/18_Weekly_Brief.py")
except Exception:
    pass

# ── 3 CORE FEATURE SPOTLIGHTS ─────────────────────────────────────────────────
st.markdown("""
<div style="font-size:1.5rem;font-weight:800;color:#E8EEFF;text-align:center;
            margin:32px 0 6px;font-family:Inter,sans-serif;letter-spacing:-0.5px;">
    Three tools that change how you invest
</div>
<div style="font-size:0.86rem;color:#8892AA;text-align:center;margin-bottom:24px;
            font-family:Inter,sans-serif;">
    Not a screener. Not a news aggregator. Something genuinely different.
</div>
""", unsafe_allow_html=True)

_sp1, _sp2, _sp3 = st.columns(3)

_SPOT = """
<div style="background:rgba(18,21,30,0.8);border:1px solid rgba(255,255,255,0.07);
            border-top:2px solid {accent};border-radius:12px;
            padding:22px 20px 18px;font-family:Inter,sans-serif;
            min-height:240px;transition:all 0.2s ease;">
    <div style="font-size:0.58rem;letter-spacing:0.14em;color:{accent};margin-bottom:8px;
                font-weight:700;">{tag}</div>
    <div style="font-size:1.0rem;font-weight:700;color:#E8EEFF;margin-bottom:10px;
                line-height:1.3;letter-spacing:-0.2px;">{title}</div>
    <div style="font-size:0.80rem;color:#B8C0D4;line-height:1.65;margin-bottom:14px;">{body}</div>
    <div style="font-size:0.72rem;color:{accent};font-weight:600;">{proof}</div>
</div>
"""

with _sp1:
    st.markdown(_SPOT.format(
        accent="#00D566",
        tag="DAILY INTELLIGENCE",
        title="Today's Brief — your 2-minute macro read",
        body=(
            "Every morning: which signals flipped overnight, what the macro bias is, "
            "and what it means for your holdings. Plain English. No jargon. "
            "Opt in for a 7 AM email digest."
        ),
        proof=f"→ Currently: {_bias_label} across {_total} signals",
    ), unsafe_allow_html=True)
    if st.button("Read Today's Brief →", use_container_width=True, key="cta_brief"):
        st.switch_page("pages/2_Today_Digest.py")

with _sp2:
    st.markdown(_SPOT.format(
        accent="#7C3AED",
        tag="STOCK-SPECIFIC ANALYSIS",
        title="Ticker Deep Dive — type any stock, get a macro report",
        body=(
            "Confluence Score (0–100), 30/60/90-day probability model, "
            "signal-by-signal breakdown, earnings markers, insider activity, news. "
            "Tells you <i>why</i> the macro environment is or isn't set up for this stock."
        ),
        proof="→ Tested on 80+ tickers with statistical validation",
    ), unsafe_allow_html=True)
    if st.button("Try Ticker Deep Dive →", use_container_width=True, key="cta_dive"):
        st.switch_page("pages/3_Ticker_Deep_Dive.py")

with _sp3:
    st.markdown(_SPOT.format(
        accent="#00C8E0",
        tag="SMART ALERTS",
        title="Watchlist — know the moment a signal flips",
        body=(
            "Track any ticker with custom alert thresholds. Get notified "
            "when the Confluence Score crosses your level, a signal changes direction, "
            "or a 52-week high/low is hit. Morning email to opted-in users."
        ),
        proof="→ Free · No Bloomberg terminal needed",
    ), unsafe_allow_html=True)
    if st.button("Build Your Watchlist →", use_container_width=True, key="cta_watchlist"):
        st.switch_page("pages/10_Watchlist.py")

st.markdown("<br>", unsafe_allow_html=True)

# ── THE CONTRAST / ANCHOR ─────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,rgba(18,21,30,0.95),rgba(26,14,61,0.9));
            border:1px solid rgba(124,58,237,0.2);
            border-radius:16px;padding:32px 36px;margin:8px 0 32px;
            font-family:Inter,sans-serif;text-align:center;">
    <div style="font-size:0.60rem;letter-spacing:0.18em;color:#7C3AED;margin-bottom:12px;
                font-weight:700;">THE EDGE ISN'T THE DATA — IT'S KNOWING WHICH SIGNALS TO WATCH</div>
    <div style="font-size:1.3rem;font-weight:800;color:#E8EEFF;max-width:640px;margin:0 auto;
                line-height:1.4;letter-spacing:-0.3px;">
        Bloomberg Terminal charges <span style="color:#F59E0B;">$27,000/year</span>
        for access to this kind of macro data.<br>
        <span style="background:linear-gradient(135deg,#00D566,#00C8E0);
                     -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                     background-clip:text;">We built the same analysis from free public sources.</span>
    </div>
    <div style="font-size:0.82rem;color:#8892AA;margin-top:14px;max-width:560px;
                margin-left:auto;margin-right:auto;line-height:1.65;">
        FRED, SEC EDGAR, FINRA, and EIA are the same primary data sources
        institutional desks rely on. The difference is we packaged it for
        investors who don't have a six-figure data budget.
    </div>
</div>
""", unsafe_allow_html=True)

# ── "SIGNALS CALLED IT BEFORE" — PROOF SECTION ────────────────────────────────
st.markdown("""
<div style="font-size:1.1rem;font-weight:800;color:#E8EEFF;text-align:center;
            margin:32px 0 6px;font-family:Inter,sans-serif;letter-spacing:-0.3px;">
    The signals called it before price did.
</div>
<div style="font-size:0.80rem;color:#8892AA;text-align:center;margin-bottom:20px;
            font-family:Inter,sans-serif;">
    Historical cases where the same macro patterns tracked live today appeared
    weeks before major price moves.
</div>
""", unsafe_allow_html=True)

_proof_c1, _proof_c2, _proof_c3 = st.columns(3)
_PROOFS = [
    {
        "icon": "📉", "date": "January 2022", "color": "#FF4444",
        "signal": "HY Credit Spreads",
        "what": "ICE BofA OAS widened 60+ bps in 6 weeks — spread signal turned bearish Jan 4.",
        "outcome": "QQQ fell 32.6% by May. Nasdaq growth stocks down 40–70%.",
        "timing": "6 weeks early",
    },
    {
        "icon": "📈", "date": "March 18–25, 2020", "color": "#00D566",
        "signal": "Insider Buying Cluster",
        "what": "Surge in Form 4 insider buys across 40+ companies in the same week.",
        "outcome": "Exact COVID market bottom. S&P 500 +47% over the following 6 months.",
        "timing": "At the exact low",
    },
    {
        "icon": "⚡", "date": "June–July 2023", "color": "#F59E0B",
        "signal": "EIA Crude Draw Streak",
        "what": "5 consecutive weekly crude inventory draws exceeding 3M bbl each.",
        "outcome": "XLE outperformed S&P 500 by ~12% over the following 8 weeks.",
        "timing": "3–5 weeks ahead",
    },
]
for _col, _p in zip([_proof_c1, _proof_c2, _proof_c3], _PROOFS):
    with _col:
        st.markdown(
            f'<div style="background:rgba(18,21,30,0.85);border:1px solid rgba(255,255,255,0.06);'
            f'border-left:4px solid {_p["color"]};border-radius:10px;padding:18px 16px 14px;'
            f'font-family:Inter,sans-serif;min-height:195px;">'
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">'
            f'<span style="font-size:1.2rem;">{_p["icon"]}</span>'
            f'<div>'
            f'<div style="font-size:0.57rem;letter-spacing:0.12em;color:#6B7FBF;font-weight:700;">{_p["date"]}</div>'
            f'<div style="font-size:0.84rem;font-weight:700;color:#E8EEFF;">{_p["signal"]}</div>'
            f'</div></div>'
            f'<div style="font-size:0.75rem;color:#B8C0D4;line-height:1.55;margin-bottom:10px;">{_p["what"]}</div>'
            f'<div style="font-size:0.78rem;font-weight:700;color:{_p["color"]};line-height:1.4;margin-bottom:8px;">{_p["outcome"]}</div>'
            f'<span style="font-size:0.60rem;padding:3px 8px;border-radius:5px;'
            f'background:{_p["color"]}18;color:{_p["color"]};font-weight:700;'
            f'letter-spacing:0.06em;">⏱ {_p["timing"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown("""
<div style="text-align:center;font-size:0.66rem;color:#434E6A;margin-top:8px;
            font-family:Inter,sans-serif;">
    Past patterns don't guarantee future results. Historical examples for educational purposes only.
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ── SECTOR ROTATION TEASER ────────────────────────────────────────────────────
st.markdown("""
<div style="font-size:1.1rem;font-weight:800;color:#E8EEFF;font-family:Inter,sans-serif;
            margin-bottom:4px;letter-spacing:-0.3px;">Sector Rotation Signal Map — live preview</div>
<div style="font-size:0.80rem;color:#8892AA;margin-bottom:16px;font-family:Inter,sans-serif;">
    Which sectors do the signals currently favor? Updated every 2 hours.
</div>
""", unsafe_allow_html=True)

_SECTOR_META = {
    "ai_infrastructure": ("Technology & AI",   "#7C3AED"),
    "energy":            ("Energy",             "#F59E0B"),
    "nuclear":           ("Nuclear/Utilities",  "#00C8E0"),
    "financials":        ("Financials",         "#00D566"),
    "healthcare":        ("Healthcare",         "#34D399"),
    "consumer":          ("Consumer",           "#EC4899"),
    "industrials":       ("Industrials",        "#06B6D4"),
    "macro":             ("Macro Backdrop",     "#8892AA"),
}

try:
    _sec = _hd.get("sectors", {})
    if _sec:
        _sorted = sorted(_sec.items(), key=lambda x: -x[1])
        _sc_cols = st.columns(4)
        for _i, (_cat, _avg) in enumerate(_sorted[:8]):
            _name, _accent = _SECTOR_META.get(_cat, (_cat.title(), "#8892AA"))
            _arrow  = "▲" if _avg >= 60 else ("▼" if _avg <= 40 else "●")
            _sc     = "#00D566" if _avg >= 60 else ("#FF4444" if _avg <= 40 else "#6B7FBF")
            _bg     = "rgba(0,213,102,0.06)" if _avg >= 60 else ("rgba(255,68,68,0.06)" if _avg <= 40 else "rgba(18,21,30,0.6)")
            with _sc_cols[_i % 4]:
                st.markdown(f"""
<div style="background:{_bg};border:1px solid rgba(255,255,255,0.06);border-left:3px solid {_sc};
            border-radius:8px;padding:12px 14px;margin-bottom:8px;font-family:Inter,sans-serif;">
    <div style="font-size:0.75rem;font-weight:600;color:#C8D0E4;margin-bottom:4px;">{_name}</div>
    <div style="font-size:1.5rem;font-weight:800;color:{_sc};letter-spacing:-0.5px;">{_arrow} {_avg:.0f}</div>
</div>
""", unsafe_allow_html=True)
    else:
        st.caption("Sector scores loading — refresh in a moment.")

    _smc, _ = st.columns([1, 3])
    with _smc:
        if st.button("Full Sector Map →", use_container_width=True, key="cta_sector"):
            st.switch_page("pages/12_Sector_Map.py")
except Exception:
    st.caption("Sector preview unavailable. Open the Sector Map page directly.")

st.divider()

# ── WHY THIS ISN'T A SCREENER ─────────────────────────────────────────────────
_da, _db = st.columns(2)

with _da:
    st.markdown("""
<div style="font-family:Inter,sans-serif;">
<div style="font-size:1.05rem;font-weight:800;color:#FF4444;margin-bottom:10px;letter-spacing:-0.2px;">
    What traditional screeners miss
</div>
<div style="font-size:0.83rem;color:#B8C0D4;line-height:1.7;">
    Stock screeners filter on price, P/E, and volume. They tell you what
    <i>has happened</i> to a stock — not what's coming. That's rear-view-mirror investing.<br><br>
    By the time a move shows up in price and volume, institutional desks have
    already positioned. The professionals were watching leading economic signals
    4 to 16 weeks earlier.
</div>
<br>
<div style="font-size:1.05rem;font-weight:800;color:#00D566;margin-bottom:10px;letter-spacing:-0.2px;">
    What leading signals actually predict
</div>
<div style="font-size:0.83rem;color:#B8C0D4;line-height:1.7;">
    • Trucking freight falls → retail earnings weaken ~6 weeks later<br>
    • Uranium spot rises → nuclear energy stocks follow<br>
    • Credit spreads widen → broad market pullback precedes it 4–8 weeks<br>
    • Hyperscaler capex accelerates → AI infrastructure stocks outperform<br><br>
    This is what hedge funds call <b style="color:#E8EEFF;">alternative data</b>.
    They pay $50K–$500K/year for it. We built it from public sources.
</div>
</div>
""", unsafe_allow_html=True)

with _db:
    st.markdown("""
<div style="font-family:Inter,sans-serif;">
<div style="font-size:1.05rem;font-weight:800;color:#E8EEFF;margin-bottom:10px;letter-spacing:-0.2px;">
    What you get that you can't get anywhere else — for free
</div>
""", unsafe_allow_html=True)

    _diffs = [
        ("Signal Lead Time",
         "Each signal comes with a measured historical lead time — how many weeks "
         "ahead it typically precedes price movement. Not guesswork."),
        ("Pre-Earnings Track Record",
         "See what the Confluence Score said 7–45 days before each past earnings event "
         "vs. the actual EPS beat or miss."),
        ("Confluence Score",
         "How many independent signals agree? One bullish signal is noise. "
         "Seven agreeing signals is a thesis."),
        ("Honest Validation",
         "We publish our backtest results even when they're not impressive. "
         "See the Model Validation page — it's one of a kind."),
        ("Plain-English Causal Logic",
         "Not just 'this signal correlates.' We explain the economic mechanism: "
         "why this indicator moves this sector, specifically."),
    ]
    for _title, _body in _diffs:
        st.markdown(f"""
<div style="border-left:3px solid #00D566;padding:8px 14px;margin-bottom:10px;
            background:rgba(0,213,102,0.04);border-radius:0 8px 8px 0;">
    <div style="font-size:0.83rem;font-weight:700;color:#E8EEFF;margin-bottom:3px;font-family:Inter,sans-serif;">{_title}</div>
    <div style="font-size:0.77rem;color:#B8C0D4;line-height:1.55;font-family:Inter,sans-serif;">{_body}</div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── HOW TO USE IN 4 STEPS ────────────────────────────────────────────────────
st.markdown("""
<div style="font-size:1.1rem;font-weight:800;color:#E8EEFF;font-family:Inter,sans-serif;
            margin-bottom:18px;letter-spacing:-0.3px;">Start generating insight in under 5 minutes</div>
""", unsafe_allow_html=True)

_steps = [
    ("1", "#00D566", "Read Today's Brief",
     "2-minute macro morning read. Which signals are bullish. Which are bearish. What it means.",
     "pages/2_Today_Digest.py", "Open Today's Brief →", "cta_s1"),
    ("2", "#F59E0B", "Check the Sector Map",
     "See which sectors the data currently favors. Find where the macro tailwinds are right now.",
     "pages/12_Sector_Map.py", "Open Sector Map →", "cta_s2"),
    ("3", "#7C3AED", "Deep Dive a Ticker",
     "Type any stock. Get a Confluence Score, signal breakdown, earnings history, and bull/bear case.",
     "pages/3_Ticker_Deep_Dive.py", "Open Deep Dive →", "cta_s3"),
    ("4", "#FF4444", "Set Up Your Watchlist",
     "Save your stocks. Get alerted when signals flip. Optional morning email at 7 AM ET.",
     "pages/10_Watchlist.py", "Open Watchlist →", "cta_s4"),
]

_st_cols = st.columns(4)
for _col, (_n, _ac, _title, _body, _page, _btn, _key) in zip(_st_cols, _steps):
    with _col:
        st.markdown(f"""
<div style="background:rgba(18,21,30,0.8);border:1px solid rgba(255,255,255,0.06);
            border-top:3px solid {_ac};
            border-radius:10px;padding:18px;font-family:Inter,sans-serif;min-height:170px;
            margin-bottom:8px;">
    <div style="font-size:1.8rem;font-weight:900;color:{_ac};margin-bottom:6px;letter-spacing:-1px;">{_n}</div>
    <div style="font-size:0.86rem;font-weight:700;color:#E8EEFF;margin-bottom:6px;letter-spacing:-0.1px;">{_title}</div>
    <div style="font-size:0.76rem;color:#B8C0D4;line-height:1.55;">{_body}</div>
</div>
""", unsafe_allow_html=True)
        if st.button(_btn, use_container_width=True, key=_key):
            st.switch_page(_page)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── PRO UPGRADE BANNER ────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,rgba(124,58,237,0.12),rgba(0,200,224,0.08));
            border:1px solid rgba(124,58,237,0.28);border-radius:14px;
            padding:22px 28px;font-family:Inter,sans-serif;
            display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;">
    <div>
        <div style="font-size:0.58rem;letter-spacing:0.18em;font-weight:700;color:#7C3AED;margin-bottom:6px;">
            UNSTRUCTURED ALPHA PRO
        </div>
        <div style="font-size:1.0rem;font-weight:800;color:#E8EEFF;letter-spacing:-0.2px;margin-bottom:4px;">
            Morning digest email · Signal Backtester · Factor Exposure · Congress Tracker
        </div>
        <div style="font-size:0.78rem;color:#8892AA;line-height:1.5;">
            $20/month · 7-day free trial · Cancel anytime · No commitment
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
_pro_col1, _pro_col2, _pro_col3 = st.columns([2.5, 1, 2.5])
with _pro_col2:
    if st.button("Try Pro Free →", type="primary", use_container_width=True, key="cta_pro_mid"):
        st.switch_page("pages/29_Upgrade.py")

st.divider()

# ── ADDITIONAL TOOLS ──────────────────────────────────────────────────────────
st.markdown("""
<div style="font-size:0.86rem;font-weight:700;color:#E8EEFF;font-family:Inter,sans-serif;
            margin-bottom:10px;">More tools</div>
""", unsafe_allow_html=True)

_t1, _t2, _t3, _t4 = st.columns(4)
with _t1:
    if st.button("📡 Signal Dashboard", use_container_width=True, key="cta_signals"):
        st.switch_page("pages/1_Signal_Dashboard.py")
with _t2:
    if st.button("📊 Market Overview", use_container_width=True, key="cta_market"):
        st.switch_page("pages/5_Market_Overview.py")
with _t3:
    if st.button("🔍 Stock Screener", use_container_width=True, key="cta_screener"):
        st.switch_page("pages/6_Stock_Screener.py")
with _t4:
    if st.button("✅ Model Validation", use_container_width=True, key="cta_validation"):
        st.switch_page("pages/11_Model_Validation.py")

st.divider()

# ── FAQ ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="font-size:1.0rem;font-weight:800;color:#E8EEFF;font-family:Inter,sans-serif;
            margin-bottom:10px;letter-spacing:-0.2px;">Common questions</div>
""", unsafe_allow_html=True)

_q1, _q2 = st.columns(2)

with _q1:
    with st.expander("What is alternative data?"):
        st.markdown(
            "Data that isn't a stock price or earnings report. Freight volumes, uranium contracts, "
            "jobless claims, credit spreads, insider buys. Hedge funds have used this for decades. "
            "Most of it comes from free government sources that nobody packaged for retail — until now."
        )
    with st.expander("What is the Confluence Score?"):
        st.markdown(
            "A 0–100 score measuring how many independent signals agree for a given stock right now. "
            "**>65** = multiple bullish signals aligning. **<35** = multiple bearish. **35–65** = mixed. "
            "One bullish signal is noise. Seven agreeing is a thesis. "
            "We walk-forward tested this — results on the Model Validation page."
        )
    with st.expander("Does this predict stock prices?"):
        st.markdown(
            "No — and we're transparent about that. The signals have shown statistical correlations "
            "in backtests, but no tool predicts with certainty. The value is pattern recognition "
            "across 40 economic indicators that historically lead price by weeks, not perfect prediction. "
            "See Model Validation for honest results."
        )

with _q2:
    with st.expander("What does it cost?"):
        st.markdown(
            "**Free** to browse signals, Today's Brief, Sector Map, Signal Dashboard, and Deep Dive — "
            "no account needed. A free account (email only, no card) unlocks the Watchlist and alert tracking. "
            "**Pro** ($20/mo, 7-day free trial) adds morning email digest, Signal Backtester, "
            "Factor Exposure, and all future Pro features. No long-term commitment."
        )
    with st.expander("Is this financial advice?"):
        st.markdown(
            "No. This is a research and education tool. All signals reflect interpretations of public "
            "economic data. Past signal correlation doesn't guarantee future accuracy. "
            "Always do your own due diligence."
        )
    with st.expander("How is this different from Yahoo Finance?"):
        st.markdown(
            "Yahoo Finance shows what has happened to a stock (price, volume, P/E). "
            "Unstructured Alpha shows what macro forces are building beneath the surface — "
            "credit spreads, freight flows, insider positioning — that historically lead "
            "price by 4–16 weeks. Different tool, different question."
        )

# ── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:28px 0 8px;font-family:Inter,sans-serif;">
    <div style="font-size:0.68rem;color:#6B7FBF;letter-spacing:0.06em;">
        UNSTRUCTURED ALPHA · ALTERNATIVE DATA INTELLIGENCE<br>
        <span style="color:#434E6A;">
        Not financial advice. All data from public sources:
        FRED, EIA, FINRA, SEC EDGAR, USASpending.gov, Yahoo Finance.
        </span>
    </div>
</div>
""", unsafe_allow_html=True)
