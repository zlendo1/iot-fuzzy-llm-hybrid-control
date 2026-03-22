from __future__ import annotations

import streamlit as st

from src.interfaces.web.bridge import get_bridge
from src.interfaces.web.components.common import render_header
from src.interfaces.web.session import init_session_state

LOG_LEVELS = ["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def _filter_entries_by_level(
    entries: list[dict[str, str]], level: str
) -> list[dict[str, str]]:
    """Filter log entries by level."""
    if level == "ALL":
        return entries
    return [entry for entry in entries if entry.get("level") == level]


def _filter_entries_by_search(
    entries: list[dict[str, str]], search_term: str
) -> list[dict[str, str]]:
    """Filter log entries by search term in message."""
    if not search_term:
        return entries
    search_lower = search_term.lower()
    return [
        entry for entry in entries if search_lower in entry.get("message", "").lower()
    ]


def _entries_for_display(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    """Transform log entries for Streamlit display."""
    display_entries: list[dict[str, str]] = []
    for entry in entries:
        display_entries.append(
            {
                "timestamp": entry.get("timestamp", ""),
                "level": entry.get("level", ""),
                "logger": entry.get("logger", ""),
                "message": entry.get("message", ""),
            }
        )
    return display_entries


def render() -> None:
    init_session_state()
    render_header("Logs")

    bridge = get_bridge()

    # Get available log categories from backend
    categories = bridge.get_log_categories()
    if not categories:
        st.info("No log categories available from backend.")
        return

    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox("Log category", categories)
    with col2:
        level = st.selectbox("Minimum level", LOG_LEVELS)

    search_term = st.text_input("Search", "")
    st.button("Refresh")

    # Fetch log entries through bridge (no direct file reads)
    result = bridge.get_log_entries(
        limit=200,
        offset=0,
        level_filter=level if level != "ALL" else "",
        category_filter=category,
    )

    if result is None:
        st.error("Failed to fetch logs from backend.")
        return

    entries = result.get("entries", [])
    pagination = result.get("pagination", {})

    if not entries:
        st.info("No log entries available for this category.")
        return

    # Apply local search filter
    filtered = _filter_entries_by_search(entries, search_term)

    total_count = pagination.get("total", 0)
    st.write(f"Showing {len(filtered)} entries (total: {total_count})")

    if not filtered:
        st.info("No log entries match the search criteria.")
        return

    display_entries = _entries_for_display(filtered)
    st.dataframe(display_entries, width="stretch")


if __name__ == "__main__":
    render()
