"""
utils/theme.py — Unstructured Alpha Modern Dark Design System
All chart styling flows through style_chart() for consistency.
Robinhood-inspired: dark backgrounds, green/purple gradient accents, glassmorphism cards.
"""
import math as _math

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
TEXT_MUTED     = "#8892AA"   # muted but readable on dark bg (was #8892AA — too dark)
TEXT_CAPTION   = "#6B7FBF"   # subtle caption

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
    _axis = dict(
        showgrid=True,
        gridcolor=GRID_COLOR,
        gridwidth=1,
        # Tick labels — readable on dark plot background (#0F1118)
        tickfont=dict(color=TEXT_SECONDARY, size=10, family="Inter, sans-serif"),
        title_font=dict(color=TEXT_MUTED, size=11, family="Inter, sans-serif"),
        linecolor="rgba(255,255,255,0.08)",
        zeroline=False,
        # Axis line itself
        showline=True,
    )
    fig.update_layout(
        height=height,
        title=dict(
            text=title,
            font=dict(family="Inter, -apple-system, sans-serif", size=13, color=TEXT_PRIMARY),
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
            namelength=-1,
        ),
        legend=dict(
            bgcolor="rgba(18,21,30,0.90)",
            bordercolor="rgba(255,255,255,0.08)",
            borderwidth=1,
            font=dict(size=11, color=TEXT_SECONDARY, family="Inter, sans-serif"),
        ),
        margin=dict(l=8, r=8, t=36 if title else 16, b=8),
        xaxis=dict(
            **_axis,
            showspikes=True,
            spikecolor="rgba(255,255,255,0.15)",
            spikethickness=1,
            spikedash="dot",
        ),
        yaxis=_axis,
    )
    return fig


