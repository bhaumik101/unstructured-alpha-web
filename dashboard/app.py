"""
Unstructured Alpha — Signal Intelligence Dashboard
===================================================
Navigation router. Each page handles its own set_page_config.

Run locally:
    pip install -r requirements.txt
    streamlit run app.py

Accounts: every page requires a logged-in user (see utils/auth_ui.py).
Deliberately does NOT call st.set_page_config() here -- every routed page
already calls it itself as that page's first Streamlit command, and
Streamlit only allows ONE set_page_config() call per script run. On a run
where the user isn't logged in yet, require_login() renders the login
form and calls st.stop() before pg.run() ever reaches a page, so no
conflict; on a run where they're already logged in, require_login()
returns immediately without rendering anything, leaving the routed page's
own set_page_config() call as the genuine first command.
"""

import streamlit as st

from utils.db import init_db
from utils.auth_ui import require_login

init_db()
current_user = require_login()

pg = st.navigation(
    {
        "": [
            st.Page("pages/home_page.py",        title="Home",             default=True),
        ],
        "Signals": [
            st.Page("pages/1_Signal_Dashboard.py", title="Signal Dashboard"),
        ],
        "Research": [
            st.Page("pages/3_Ticker_Deep_Dive.py", title="Ticker Deep Dive"),
            st.Page("pages/4_Power_Supercycle.py", title="Power Supercycle"),
        ],
        "Market": [
            st.Page("pages/5_Market_Overview.py",  title="Market Overview"),
            st.Page("pages/6_Stock_Screener.py",   title="Stock Screener"),
        ],
        "Alerts": [
            st.Page("pages/10_Alerts.py",           title="Alerts"),
        ],
        "Info": [
            st.Page("pages/8_About.py",            title="About"),
            st.Page("pages/9_AI_Assistant.py",     title="AI Assistant"),
        ],
    },
    position="sidebar",
)

pg.run()
