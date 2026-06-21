"""
RETIRED — this page has been consolidated into Market Overview.

Growth Indicators, Labor Market, Consumer & Inflation, the official FRED
10Y-2Y yield curve, and the Economic Releases calendar now all live at the
bottom of the Market Overview page, alongside the live market data that used
to require a second page click to cross-reference against.

This file is kept only as a harmless stub (the platform this app runs on
doesn't allow deleting files from this folder) and is no longer registered
in app.py's navigation, so it won't appear in the sidebar. If you land here
directly, you'll be redirected automatically.
"""

import streamlit as st

st.set_page_config(page_title="Macro Monitor (Retired) — UA", layout="wide")

st.info(
    "This page has been merged into **Market Overview** — scroll to the bottom "
    "for Growth Indicators, Labor Market, Consumer & Inflation, and the Economic "
    "Releases calendar. Redirecting…"
)

if st.button("Go to Market Overview now"):
    st.switch_page("pages/5_Market_Overview.py")