def style_chart_secondary(fig, height: int = 380,
                           y1_title: str = "Signal",
                           y2_title: str = "Price",
                           y1_color: str = GREEN,
                           y2_color: str = PURPLE) -> object:
    """Style a dual-axis chart (make_subplots secondary_y=True)."""
    _tick = dict(color=TEXT_SECONDARY, size=10, family="Inter, sans-serif")
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
            namelength=-1,
        ),
        legend=dict(
            bgcolor="rgba(18,21,30,0.90)",
            bordercolor="rgba(255,255,255,0.08)",
            borderwidth=1,
            font=dict(size=11, color=TEXT_SECONDARY, family="Inter, sans-serif"),
        ),
        margin=dict(l=8, r=8, t=20, b=8),
        xaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            tickfont=_tick,
            title_font=dict(color=TEXT_MUTED, size=11, family="Inter, sans-serif"),
            linecolor="rgba(255,255,255,0.08)",
            showline=True,
        ),
    )
    fig.update_yaxes(
        title_text=y1_title, secondary_y=False,
        gridcolor=GRID_COLOR,
        tickfont=_tick,
        title_font=dict(color=y1_color, family="Inter, sans-serif", size=11),
        linecolor="rgba(255,255,255,0.08)",
        showline=True,
    )
    fig.update_yaxes(
        title_text=y2_title, secondary_y=True,
        gridcolor="rgba(0,0,0,0)",
        tickfont=_tick,
        title_font=dict(color=y2_color, family="Inter, sans-serif", size=11),
        linecolor="rgba(255,255,255,0.08)",
        showline=True,
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
        "insufficient_data": ("#8892AA", "NO DATA",  "○", "rgba(18,21,30,0.4)",    "rgba(255,255,255,0.08)"),
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
    background: {bg_tint};
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
        <div style="font-size:0.60rem;color:#8892AA;letter-spacing:0.10em;text-transform:uppercase;font-weight:700;">
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
            <div style="font-size:0.60rem;color:#8892AA;margin-top:1px;">/100</div>
        </div>
        <div style="flex:1;padding-bottom:6px;">
            <div style="height:3px;background:rgba(255,255,255,0.05);border-radius:2px;overflow:hidden;margin-bottom:8px;">
                <div style="height:100%;width:{bar_pct}%;background:{color};border-radius:2px;transition:width 0.5s ease;"></div>
            </div>
            <div style="font-size:0.72rem;color:#8892AA;line-height:1.7;">
                <div><span style="color:#8892AA;">Dev</span> &nbsp;<b style="color:#B8C0D4;">{dev:+.1f}%</b> vs 52w avg</div>
                <div><span style="color:#8892AA;">Trend</span> &nbsp;<b style="color:{trend_color};">{trend_arrow} {trend:+.1f}%</b></div>
                <div><span style="color:#8892AA;">Lead</span> &nbsp;<b style="color:#B8C0D4;">~{lag_weeks}w</b></div>
            </div>
        </div>
    </div>
</div>
"""


# ── SVG Radial Gauge ─────────────────────────────────────────────────────────

def confluence_gauge_svg(score: float, case: str = "") -> str:
    """
    Animated semicircular SVG gauge for Confluence Score (0–100).
    Zones: red 0-35 / gray 35-65 / green 65-100.
    Returns HTML string for st.markdown(..., unsafe_allow_html=True).
    """
    CX, CY, R_OUT, R_IN = 100, 80, 62, 45

    score = max(0.0, min(100.0, float(score)))
    sc = ("#00D566" if (score >= 65 or case == "BULL")
          else "#FF4444" if (score <= 35 or case == "BEAR")
          else "#6B7FBF")
    cs = case or ("BULL" if score >= 65 else ("BEAR" if score <= 35 else "NEUTRAL"))

    def _pt(a_deg, r):
        rad = _math.radians(a_deg)
        return CX + r * _math.cos(rad), CY - r * _math.sin(rad)

    def _arc(a1, a2, ro, ri, col, op=1.0):
        x1o, y1o = _pt(a1, ro); x2o, y2o = _pt(a2, ro)
        x1i, y1i = _pt(a1, ri); x2i, y2i = _pt(a2, ri)
        lg = 1 if abs(a1 - a2) > 180 else 0
        d = (f"M{x1o:.2f},{y1o:.2f} A{ro},{ro} 0 {lg},0 {x2o:.2f},{y2o:.2f} "
             f"L{x2i:.2f},{y2i:.2f} A{ri},{ri} 0 {lg},1 {x1i:.2f},{y1i:.2f}Z")
        return f'<path d="{d}" fill="{col}" opacity="{op}"/>'

    needle_ang = 180.0 - score * 1.8

    # Background zone rings
    bg = (_arc(180, 117, R_OUT, R_IN, "#FF4444", 0.22)
        + _arc(117, 63,  R_OUT, R_IN, "#8892AA", 0.14)
        + _arc(63,  0,   R_OUT, R_IN, "#00D566", 0.22))

    # Active fill up to needle
    fill = _arc(180, needle_ang, R_OUT, R_IN, sc, 0.88) if score > 0.5 else ""

    # Zone separator ticks
    def _tick(a):
        x1, y1 = _pt(a, R_IN - 1); x2, y2 = _pt(a, R_OUT + 1)
        return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="#0B0D12" stroke-width="2.5"/>')
    ticks = _tick(117) + _tick(63)

    # Animated needle: sweeps from left (score=0) to final position
    nx1, ny1 = _pt(needle_ang, R_IN + 2)
    nx2, ny2 = _pt(needle_ang, R_OUT - 1)
    rotation_start = score * 1.8
    needle = (
        f'<line x1="{nx1:.1f}" y1="{ny1:.1f}" x2="{nx2:.1f}" y2="{ny2:.1f}" '
        f'stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round">'
        f'<animateTransform attributeName="transform" type="rotate" '
        f'from="{rotation_start:.1f},{CX},{CY}" to="0,{CX},{CY}" '
        f'dur="1.0s" fill="freeze" calcMode="spline" '
        f'keyTimes="0;1" keySplines="0.25,0.46,0.45,0.94"/>'
        f'</line>'
    )

    # Center cap
    cap = (f'<circle cx="{CX}" cy="{CY}" r="6" fill="#0B0D12"/>'
           f'<circle cx="{CX}" cy="{CY}" r="3.5" fill="#E8EEFF"/>')

    # Score text inside the arc
    score_txt = (f'<text x="{CX}" y="{CY + 20}" text-anchor="middle" '
                 f'font-family="Inter,sans-serif" font-size="28" font-weight="900" '
                 f'fill="{sc}">{score:.0f}</text>')
    case_lbl  = (f'<text x="{CX}" y="{CY + 33}" text-anchor="middle" '
                 f'font-family="Inter,sans-serif" font-size="8" font-weight="700" '
                 f'letter-spacing="2" fill="{sc}">{cs}</text>')

    # Axis labels
    def _lbl(a, text):
        lx, ly = _pt(a, R_OUT + 10)
        return (f'<text x="{lx:.0f}" y="{ly + 4:.0f}" text-anchor="middle" '
                f'font-family="Inter,sans-serif" font-size="8" fill="#6B7FBF">{text}</text>')
    labels = _lbl(180, "0") + _lbl(90, "50") + _lbl(0, "100")

    header = (f'<text x="{CX}" y="10" text-anchor="middle" '
              f'font-family="Inter,sans-serif" font-size="7" font-weight="700" '
              f'letter-spacing="2.5" fill="#6B7FBF">CONFLUENCE</text>')

    return (
        '<div style="display:flex;justify-content:center;align-items:center;'
        'padding:4px 0;animation:fadeIn 0.5s ease-out;">'
        '<svg width="196" height="120" viewBox="0 0 196 120" '
        'xmlns="http://www.w3.org/2000/svg">'
        f'{bg}{fill}{ticks}{needle}{cap}{header}{score_txt}{case_lbl}{labels}'
        '</svg></div>\n'
        '<style>@keyframes fadeIn{from{opacity:0;transform:scale(0.95)}'
        'to{opacity:1;transform:scale(1)}}</style>'
    )


# ── Gradient Area Chart Helper ────────────────────────────────────────────────

def style_area_chart(fig, line_color: str = GREEN, fill_opacity: float = 0.12,
                     height: int = 350, title: str = "") -> object:
    """
    Apply dark theme to a Plotly figure AND add semi-transparent gradient area
    fill under the first trace. Call after building your go.Scatter traces.

    The fill uses tozeroy with a matching rgba color so the area recedes from
    the line — giving a Robinhood / Bloomberg Terminal look.

    Usage:
        fig = go.Figure([go.Scatter(x=dates, y=values, name="Price",
                                    line=dict(color="#00D566", width=2))])
        fig = style_area_chart(fig, line_color="#00D566")
        st.plotly_chart(fig, use_container_width=True)
    """
    import re
    # Parse hex color to rgba fill
    hex_c = line_color.lstrip("#")
    if len(hex_c) == 6:
        r_, g_, b_ = int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)
        fill_color = f"rgba({r_},{g_},{b_},{fill_opacity})"
    else:
        fill_color = f"rgba(0,213,102,{fill_opacity})"

    # Inject fill on the first trace
    if fig.data:
        fig.data[0].update(
            fill="tozeroy",
            fillcolor=fill_color,
            line=dict(color=line_color, width=2),
        )

    return style_chart(fig, height=height, title=title)


# ── Skeleton / Shimmer Loading System ────────────────────────────────────────
# Usage pattern (in any page):
#
#   from utils.theme import inject_skeleton_css, skeleton_cards, skeleton_chart_block
#
#   inject_skeleton_css()       # once per page, injects global CSS
#
#   # Show skeleton while data loads
#   ph = st.empty()
#   ph.markdown(skeleton_cards(n=3, height=110), unsafe_allow_html=True)
#   data = expensive_load()
#   ph.empty()                  # replace with real content
#
# All skeleton elements use the `.ua-sk` class so they won't conflict with
# any Streamlit or external CSS already on the page.

_SKELETON_CSS = """
<style>
@keyframes ua_shimmer {
  0%   { background-position: -1200px 0; }
  100% { background-position:  1200px 0; }
}
.ua-sk {
  background: linear-gradient(
    90deg,
    rgba(26,30,44,0.9)   0%,
    rgba(42,48,72,0.95)  35%,
    rgba(55,62,90,0.90)  50%,
    rgba(42,48,72,0.95)  65%,
    rgba(26,30,44,0.9)  100%
  );
  background-size: 1200px 100%;
  animation: ua_shimmer 1.8s infinite linear;
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.05);
}
.ua-sk-line {
  background: linear-gradient(
    90deg,
    rgba(26,30,44,0.9)  0%,
    rgba(42,48,72,0.95) 40%,
    rgba(26,30,44,0.9) 100%
  );
  background-size: 1200px 100%;
  animation: ua_shimmer 1.8s infinite linear;
  border-radius: 4px;
  height: 11px;
  margin-bottom: 8px;
}
.ua-sk-wrap {
  background: rgba(18,21,30,0.8);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px;
  padding: 16px 18px;
  margin-bottom: 10px;
}
</style>
"""


def inject_skeleton_css() -> None:
    """
    Inject the skeleton/shimmer CSS into the page. Call once near the top of
    any page that uses skeleton placeholders. Safe to call multiple times —
    Streamlit deduplicates identical markdown injections within a session.
    """
    import streamlit as st
    st.markdown(_SKELETON_CSS, unsafe_allow_html=True)


def skeleton_cards(n: int = 3, height: int = 110, cols: int = 1) -> str:
    """
    Return HTML for `n` stacked shimmer card placeholders.
    Use `cols` to lay them out in a CSS grid (1–4 columns).

    Args:
        n:      number of skeleton cards
        height: card height in pixels
        cols:   number of grid columns
    """
    card = (
        f'<div class="ua-sk-wrap">'
        f'  <div class="ua-sk" style="height:{height}px;width:100%;"></div>'
        f'</div>'
    )
    grid_css = f"display:grid;grid-template-columns:repeat({cols},1fr);gap:10px;"
    return f'<div style="{grid_css}">{"".join([card] * n)}</div>'


def skeleton_chart_block(height: int = 300, title_lines: int = 1) -> str:
    """
    Return HTML for a shimmer chart placeholder (full-width).

    Args:
        height:      chart area height in pixels
        title_lines: number of fake title/label lines above the chart area
    """
    lines_html = "".join(
        f'<div class="ua-sk-line" style="width:{w}%;margin-bottom:6px;"></div>'
        for w in ([40] + [25] * (title_lines - 1))[:title_lines]
    )
    return (
        f'<div class="ua-sk-wrap">'
        f'  {lines_html}'
        f'  <div class="ua-sk" style="height:{height}px;width:100%;margin-top:8px;"></div>'
        f'</div>'
    )


def skeleton_stat_row(n: int = 4) -> str:
    """
    Return HTML for a row of `n` small stat-box skeletons (metric cards).
    Typically used to placeholder a row of KPI chips above a chart.
    """
    card = (
        '<div class="ua-sk-wrap" style="flex:1;min-width:0;">'
        '  <div class="ua-sk-line" style="width:60%;"></div>'
        '  <div class="ua-sk" style="height:36px;width:80%;margin-top:4px;"></div>'
        '</div>'
    )
    return (
        f'<div style="display:flex;gap:10px;margin-bottom:10px;">'
        f'{"".join([card] * n)}'
        f'</div>'
    )
