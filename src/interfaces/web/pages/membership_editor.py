"""Membership Editor page - Edit fuzzy membership functions."""

from __future__ import annotations

import json

import streamlit as st

from src.interfaces.web.bridge import get_bridge
from src.interfaces.web.components.common import render_header
from src.interfaces.web.session import init_session_state


def _render_membership_editor() -> None:
    init_session_state()
    render_header("Membership Editor")

    bridge = get_bridge()

    sensor_types = bridge.list_sensor_types()
    if not sensor_types:
        st.warning("No sensor types available. Backend may be unavailable.")
        return

    sensor_type = st.selectbox("Sensor type", sensor_types)

    mf_data = bridge.get_membership_functions(sensor_type)
    if mf_data is None:
        st.warning("Failed to load membership functions. Backend may be unavailable.")
        return

    if mf_data:
        st.json(mf_data)
        default_text = json.dumps(mf_data, indent=2)
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

        linguistic_vars = parsed.get("linguistic_variables", [])
        if not isinstance(linguistic_vars, list):
            st.error("Invalid structure: must contain 'linguistic_variables' array")
            return

        success = True
        for var in linguistic_vars:
            if not isinstance(var, dict):
                st.error("Invalid structure: linguistic_variables must contain objects")
                return
            var_name = var.get("name")
            mfs = var.get("membership_functions", [])
            if not isinstance(mfs, list):
                st.error(
                    f"Invalid structure: {var_name}.membership_functions must be array"
                )
                return

            for mf in mfs:
                if not isinstance(mf, dict):
                    st.error(
                        "Invalid structure: membership_functions must contain objects"
                    )
                    return
                mf_name = mf.get("name")
                func_type = mf.get("function_type")
                params = mf.get("parameters", {})

                if not isinstance(params, dict):
                    st.error(f"Invalid parameters for {mf_name}: must be object")
                    return

                float_params: dict[str, float] = {}
                try:
                    for k, v in params.items():
                        float_params[k] = float(v)
                except (ValueError, TypeError):
                    st.error(
                        f"Invalid parameters for {mf_name}: values must be numbers"
                    )
                    return

                result = bridge.update_membership_function(
                    sensor_type, var_name, mf_name, func_type, float_params
                )
                if result is None:
                    st.error(f"Failed to save {mf_name}. Backend may be unavailable.")
                    success = False
                    break

            if not success:
                break

        if success:
            st.success("Saved.")


def render() -> None:
    _render_membership_editor()


if __name__ == "__main__":
    render()
