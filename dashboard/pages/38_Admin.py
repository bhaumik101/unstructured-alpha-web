# pages/38_Admin.py
# Unstructured Alpha — Admin Dashboard
#
# Gated to the admin email (ADMIN_EMAIL below). Anyone else sees a blank
# "access denied" message — no information leakage, no error stack traces.
#
# Metrics shown:
#   • Top-line KPIs: total users, verified, Pro, trial, free, digest opt-ins
#   • Acquisition: signups today / 7d / 30d
#   • Engagement: active users (login in last 7d / 30d)
#   • Conversion funnel: signup → verified → pro
#   • Daily signup chart (last 30 days)
#   • Recent signups table (last 50)
#   • Referral stats
#   • Watchlist adoption

import streamlit as st

st.set_page_config(
    page_title="Admin — UA",
    layout="wide",
    initial_sidebar_state="expanded",
)

from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, text

from utils.header import render_header, render_page_header, render_sidebar_base
from utils.db import engine, users, referrals, watchlist
from utils.theme import inject_premium_css

ADMIN_EMAIL = "bpgiri2005@gmail.com"

render_header("Admin")
render_sidebar_base()
inject_premium_css()

# ── Access gate ───────────────────────────────────────────────────────────────

current_user = st.session_state.get("user", {}).get("email", "")
if current_user != ADMIN_EMAIL:
    st.error("Access denied.")
    st.stop()

render_page_header(
    "Admin Dashboard",
    "User metrics, acquisition funnel, and engagement — live from the DB.",
    icon="🛠️",
)

# ── Query helpers ─────────────────────────────────────────────────────────────

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


@st.cache_data(ttl=60)  # refresh every minute
def load_metrics() -> dict:
    """Pull all admin metrics in one DB trip bundle. Returns a flat dict."""
    now = _now_utc()
    d1  = _iso(now - timedelta(days=1))
    d7  = _iso(now - timedelta(days=7))
    d30 = _iso(now - timedelta(days=30))

    with engine.connect() as conn:
        # ── Top-line counts ────────────────────────────────────────────────
        total        = conn.execute(select(func.count()).select_from(users)).scalar() or 0
        verified     = conn.execute(
            select(func.count()).where(users.c.email_verified == True)  # noqa: E712
        ).scalar() or 0
        pro_count    = conn.execute(
            select(func.count()).where(users.c.subscription_tier == "pro")
        ).scalar() or 0
        trial_count  = conn.execute(
            select(func.count()).where(
                (users.c.subscription_tier == "pro") &
                (users.c.trial_end_at != None)  # noqa: E711
            )
        ).scalar() or 0
        free_count   = conn.execute(
            select(func.count()).where(users.c.subscription_tier == "free")
        ).scalar() or 0
        digest_count = conn.execute(
            select(func.count()).where(users.c.digest_opted_in == True)  # noqa: E712
        ).scalar() or 0

        # ── Acquisition ───────────────────────────────────────────────────
        new_today = conn.execute(
            select(func.count()).where(users.c.created_at >= d1)
        ).scalar() or 0
        new_7d    = conn.execute(
            select(func.count()).where(users.c.created_at >= d7)
        ).scalar() or 0
        new_30d   = conn.execute(
            select(func.count()).where(users.c.created_at >= d30)
        ).scalar() or 0

        # ── Engagement ────────────────────────────────────────────────────
        active_7d  = conn.execute(
            select(func.count()).where(
                (users.c.last_login_at != None) &  # noqa: E711
                (users.c.last_login_at >= d7)
            )
        ).scalar() or 0
        active_30d = conn.execute(
            select(func.count()).where(
                (users.c.last_login_at != None) &  # noqa: E711
                (users.c.last_login_at >= d30)
            )
        ).scalar() or 0

        # ── Daily signups (last 30 days) ──────────────────────────────────
        # We can't use DATE() portably across SQLite/Postgres in SQLAlchemy
        # Core easily, so pull the raw created_at strings and bucket in Python.
        rows = conn.execute(
            select(users.c.created_at).where(users.c.created_at >= d30)
        ).fetchall()
        daily_counts: dict[str, int] = {}
        for (ts,) in rows:
            day = ts[:10] if ts else None  # first 10 chars = YYYY-MM-DD
            if day:
                daily_counts[day] = daily_counts.get(day, 0) + 1

        # ── Recent signups (last 50) ──────────────────────────────────────
        recent = conn.execute(
            select(
                users.c.email,
                users.c.created_at,
                users.c.email_verified,
                users.c.subscription_tier,
                users.c.trial_end_at,
                users.c.last_login_at,
                users.c.digest_opted_in,
            ).order_by(users.c.created_at.desc()).limit(50)
        ).fetchall()

        # ── Referrals ─────────────────────────────────────────────────────
        try:
            ref_total     = conn.execute(select(func.count()).select_from(referrals)).scalar() or 0
            ref_converted = conn.execute(
                select(func.count()).where(referrals.c.status == "converted")
            ).scalar() or 0
            ref_rewarded  = conn.execute(
                select(func.count()).where(referrals.c.status == "rewarded")
            ).scalar() or 0
        except Exception:
            ref_total = ref_converted = ref_rewarded = 0

        # ── Watchlist adoption ────────────────────────────────────────────
        users_with_watchlist = conn.execute(
            select(func.count(func.distinct(watchlist.c.user_id)))
        ).scalar() or 0

    return {
        "total": total,
        "verified": verified,
        "pro": pro_count,
        "trial": trial_count,
        "free": free_count,
        "digest": digest_count,
        "new_today": new_today,
        "new_7d": new_7d,
        "new_30d": new_30d,
        "active_7d": active_7d,
        "active_30d": active_30d,
        "daily_counts": daily_counts,
        "recent": recent,
        "ref_total": ref_total,
        "ref_converted": ref_converted,
        "ref_rewarded": ref_rewarded,
        "users_with_watchlist": users_with_watchlist,
    }


