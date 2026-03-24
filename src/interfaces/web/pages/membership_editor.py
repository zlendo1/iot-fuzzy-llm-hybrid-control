"""Membership page - Visualize and edit fuzzy membership functions."""

from __future__ import annotations

import json
import math
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

from src.interfaces.web.bridge import get_bridge
from src.interfaces.web.components.common import render_header
from src.interfaces.web.session import init_session_state


def _calculate_mf(x: float, func_type: str, params: dict[str, float]) -> float:
    """Fuzzy MF calculation: triangular(a,b,c), trapezoidal(a,b,c,d), gaussian(mean,sigma), sigmoid(a,b)."""
    if func_type == "triangular":
        a = params.get("a", 0.0)
        b = params.get("b", 0.0)
        c = params.get("c", 0.0)
        if x <= a or x >= c:
            return 0.0
        elif a < x <= b:
            return (x - a) / (b - a) if b != a else 1.0
        elif b < x < c:
            return (c - x) / (c - b) if c != b else 1.0
        return 0.0
    elif func_type == "trapezoidal":
        a = params.get("a", 0.0)
        b = params.get("b", 0.0)
        c = params.get("c", 0.0)
        d = params.get("d", 0.0)
        if x <= a or x >= d:
            return 0.0
        elif a < x <= b:
            return (x - a) / (b - a) if b != a else 1.0
        elif b < x <= c:
            return 1.0
        elif c < x < d:
            return (d - x) / (d - c) if d != c else 1.0
        return 0.0
    elif func_type == "gaussian":
        mean = params.get("mean", 0.0)
        sigma = params.get("sigma", 1.0)
        if sigma == 0:
            return 1.0 if x == mean else 0.0
        try:
            return math.exp(-0.5 * ((x - mean) / sigma) ** 2)
        except OverflowError:
            return 0.0
    elif func_type == "sigmoid":
        a = params.get("a", 1.0)
        b = params.get("b", 0.0)
        try:
            return 1.0 / (1.0 + math.exp(-a * (x - b)))
        except OverflowError:
            return 0.0 if a * (x - b) < 0 else 1.0
    return 0.0


def _extract_membership_functions(
    mf_data: dict[str, object],
) -> list[dict[str, object]]:
    """Extract membership functions from gRPC response format.

    gRPC returns: {linguistic_variables: [{name, membership_functions: [{name, function_type, parameters}]}]}
    We need: [{term, function_type, parameters}]
    """
    result: list[dict[str, object]] = []
    raw_vars = mf_data.get("linguistic_variables", [])
    if not isinstance(raw_vars, list):
        return result
    for lv in raw_vars:
        if not isinstance(lv, dict):
            continue
        mfs = lv.get("membership_functions", [])
        if isinstance(mfs, list) and mfs:
            mf = mfs[0]
            if isinstance(mf, dict):
                result.append(
                    {
                        "term": mf.get("name", lv.get("name", "unknown")),
                        "function_type": mf.get("function_type", "triangular"),
                        "parameters": mf.get("parameters", {}),
                    }
                )
    return result


def _build_chart_data(
    linguistic_vars: list[dict[str, object]],
    u_min: float,
    u_max: float,
    num_points: int = 200,
) -> list[dict[str, object]]:
    step = (u_max - u_min) / (num_points - 1) if num_points > 1 else 1.0
    chart_data: list[dict[str, object]] = []

    for i in range(num_points):
        x = u_min + i * step
        for var in linguistic_vars:
            term = str(var.get("term", "unknown"))
            func_type = str(var.get("function_type", "triangular"))
            params = var.get("parameters", {})
            if isinstance(params, dict):
                y = _calculate_mf(x, func_type, params)
                chart_data.append(
                    {
                        "x": round(x, 2),
                        "Membership": round(y, 4),
                        "Term": term,
                    }
                )

    return chart_data


