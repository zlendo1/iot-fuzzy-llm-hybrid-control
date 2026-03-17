"""Shared UI components for all pages."""

from __future__ import annotations

import streamlit as st


def render_header(title: str = "IoT Fuzzy-LLM System") -> None:
    """Render the application header with title."""
    st.title(title)
    st.divider()


def render_status_badge(status: str) -> None:
    """Render a colored status indicator badge.

    Args:
        status: Status string, one of 'online', 'offline', 'warning', 'unknown'
    """
    color_map = {
        "online": "green",
        "offline": "red",
        "warning": "orange",
        "unknown": "gray",
    }
    color = color_map.get(status.lower(), "gray")
    st.markdown(
        f'<span style="color:{color}; font-weight:bold;">● {status.upper()}</span>',
        unsafe_allow_html=True,
    )


def render_error_message(error: str) -> None:
    """Display a formatted error message box.

    Args:
        error: Error message to display
    """
    st.error(f"⚠️ {error}")
