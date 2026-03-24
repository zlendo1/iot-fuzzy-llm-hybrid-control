"""Shared UI components for all pages."""

from __future__ import annotations

import streamlit as st

from src.interfaces.web.components.theme import badge_html


def render_header(title: str, subtitle: str = "") -> None:
    """Render the application header with title and optional subtitle."""
    st.title(title)
    if subtitle:
        st.markdown(
            f'<p class="iot-page-subtitle">{subtitle}</p>',
            unsafe_allow_html=True,
        )
    st.divider()


def render_status_badge(status: str) -> None:
    """Render a colored status indicator badge pill.

    Args:
        status: One of 'online', 'offline', 'warning', 'unknown'.
    """
    variant_map = {
        "online": "online",
        "running": "online",
        "offline": "offline",
        "stopped": "offline",
        "warning": "warning",
        "unknown": "unknown",
        "sensor": "info",
        "actuator": "info",
    }
    variant = variant_map.get(status.lower(), "unknown")
    st.markdown(badge_html(status.upper(), variant), unsafe_allow_html=True)


def render_error_message(error: str) -> None:
    """Display a formatted error message box."""
    st.error(f"Error: {error}")