def _render_function_graph() -> None:
    bridge = get_bridge()

    sensor_types = bridge.list_sensor_types()
    if not sensor_types:
        st.warning("No sensor types available. Backend may be unavailable.")
        return

    sensor_type = st.selectbox(
        "Sensor type",
        sensor_types,
        help="Select a sensor type to view its membership functions",
    )

    mf_data = bridge.get_membership_functions(sensor_type)
    if mf_data is None:
        st.warning("Failed to load membership functions. Backend may be unavailable.")
        return

    linguistic_vars = _extract_membership_functions(mf_data)

    if not linguistic_vars:
        st.info("No linguistic variables defined for this sensor type.")
        return

    all_params: list[float] = []
    for var in linguistic_vars:
        params = var.get("parameters")
        if isinstance(params, dict):
            all_params.extend(float(v) for v in params.values())
    if all_params:
        u_min = min(all_params) - 5
        u_max = max(all_params) + 5
    else:
        u_min, u_max = 0.0, 100.0

    chart_data = _build_chart_data(linguistic_vars, u_min, u_max)

    if not chart_data:
        st.info("No data available to display.")
        return

    df = pd.DataFrame(chart_data)
    x_title = "Value"

    chart = (
        alt.Chart(df)
        .mark_line(strokeWidth=2)
        .encode(
            x=alt.X("x:Q", title=x_title),
            y=alt.Y(
                "Membership:Q",
                title="Membership Degree",
                scale=alt.Scale(domain=[0, 1]),
            ),
            color=alt.Color("Term:N", title="Linguistic Term"),
            tooltip=[
                alt.Tooltip("x:Q", title="Value", format=".2f"),
                alt.Tooltip("Membership:Q", title="μ", format=".3f"),
                alt.Tooltip("Term:N", title="Term"),
            ],
        )
        .properties(height=450)
        .configure_legend(
            orient="bottom",
            titleFontSize=12,
            labelFontSize=11,
        )
    )

    st.altair_chart(chart, use_container_width=True)

    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Sensor Type", str(sensor_type).replace("_", " ").title())

    with col2:
        st.metric("Universe Range", f"{u_min:.0f} – {u_max:.0f}")

    with col3:
        st.metric("Linguistic Terms", len(linguistic_vars))

    with st.expander("Term Details", expanded=False):
        for var in linguistic_vars:
            term = str(var.get("term", "unknown"))
            func_type = str(var.get("function_type", "unknown"))
            params = var.get("parameters")

            if isinstance(params, dict):
                param_str = ", ".join(f"{k}={v}" for k, v in params.items())
            else:
                param_str = ""
            st.markdown(f"**{term}** — `{func_type}({param_str})`")


def _render_json_editor() -> None:
    bridge = get_bridge()

    sensor_types = bridge.list_sensor_types()
    if not sensor_types:
        st.warning("No sensor types available. Backend may be unavailable.")
        return

    sensor_type = st.selectbox(
        "Sensor type",
        sensor_types,
        key="json_editor_sensor_type",
        help="Select a sensor type to edit its membership functions",
    )

    mf_data = bridge.get_membership_functions(sensor_type)
    if mf_data is None:
        st.warning("Failed to load membership functions. Backend may be unavailable.")
        return

    edited_text = st.text_area(
        label="Edit JSON",
        value=json.dumps(mf_data, indent=2),
        height=600,
        key=f"mf_editor_{sensor_type}",
        label_visibility="collapsed",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(
        "Save Membership Functions",
        key=f"save_mf_{sensor_type}",
        type="primary",
        use_container_width=True,
    ):
        try:
            parsed: dict[str, Any] = json.loads(edited_text)
        except json.JSONDecodeError as exc:
            st.error(f"Invalid JSON: {exc}")
            return

        lv_list = parsed.get("linguistic_variables", [])
        if not isinstance(lv_list, list):
            st.error("Invalid format: 'linguistic_variables' must be a list.")
            return

        errors: list[str] = []
        updated = 0
        for lv in lv_list:
            if not isinstance(lv, dict):
                continue
            variable_name = str(lv.get("name", ""))
            mfs = lv.get("membership_functions", [])
            if not isinstance(mfs, list):
                continue
            for mf in mfs:
                if not isinstance(mf, dict):
                    continue
                function_name = str(mf.get("name", ""))
                function_type = str(mf.get("function_type", ""))
                parameters = mf.get("parameters", {})
                if not isinstance(parameters, dict):
                    errors.append(
                        f"{variable_name}/{function_name}: invalid parameters"
                    )
                    continue
                float_params: dict[str, float] = {}
                try:
                    float_params = {k: float(v) for k, v in parameters.items()}
                except (ValueError, TypeError) as exc:
                    errors.append(f"{variable_name}/{function_name}: {exc}")
                    continue
                result = bridge.update_membership_function(
                    str(sensor_type),
                    variable_name,
                    function_name,
                    function_type,
                    float_params,
                )
                if result is None or not result.get("success"):
                    msg = (
                        result.get("message", "Unknown error")
                        if result is not None
                        else "Backend unavailable"
                    )
                    errors.append(f"{variable_name}/{function_name}: {msg}")
                else:
                    updated += 1

        if errors:
            st.error(
                f"Failed to update {len(errors)} function(s):\n" + "\n".join(errors)
            )
        if updated > 0:
            st.success(f"Updated {updated} membership function(s).")


def render() -> None:
    init_session_state()
    render_header("Membership", "Manage fuzzy membership functions for sensor types")

    graph_tab, json_tab = st.tabs(["Graph", "JSON Editor"])
    with graph_tab:
        _render_function_graph()
    with json_tab:
        _render_json_editor()


if __name__ == "__main__":
    render()
