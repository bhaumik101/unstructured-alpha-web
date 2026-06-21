"""
utils/theme.py — Unstructured Alpha WSJ/Bloomberg Color System
All chart styling flows through style_chart() for consistency.
"""

# ── Palette ───────────────────────────────────────────────────────────────────

# Backgrounds
BG_PAGE    = "#FAF7F0"   # warm cream page
BG_CARD    = "#F0EBE1"   # slightly darker cream for cards
BG_PLOT    = "#FFFFFF"   # pure white chart area
BG_SIDEBAR = "#1C2B4A"   # deep navy sidebar

# Typography
TEXT_PRIMARY   = "#1A1612"  # near-black warm
TEXT_SECONDARY = "#6B6560"  # warm gray
TEXT_SIDEBAR   = "#F0EBE1"  # cream on navy
TEXT_CAPTION   = "#9E9E8E"  # muted warm gray

# Brand accent
GOLD        = "#B8860B"   # dark goldenrod — primary
GOLD_LIGHT  = "#C9A84C"   # lighter gold for hover/accents
NAVY        = "#1C2B4A"   # deep navy
TEAL        = "#0D4F5C"   # deep teal accent

# Signal status
BULL_GREEN  = "#1B5E20"   # dark forest green (bullish)
BEAR_RED    = "#7B1010"   # dark burgundy (bearish)
NEUTRAL_TAN = "#8B7355"   # warm brown (neutral)

# Chart grid & borders
GRID_COLOR  = "#E8E0CE"   # warm beige grid lines
BORDER_LIGHT = "#D4C9B0"  # card borders
DIVIDER     = "#D4C9B0"   # section dividers

# Data series colors (WSJ palette — works on white backgrounds)
SERIES_COLORS = [
    "#1C2B4A",  # navy
    "#B8860B",  # gold
    "#1B5E20",  # forest green
    "#7B1010",  # burgundy
    "#5D4037",  # warm brown
    "#0D4F5C",  # teal
    "#4A1B6B",  # deep purple
    "#B34700",  # burnt orange
]

# COT / categorical colors
COT_SPEC  = "#1C2B4A"   # navy for speculators
COT_COMM  = "#B8860B"   # gold for commercials

# Heatmap colorscale (bear → neutral → bull)
HEATMAP_COLORSCALE = [
    [0.00, "#5C0A0A"],   # deep burgundy
    [0.25, "#7B1010"],   # bear red
    [0.40, "#C8AD7F"],   # warm tan (neutral-bear)
    [0.50, "#E8D5A3"],   # neutral cream
    [0.60, "#A8C09A"],   # neutral-bull green
    [0.75, "#4A8C3F"],   # mid green
    [1.00, "#0F3D0F"],   # deep forest green
]

# ── Chart Style Helper ────────────────────────────────────────────────────────

def style_chart(fig, height: int = 350, title: str = "") -> object:
    """
    Apply the WSJ/Bloomberg light theme to any Plotly figure.

    Usage:
        fig = go.Figure(...)
        fig = style_chart(fig, height=400, title="Signal vs. Price")
        st.plotly_chart(fig, use_container_width=True)
    """
    fig.update_layout(
        height=height,
        title=dict(
            text=title,
            font=dict(family="Georgia, serif", size=14, color=TEXT_PRIMARY),
            x=0,
            xanchor="left",
        ) if title else None,
        paper_bgcolor=BG_PAGE,
        plot_bgcolor=BG_PLOT,
        font=dict(family="Georgia, serif", color=TEXT_PRIMARY),
        hovermode="x unified",
        legend=dict(
            bgcolor="rgba(250,247,240,0.92)",
            bordercolor=BORDER_LIGHT,
            borderwidth=1,
            font=dict(size=11, color=TEXT_PRIMARY),
        ),
        margin=dict(l=0, r=0, t=30 if title else 10, b=0),
        xaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            gridwidth=1,
            tickfont=dict(color=TEXT_SECONDARY, size=10),
            linecolor=BORDER_LIGHT,
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            gridwidth=1,
            tickfont=dict(color=TEXT_SECONDARY, size=10),
            linecolor=BORDER_LIGHT,
            zeroline=False,
        ),
    )
    return fig


def style_chart_secondary(fig, height: int = 380,
                           y1_title: str = "Signal",
                           y2_title: str = "Price",
                           y1_color: str = NAVY,
                           y2_color: str = GOLD) -> object:
    """Style a dual-axis chart (make_subplots secondary_y=True)."""
    fig.update_layout(
        height=height,
        paper_bgcolor=BG_PAGE,
        plot_bgcolor=BG_PLOT,
        font=dict(family="Georgia, serif", color=TEXT_PRIMARY),
        hovermode="x unified",
        legend=dict(
            bgcolor="rgba(250,247,240,0.92)",
            bordercolor=BORDER_LIGHT,
            borderwidth=1,
            font=dict(size=11, color=TEXT_PRIMARY),
        ),
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            tickfont=dict(color=TEXT_SECONDARY, size=10),
        ),
    )
    fig.update_yaxes(
        title_text=y1_title, secondary_y=False,
        gridcolor=GRID_COLOR,
        tickfont=dict(color=TEXT_SECONDARY, size=10),
        title_font=dict(color=y1_color),
    )
    fig.update_yaxes(
        title_text=y2_title, secondary_y=True,
        gridcolor="rgba(0,0,0,0)",
        tickfont=dict(color=TEXT_SECONDARY, size=10),
        title_font=dict(color=y2_color),
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
    """Return an HTML card for a signal status widget."""
    status_color = {
        "bullish": BULL_GREEN,
        "bearish": BEAR_RED,
        "neutral": NEUTRAL_TAN,
        "insufficient_data": "#9E9E9E",
    }.get(status, NEUTRAL_TAN)

    status_emoji = {
        "bullish": "▲",
        "bearish": "▼",
        "neutral": "●",
        "insufficient_data": "○",
    }.get(status, "●")

    trend_arrow = "↑" if trend > 1 else ("↓" if trend < -1 else "→")

    return f"""
    <div style="
        background:{BG_CARD};
        border-radius:8px;
        padding:14px 16px;
        border-left:4px solid {status_color};
        border-top:1px solid {BORDER_LIGHT};
        border-right:1px solid {BORDER_LIGHT};
        border-bottom:1px solid {BORDER_LIGHT};
        margin-bottom:10px;
        min-height:130px;
        font-family:Georgia,serif;
    ">
        <div style="font-size:0.72rem;color:{TEXT_CAPTION};margin-bottom:4px;letter-spacing:0.03em;">
            {icon} {cat_name.upper()} · PCS {pcs}/10
        </div>
        <div style="font-weight:700;font-size:0.92rem;color:{TEXT_PRIMARY};margin-bottom:8px;line-height:1.3;">
            {name[:48]}
        </div>
        <div style="display:flex;align-items:center;gap:16px;">
            <div>
                <div style="font-size:1.5rem;font-weight:700;color:{status_color};">
                    {status_emoji} {score:.0f}
                </div>
                <div style="font-size:0.70rem;color:{TEXT_CAPTION};">/100</div>
            </div>
            <div style="font-size:0.80rem;color:{TEXT_SECONDARY};line-height:1.6;">
                <div><b>Dev:</b> {dev:+.1f}% vs 52w avg</div>
                <div><b>Trend:</b> {trend_arrow} {trend:+.1f}%</div>
                <div><b>Lead:</b> ~{lag_weeks}w</div>
            </div>
        </div>
    </div>
    """
