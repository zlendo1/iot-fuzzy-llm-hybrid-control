from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from src.interfaces.web.bridge import get_bridge
from src.interfaces.web.components.common import render_error_message, render_header
from src.interfaces.web.session import init_session_state

LOG_DIR = Path("logs")
LOG_CATEGORIES = ["system", "commands", "sensors", "errors", "rules"]
LOG_LEVELS = ["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def _load_log_entries(category: str) -> list[dict[str, str]]:
    log_file = LOG_DIR / f"{category}.json"
    entries: list[dict[str, str]] = []
    try:
        for line in log_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(entry, dict):
                entries.append({str(key): str(value) for key, value in entry.items()})
    except FileNotFoundError:
        pass
    return entries


def _filter_entries(
    entries: list[dict[str, str]], level: str, search_term: str
) -> list[dict[str, str]]:
    filtered = entries
    if level != "ALL":
        filtered = [entry for entry in filtered if entry.get("level") == level]
    if search_term:
        search_lower = search_term.lower()
        filtered = [
            entry
            for entry in filtered
            if search_lower in entry.get("message", "").lower()
        ]
    return filtered


def _entries_for_display(entries: list[dict[str, str]]) -> list[dict[str, str]]:
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

    try:
        get_bridge()
    except RuntimeError as exc:
        render_error_message(str(exc))
        return

    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox("Log category", LOG_CATEGORIES)
    with col2:
        level = st.selectbox("Minimum level", LOG_LEVELS)

    search_term = st.text_input("Search", "")
    st.button("Refresh")

    entries = _load_log_entries(category)
    if not entries:
        st.info("No log file found for this category.")
        return

    filtered = _filter_entries(entries, level, search_term)
    st.write(f"Showing {len(filtered)} entries")

    if not filtered:
        st.info("No log entries match the filter.")
        return

    display_entries = _entries_for_display(filtered)
    st.dataframe(display_entries, use_container_width=True)


if __name__ == "__main__":
    render()
