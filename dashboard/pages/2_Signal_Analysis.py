"""
RETIRED — this page has been consolidated into Ticker Deep Dive.

The Lead Time Optimizer / lag-scan / rolling-correlation tools that used to
live on this standalone page now live in the "Deep Correlation Scan — Lead
Time Optimizer" section near the bottom of the Ticker Deep Dive page, where
they reuse data already fetched for the ticker you're analyzing instead of
requiring a second, separate signal+ticker lookup.

This file is kept only as a harmless stub (the platform this app runs on
doesn't allow deleting files from this folder) and is no longer registered
in app.py's navigation, so it won't appear in the sidebar. If you land here
directly, you'll be redirected automatically.
"""

import streamlit as st

st.set_page_config(page_title="Signal Analysis (Retired) — UA", layout="wide")

st.info(
    "This page has been merged into **Ticker Deep Dive** — look for the "
    "**Deep Correlation Scan — Lead Time Optimizer** section there. Redirecting…"
)

if st.button("Go to Ticker Deep Dive now"):
    st.switch_page("pages/3_Ticker_Deep_Dive.py")
