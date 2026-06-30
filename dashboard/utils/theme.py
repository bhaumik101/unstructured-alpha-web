"""
utils/theme.py — Unstructured Alpha Modern Dark Design System
All chart styling flows through style_chart() for consistency.
Robinhood-inspired: dark backgrounds, green/purple gradient accents, glassmorphism cards.
"""

# ── Palette ───────────────────────────────────────────────────────────────────

# Backgrounds
BG_PAGE         = "#0B0D12"   # near-black page background
BG_CARD         = "#12151E"   # card surface
BG_CARD_RAISED  = "#1A1E2C"   # hover / elevated card
BG_PLOT         = "#0F1118"   # chart plot area
BG_SIDEBAR      = "#0D0F1A"   # sidebar

# Typography
TEXT_PRIMARY   = "#E8EEFF"   # cool near-white
TEXT_SECONDARY = "#8892AA"   # muted blue-gray
TEXT_MUTED     = "#434E6A"   # very muted
TEXT_CAPTION   = "#2E3650"   # barely visible label

# Brand accents
GREEN       = "#00D566"   # primary green (Robinhood-style)
GREEN_DARK  = "#00A847"   # darker green variant
GREEN_DIM   = "#001A0D"   # dimmed green for backgrounds
PURPLE      = "#7C3AED"   # violet accent
PURPLE_DIM  = "#1A0A3D"   # dimmed purple
CYAN        = "#00C8E0"   # secondary accent
AMBER       = "#F59E0B"   # warning/watch amber

# Signal status
BULL_GREEN  = "#00D566"   # bullish green
BEAR_RED    = "#FF4444"   # bearish red
BEAR_DIM    = "#4D0000"   # dimmed red
NEUTRAL     = "#6B7FBF"   # neutral blue-gray

# Chart grid & borders
GRID_COLOR   = "rgba(255,255,255,0.04)"
BORDER_LIGHT = "rgba(255,255,255,0.07)"
DIVIDER      = "rgba(255,255,255,0.05)"

# Data series — vibrant on dark
SERIES_COLORS = [
    "#00D566",   # green (primary)
    "#7C3AED",   # purple
    "#00C8E0",   # cyan
    "#FF4444",   # red
    "#F59E0B",   # amber
    "#06B6D4",   # sky
    "#EC4899",   # pink
    "#34D399",   # emerald
]

# Heatmap colorscale (bear → neutral → bull) — dark-friendly
HEATMAP_COLORSCALE = [
    [0.00, "#3D0000"],
    [0.25, "#FF4444"],
    [0.45, "#1A1E2C"],
    [0.50, "#20243A"],
    [0.55, "#0A2018"],
    [0.75, "#00D566"],
    [1.00, "#003D1A"],
]

# ── Chart Style Helper ────────────────────────────────────────────────────────

def style_chart(fig, height: int = 350, title: str = "") -> object:
    """
    Apply the Unstructured Alpha dark theme to any Plotly figure.

    Usage:
        fig = go.Figure(...)
        fig = style_chart(fig, height=400, title="Signal vs. Price")
        st.plotly_chart(fig, use_container_width=True)
    """
    fig.update_layout(
        height=height,
        title=dict(
            text=title,
            font=dict(family="Inter, -apple-system, sans-serif", size=13, color=TEXT_SECONDARY),
            x=0,
            xanchor="left",
        ) if title else None,
        paper_bgcolor=BG_PAGE,
        plot_bgcolor=BG_PLOT,
        font=dict(family="Inter, -apple-system, sans-serif", color=TEXT_SECONDARY),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=BG_CARD_RAISED,
            bordercolor=BORDER_LIGHT,
            font=dict(family="Inter, sans-serif", size=12, color=TEXT_PRIMARY),
        ),
        legend=dict(
            bgcolor="rgba(18,21,30,0.85)",
            bordercolor=BORDER_LIGHT,
            borderwidth=1,
            font=dict(size=11, color=TEXT_SECONDARY, family="Inter, sans-serif"),
        ),
        margin=dict(l=0, r=0, t=32 if title else 12, b=0),
        xaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            gridwidth=1,
            tickfont=dict(color=TEXT_MUTED, size=10, family="Inter, sans-serif"),
            linecolor=DIVIDER,
            zeroline=False,
            showspikes=True,
            spikecolor=BORDER_LIGHT,
            spikethickness=1,
            spikedash="dot",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            gridwidth=1,
            tickfont=dict(color=TEXT_MUTED, size=10, family="Inter, sans-serif"),
            linecolor=DIVIDER,
            zeroline=False,
        ),
    )
    return fig


