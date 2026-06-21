"""
Unstructured Alpha — Signal Intelligence Dashboard
===================================================
Navigation router. Each page handles its own set_page_config.

Run locally:
    pip install -r requirements.txt
    streamlit run app.py
"""

import streamlit as st

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
