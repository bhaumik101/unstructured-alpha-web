"""
Page 10 — Alerts
Watchlist management + notification feed for the alert engine in
utils/alerts.py. Triggers (per the user's explicit scoping): Confluence
Score threshold crossings, price moves (52-week high/low and % moves), and
differentiator-signal changes (insider activity, short interest, 13F).

Honesty check on delivery: this page is the IN-APP notification center.
Email delivery was explicitly scoped as a fast-follow, not built yet --
that requires an actual scheduled job running outside this Streamlit
process (a cron job, a hosted scheduler, etc.) plus an email-sending
service, which is real infrastructure, not just a feature on this page.
The "Check Watchlist Now" button below runs the same evaluation logic that
job would call, but only when someone has this page open and clicks it --
it does not run on a timer in the background.
"""

import streamlit as st

from utils.config import TICKERS
from utils import alerts_db
from utils.alerts import evaluate_watchlist
from utils.header import render_header, render_sidebar_base, ticker_label

st.set_page_config(page_title="Alerts — UA", layout="wide")
render_header("Alerts")
render_sidebar_base()

alerts_db.init_db()

st.markdown("# Alerts")
st.caption("Get notified when a watched ticker's Confluence Score crosses a threshold, its price moves "
           "sharply, or a differentiator signal (insider activity, short interest, 13F positioning) changes.")

with st.expander("How this works — and what's not built yet"):
    st.markdown("""
    **Triggers checked for every watched ticker:**

    - **Confluence Score threshold crossing** — fires when the score moves from below your bullish
      threshold to at or above it (or the reverse for bearish), not every time it simply stays above —
      otherwise the feed would just repeat the same alert on every check.
    - **Price moves** — a single-check % move past your threshold, or a genuine new 52-week high/low.
    - **Differentiator signal changes** — insider buy/sell clustering, FINRA short interest trend, or
      curated-fund 13F positioning flipping between bullish/bearish/neutral.

    **Delivery — in-app only right now.** This page is the notification center. Email alerts were
    explicitly scoped as a fast-follow, not built yet: real email delivery needs a scheduled job that
    runs even when nobody has this page open, plus an email-sending service (e.g. SendGrid, SES) and
    its own credentials — that's infrastructure beyond what a Streamlit page can do by itself. The
    "Check Watchlist Now" button below runs the exact same evaluation logic a scheduled job would, but
    only fires when you click it while this page is open.

    **Nothing fires on the very first check** for a newly-watched ticker — there's no prior snapshot
    yet to compare against, so the first check just establishes a baseline silently.
    """)

st.divider()

# ── Watchlist management ──────────────────────────────────────────────────────
st.markdown('<div class="section-header">WATCHLIST</div>', unsafe_allow_html=True)

col_add, col_thresh = st.columns([1, 2])
with col_add:
    new_ticker = st.text_input("Add a ticker to watch:", key="new_watch_ticker", max_chars=10).upper().strip()
with col_thresh:
    st.markdown("**Thresholds for this ticker:**")
    t1, t2, t3 = st.columns(3)
    with t1:
        bull_thresh = st.number_input("Bullish score ≥", min_value=50.0, max_value=99.0, value=65.0, step=1.0, key="add_bull")
    with t2:
        bear_thresh = st.number_input("Bearish score ≤", min_value=1.0, max_value=50.0, value=35.0, step=1.0, key="add_bear")
    with t3:
        price_thresh = st.number_input("Price move % ≥", min_value=0.5, max_value=50.0, value=5.0, step=0.5, key="add_price")

if st.button("Add to Watchlist", type="primary", disabled=not new_ticker):
    alerts_db.add_to_watchlist(
        new_ticker,
        score_bull_threshold=bull_thresh,
        score_bear_threshold=bear_thresh,
        price_move_pct_threshold=price_thresh,
    )
    st.success(f"{new_ticker} added to watchlist.")
    st.rerun()

watchlist = alerts_db.get_watchlist()

if not watchlist:
    st.info("Your watchlist is empty. Add a ticker above to start tracking it for alerts.")
else:
    for row in watchlist:
        ticker = row["ticker"]
        company = TICKERS.get(ticker, {}).get("name", "")
        label = f"{ticker} — {company}" if company else ticker
        wc1, wc2, wc3, wc4, wc5 = st.columns([2, 1, 1, 1, 1])
        with wc1:
            st.markdown(f"**{label}**")
        with wc2:
            st.caption(f"Bull ≥ {row['score_bull_threshold']:.0f}")
        with wc3:
            st.caption(f"Bear ≤ {row['score_bear_threshold']:.0f}")
        with wc4:
            st.caption(f"Move ≥ {row['price_move_pct_threshold']:.1f}%")
        with wc5:
            if st.button("Remove", key=f"remove_{ticker}"):
                alerts_db.remove_from_watchlist(ticker)
                st.rerun()

    st.divider()
    if st.button("Check Watchlist Now", type="primary"):
        with st.spinner(f"Checking {len(watchlist)} watched ticker(s)…"):
            new_alerts = evaluate_watchlist()
        if new_alerts:
            st.success(f"{len(new_alerts)} new alert(s) generated — see the feed below.")
        else:
            st.info("No new alerts. Either nothing crossed a threshold, or this is the first check "
                    "for one or more tickers (which just establishes a baseline).")
        st.rerun()

st.divider()

# ── Alert feed ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">ALERT FEED</div>', unsafe_allow_html=True)

unread_count = alerts_db.count_unread()
fc1, fc2, fc3 = st.columns([2, 1, 1])
with fc1:
    show_unread_only = st.checkbox(f"Show unread only ({unread_count} unread)", value=False)
with fc2:
    if st.button("Mark All Read", disabled=unread_count == 0):
        alerts_db.mark_all_read()
        st.rerun()
with fc3:
    if st.button("Clear Feed"):
        alerts_db.clear_all_alerts()
        st.rerun()

DIRECTION_COLOR = {"bullish": "#1B5E20", "bearish": "#7B1010"}
TYPE_LABEL = {
    "score_threshold": "Confluence Score",
    "price_move": "Price",
    "insider": "Insider Activity",
    "short_interest": "Short Interest",
    "13f": "13F Positioning",
}

alert_rows = alerts_db.get_alerts(unread_only=show_unread_only, limit=100)

if not alert_rows:
    st.info("No alerts yet. Add tickers to your watchlist and click \"Check Watchlist Now\" to evaluate them.")
else:
    for a in alert_rows:
        color = DIRECTION_COLOR.get(a["direction"], "#8B7355")
        unread_marker = "●" if not a["is_read"] else "○"
        type_label = TYPE_LABEL.get(a["alert_type"], a["alert_type"])
        company = TICKERS.get(a["ticker"], {}).get("name", "")
        ticker_disp = f"{a['ticker']} ({company})" if company else a["ticker"]
        st.markdown(f"""
        <div style="background:#F0EBE1;border-radius:6px;padding:10px 16px;margin-bottom:8px;
                    border-left:4px solid {color};font-family:Georgia,serif;">
            <span style="color:{color};font-weight:700;">{unread_marker} {ticker_disp}</span>
            <span style="color:#8B7355;font-size:0.78rem;letter-spacing:0.04em;"> · {type_label} · {a['created_at'][:16].replace('T', ' ')} UTC</span>
            <div style="color:#1A1612;margin-top:4px;">{a['message']}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("""
<div class="disclaimer">
<b>Not financial advice.</b> Alerts reflect signal and price changes in publicly available data,
not a recommendation to buy or sell. Do your own research before making any investment decision.
</div>
""", unsafe_allow_html=True)