def style_chart_secondary(fig, height: int = 380,
                           y1_title: str = "Signal",
                           y2_title: str = "Price",
                           y1_color: str = GREEN,
                           y2_color: str = PURPLE) -> object:
    """Style a dual-axis chart (make_subplots secondary_y=True)."""
    fig.update_layout(
        height=height,
        paper_bgcolor=BG_PAGE,
        plot_bgcolor=BG_PLOT,
        font=dict(family="Inter, -apple-system, sans-serif", color=TEXT_SECONDARY),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=BG_CARD_RAISED,
            bordercolor=BORDER_LIGHT,
            font=dict(family="Inter, sans-serif", size=12, color=TEXT_PRIMARY),
        ),
        legend=dict(
            bgcolor="rgba(18,21,30,0.85)",
            bordercolor=BORDER_LIGHT,
            borderwidth=1,
            font=dict(size=11, color=TEXT_SECONDARY, family="Inter, sans-serif"),
        ),
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            tickfont=dict(color=TEXT_MUTED, size=10, family="Inter, sans-serif"),
        ),
    )
    fig.update_yaxes(
        title_text=y1_title, secondary_y=False,
        gridcolor=GRID_COLOR,
        tickfont=dict(color=TEXT_MUTED, size=10, family="Inter, sans-serif"),
        title_font=dict(color=y1_color, family="Inter, sans-serif", size=11),
    )
    fig.update_yaxes(
        title_text=y2_title, secondary_y=True,
        gridcolor="rgba(0,0,0,0)",
        tickfont=dict(color=TEXT_MUTED, size=10, family="Inter, sans-serif"),
        title_font=dict(color=y2_color, family="Inter, sans-serif", size=11),
    )
    return fig


# ── HTML Card Templates ───────────────────────────────────────────────────────

def signal_card_html(
    icon: str,
    cat_name: str,
    pcs: int,
    name: str,
    status: str,
    score: float,
    dev: float,
    trend: float,
    lag_weeks: int,
) -> str:
    """Return an HTML card for a signal status widget — modern dark glassmorphism design."""
    STATUS_MAP = {
        "bullish":           ("#00D566", "BULLISH",  "▲", "rgba(0,213,102,0.07)",  "rgba(0,213,102,0.25)"),
        "bearish":           ("#FF4444", "BEARISH",  "▼", "rgba(255,68,68,0.07)",  "rgba(255,68,68,0.25)"),
        "neutral":           ("#6B7FBF", "NEUTRAL",  "●", "rgba(107,127,191,0.05)", "rgba(107,127,191,0.20)"),
        "insufficient_data": ("#434E6A", "NO DATA",  "○", "rgba(18,21,30,0.4)",    "rgba(255,255,255,0.08)"),
    }
    color, label, arrow, bg_tint, border_color = STATUS_MAP.get(
        status, STATUS_MAP["neutral"]
    )

    trend_arrow = "↑" if trend > 1 else ("↓" if trend < -1 else "→")
    trend_color = "#00D566" if trend > 1 else ("#FF4444" if trend < -1 else "#6B7FBF")

    # Score bar fill %
    bar_pct = min(max(score, 0), 100)

    return f"""
<div style="
    background:{bg_tint};
    border:1px solid {border_color};
    border-radius:12px;
    padding:14px 16px;
    margin-bottom:10px;
    font-family:'Inter',-apple-system,sans-serif;
    backdrop-filter:blur(8px);
    transition:all 0.2s cubic-bezier(0.4,0,0.2,1);
    position:relative;
    overflow:hidden;
">
    <div style="position:absolute;left:0;top:0;bottom:0;width:3px;background:{color};border-radius:12px 0 0 12px;"></div>
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
        <div style="font-size:0.60rem;color:#434E6A;letter-spacing:0.10em;text-transform:uppercase;font-weight:700;">
            {icon} {cat_name} &nbsp;·&nbsp; PCS {pcs}/10
        </div>
        <div style="
            font-size:0.60rem;font-weight:700;letter-spacing:0.08em;
            color:{color};background:{'rgba(0,213,102,0.1)' if status=='bullish' else ('rgba(255,68,68,0.1)' if status=='bearish' else 'rgba(107,127,191,0.1)')};
            padding:2px 7px;border-radius:4px;
        ">{arrow} {label}</div>
    </div>
    <div style="font-weight:600;font-size:0.88rem;color:#E8EEFF;margin-bottom:10px;line-height:1.35;letter-spacing:-0.1px;">
        {name[:52]}
    </div>
    <div style="display:flex;align-items:flex-end;justify-content:space-between;gap:12px;">
        <div>
            <div style="font-size:2.2rem;font-weight:800;color:{color};letter-spacing:-1.5px;line-height:1.0;">
                {score:.0f}
            </div>
            <div style="font-size:0.60rem;color:#434E6A;margin-top:1px;">/100</div>
        </div>
        <div style="flex:1;padding-bottom:6px;">
            <div style="height:3px;background:rgba(255,255,255,0.05);border-radius:2px;overflow:hidden;margin-bottom:8px;">
                <div style="height:100%;width:{bar_pct}%;background:{color};border-radius:2px;transition:width 0.5s ease;"></div>
            </div>
            <div style="font-size:0.72rem;color:#8892AA;line-height:1.7;">
                <div><span style="color:#434E6A;">Dev</span> &nbsp;<b style="color:#B8C0D4;">{dev:+.1f}%</b> vs 52w avg</div>
                <div><span style="color:#434E6A;">Trend</span> &nbsp;<b style="color:{trend_color};">{trend_arrow} {trend:+.1f}%</b></div>
                <div><span style="color:#434E6A;">Lead</span> &nbsp;<b style="color:#B8C0D4;">~{lag_weeks}w</b></div>
            </div>
        </div>
    </div>
</div>
"""
