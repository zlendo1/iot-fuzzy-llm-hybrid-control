"""Membership Editor page - Edit fuzzy membership functions."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from src.interfaces.web.components.common import render_header
from src.interfaces.web.session import init_session_state

SENSOR_TYPES = ["temperature", "humidity", "light_level", "motion"]
MEMBERSHIP_DIR = Path("config/membership_functions")


def _load_membership_data(sensor_type: str) -> dict[str, object] | None:
    file_path = MEMBERSHIP_DIR / f"{sensor_type}.json"
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        st.warning("Membership file not found.")
        return None
    except json.JSONDecodeError as exc:
        st.error(f"Invalid JSON in membership file: {exc}")
        return None
    except OSError as exc:
        st.error(f"Failed to read membership file: {exc}")
        return None


def _save_membership_data(sensor_type: str, payload: dict[str, object]) -> None:
    file_path = MEMBERSHIP_DIR / f"{sensor_type}.json"
    try:
        file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        st.success("Saved.")
    except OSError as exc:
        st.error(f"Failed to save membership file: {exc}")


def render() -> None:
    init_session_state()
    render_header("Membership Editor")

    sensor_type = st.selectbox("Sensor type", SENSOR_TYPES)

    data = _load_membership_data(sensor_type)
    if data is not None:
        st.json(data)
        default_text = json.dumps(data, indent=2)
    else:
        default_text = "{}"

    edited_text = st.text_area(
        "Edit JSON",
        value=default_text,
        height=400,
    )

    if st.button("Save"):
        try:
            parsed = json.loads(edited_text)
        except json.JSONDecodeError as exc:
            st.error(f"Invalid JSON: {exc}")
            return
        if not isinstance(parsed, dict):
            st.error("Invalid JSON: root must be an object.")
            return
        _save_membership_data(sensor_type, parsed)


if __name__ == "__main__":
    render()
