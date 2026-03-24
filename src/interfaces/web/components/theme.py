"""Global CSS theme and styling utilities for the Streamlit web interface."""

from __future__ import annotations

from string import Template

import streamlit as st

COLORS = {
    "primary": "#667eea",
    "primary_light": "#7c93ed",
    "success": "#48bb78",
    "success_bg": "rgba(72,187,120,0.12)",
    "warning": "#ed8936",
    "warning_bg": "rgba(237,137,54,0.12)",
    "danger": "#fc8181",
    "danger_bg": "rgba(252,129,129,0.12)",
    "info": "#63b3ed",
    "info_bg": "rgba(99,179,237,0.12)",
    "muted": "#a0aec0",
    "border": "rgba(172, 177, 195, 0.15)",
    "card_bg": "rgba(172, 177, 195, 0.15)",
    "card_shadow": "rgba(0,0,0,0.04)",
}

_GLOBAL_CSS = Template("""
<style>
/* ── Metric cards ──────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: $card_bg;
    border: 1px solid $border;
    border-radius: 10px;
    padding: 16px 20px;
    box-shadow: 0 1px 3px $card_shadow;
    transition: box-shadow 0.2s ease;
}
[data-testid="stMetric"]:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
[data-testid="stMetricLabel"] {
    font-size: 0.82rem !important;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: $muted !important;
}
[data-testid="stMetricValue"] {
    font-weight: 700 !important;
}

/* ── Expanders ─────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid $border;
    border-radius: 10px;
    margin-bottom: 8px;
    overflow: hidden;
}

/* ── Tabs ──────────────────────────────────────────────────────── */
button[data-baseweb="tab"] {
    font-weight: 600 !important;
    letter-spacing: 0.02em;
}

/* ── Status badge pills ────────────────────────────────────────── */
.iot-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}
.iot-badge-online  { background: $success_bg; color: $success; }
.iot-badge-offline { background: $danger_bg;  color: $danger;  }
.iot-badge-warning { background: $warning_bg; color: $warning; }
.iot-badge-unknown { background: rgba(160,174,192,0.12); color: $muted; }
.iot-badge-info    { background: $info_bg;    color: $info;    }

/* ── Page header ───────────────────────────────────────────────── */
.iot-page-header {
    margin-bottom: 4px;
}
.iot-page-subtitle {
    color: $muted;
    font-size: 0.95rem;
    margin-top: -8px;
    margin-bottom: 16px;
}

/* ── Info cards ─────────────────────────────────────────────────── */
.iot-card {
    background: $card_bg;
    border: 1px solid $border;
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 12px;
    box-shadow: 0 1px 3px $card_shadow;
}
.iot-card-header {
    font-weight: 700;
    font-size: 1rem;
    margin-bottom: 8px;
}
.iot-card-muted {
    color: $muted;
    font-size: 0.85rem;
}

/* ── Dividers ──────────────────────────────────────────────────── */
hr {
    border: none;
    border-top: 1px solid $border;
    margin: 20px 0;
}

/* ── Log-level colors ──────────────────────────────────────────── */
.log-debug    { color: $muted; }
.log-info     { color: $info; }
.log-warning  { color: $warning; }
.log-error    { color: $danger; }
.log-critical { color: $danger; font-weight: 700; }

/* ── Sensor card grid ──────────────────────────────────────────── */
.sensor-value {
    font-size: 1.6rem;
    font-weight: 700;
    line-height: 1.2;
}
.sensor-unit {
    color: $muted;
    font-size: 0.9rem;
    margin-left: 4px;
}
</style>
""").safe_substitute(COLORS)


def inject_global_css() -> None:
    """Inject the global CSS theme into the current page.

    Call this once at the top of ``streamlit_app.main()`` so every page
    inherits the shared visual style.
    """
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)


def badge_html(label: str, variant: str = "info") -> str:
    """Return an HTML snippet for a styled status badge.

    Args:
        label: Text displayed inside the badge.
        variant: One of ``online``, ``offline``, ``warning``,
            ``unknown``, ``info``.
    """
    dot = "&#9679;"  # ●
    css_class = f"iot-badge iot-badge-{variant}"
    return f'<span class="{css_class}">{dot} {label}</span>'


def card_html(header: str, body: str, muted: str = "") -> str:
    """Return an HTML snippet for a styled info card.

    Args:
        header: Bold card title.
        body: Main body HTML.
        muted: Optional muted subtext.
    """
    muted_block = f'<div class="iot-card-muted">{muted}</div>' if muted else ""
    return (
        f'<div class="iot-card">'
        f'<div class="iot-card-header">{header}</div>'
        f"{body}{muted_block}</div>"
    )