# ── Load data ─────────────────────────────────────────────────────────────────

with st.spinner("Loading metrics..."):
    m = load_metrics()

# ── KPI cards ─────────────────────────────────────────────────────────────────

st.markdown("### 📊 Top-Line KPIs")

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Users", m["total"])
c2.metric("Verified", m["verified"],
          delta=f"{round(m['verified']/m['total']*100)}% of total" if m["total"] else None)
c3.metric("Pro", m["pro"],
          delta=f"{round(m['pro']/m['total']*100)}% of total" if m["total"] else None)
c4.metric("On Trial", m["trial"])
c5.metric("Free", m["free"])
c6.metric("Digest Opt-in", m["digest"])

st.markdown("---")

# ── Acquisition ───────────────────────────────────────────────────────────────

st.markdown("### 🚀 Acquisition")

a1, a2, a3 = st.columns(3)
a1.metric("New Today",    m["new_today"])
a2.metric("New (7 days)", m["new_7d"])
a3.metric("New (30 days)", m["new_30d"])

# ── Engagement ────────────────────────────────────────────────────────────────

st.markdown("### 🔥 Engagement")

e1, e2, e3 = st.columns(3)
e1.metric("Active (7d)",  m["active_7d"],
          delta=f"{round(m['active_7d']/m['total']*100)}% of users" if m["total"] else None)
e2.metric("Active (30d)", m["active_30d"],
          delta=f"{round(m['active_30d']/m['total']*100)}% of users" if m["total"] else None)
e3.metric("Have Watchlist", m["users_with_watchlist"],
          delta=f"{round(m['users_with_watchlist']/m['total']*100)}% of users" if m["total"] else None)

# ── Conversion funnel ─────────────────────────────────────────────────────────

st.markdown("### 🎯 Conversion Funnel")

if m["total"] > 0:
    import plotly.graph_objects as go

    fig = go.Figure(go.Funnel(
        y=["Signed Up", "Email Verified", "Has Watchlist", "Pro Subscriber"],
        x=[m["total"], m["verified"], m["users_with_watchlist"], m["pro"]],
        textinfo="value+percent initial",
        marker={"color": ["#4A9EFF", "#3DD68C", "#F5A623", "#A855F7"]},
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E2E8F0",
        margin={"t": 20, "b": 20, "l": 0, "r": 0},
        height=280,
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No users yet — funnel will appear once signups arrive.")

# ── Daily signups chart ───────────────────────────────────────────────────────

st.markdown("### 📈 Daily Signups (last 30 days)")

if m["daily_counts"]:
    import plotly.graph_objects as go
    from datetime import date

    # Fill in zeros for days with no signups
    today = datetime.now(timezone.utc).date()
    all_days = [(today - timedelta(days=i)).isoformat() for i in range(29, -1, -1)]
    counts   = [m["daily_counts"].get(d, 0) for d in all_days]

    fig2 = go.Figure(go.Bar(
        x=all_days,
        y=counts,
        marker_color="#4A9EFF",
    ))
    fig2.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E2E8F0",
        xaxis={"showgrid": False},
        yaxis={"showgrid": True, "gridcolor": "rgba(255,255,255,0.08)"},
        margin={"t": 10, "b": 40, "l": 40, "r": 10},
        height=240,
    )
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("No signups in the last 30 days.")

# ── Referral stats ────────────────────────────────────────────────────────────

st.markdown("### 🔗 Referral Program")

r1, r2, r3 = st.columns(3)
r1.metric("Total Referrals",  m["ref_total"])
r2.metric("Converted",        m["ref_converted"],
          delta=f"{round(m['ref_converted']/m['ref_total']*100)}%" if m["ref_total"] else None)
r3.metric("Rewarded",         m["ref_rewarded"])

# ── Recent signups table ──────────────────────────────────────────────────────

st.markdown("### 👥 Recent Signups (last 50)")

if m["recent"]:
    import pandas as pd

    rows = []
    for email, created_at, verified, tier, trial_end, last_login, digest in m["recent"]:
        rows.append({
            "Email":       email,
            "Signed Up":   created_at[:16].replace("T", " ") if created_at else "—",
            "Verified":    "✅" if verified else "❌",
            "Tier":        tier or "free",
            "Trial Ends":  trial_end[:10] if trial_end else "—",
            "Last Login":  last_login[:16].replace("T", " ") if last_login else "never",
            "Digest":      "✅" if digest else "—",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No users yet.")

# ── Refresh note ──────────────────────────────────────────────────────────────

st.markdown(
    "<p style='color:#64748B;font-size:0.8rem;text-align:right;margin-top:1rem'>"
    f"Data refreshes every 60 seconds · Last loaded {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
    "</p>",
    unsafe_allow_html=True,
)
