"""Membership Editor page - Edit fuzzy membership functions."""

from __future__ import annotations

import json
import math

import altair as alt
import pandas as pd
import streamlit as st

from src.interfaces.web.bridge import get_bridge
from src.interfaces.web.components.common import render_header
from src.interfaces.web.session import init_session_state


def _calculate_mf(x: float, func_type: str, params: dict[str, float]) -> float:
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


def _render_membership_editor() -> None:
    init_session_state()
    render_header("Membership Editor", "Visualize and edit fuzzy membership functions")

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

    visual_tab, json_tab = st.tabs(["Visual Editor", "JSON Editor"])

    with visual_tab:
        universe = mf_data.get("universe_of_discourse", {})
        u_min = float(universe.get("min", 0.0))
        u_max = float(universe.get("max", 100.0))
        unit = str(mf_data.get("unit", ""))
        linguistic_vars = mf_data.get("linguistic_variables", [])

        if not linguistic_vars:
            st.info("No linguistic variables defined for this sensor type.")
        else:
            st.markdown("#### Adjust Parameters")
            updated_vars: list[dict[str, object]] = []

            for i, var in enumerate(linguistic_vars):
                term = str(var.get("term", f"var_{i}"))
                func_type = str(var.get("function_type", "triangular"))
                params = var.get("parameters", {})

                st.markdown(f"**{term}** (`{func_type}`)")

                updated_params: dict[str, float] = {}
                if params:
                    cols = st.columns(len(params))
                    for col, (param_key, param_val) in zip(cols, params.items()):
                        updated_params[param_key] = col.number_input(
                            param_key,
                            value=float(param_val),
                            key=f"param_{sensor_type}_{term}_{param_key}",
                        )

                updated_vars.append(
                    {
                        "term": term,
                        "function_type": func_type,
                        "parameters": updated_params,
                    }
                )

            num_points = 200
            step = (u_max - u_min) / (num_points - 1) if num_points > 1 else 1.0

            chart_data: list[dict[str, object]] = []
            for i in range(num_points):
                x = u_min + i * step
                for var in updated_vars:
                    var_term = str(var["term"])
                    var_func_type = str(var["function_type"])
                    var_params = var["parameters"]
                    if isinstance(var_params, dict):
                        y = _calculate_mf(x, var_func_type, var_params)
                        chart_data.append(
                            {
                                "x": round(x, 2),
                                "Membership": round(y, 4),
                                "Term": var_term,
                            }
                        )

            st.markdown("#### Membership Function Graph")
            x_title = f"Value ({unit})" if unit else "Value"
            df = pd.DataFrame(chart_data)
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
                    color=alt.Color("Term:N", title="Term"),
                    tooltip=["x:Q", "Membership:Q", "Term:N"],
                )
                .properties(height=400)
            )
            st.altair_chart(chart, width="stretch")

            if st.button("Save", key="save_visual"):
                success = True
                for var in updated_vars:
                    res = bridge.update_membership_function(
                        str(sensor_type),
                        str(var["term"]),
                        str(var["term"]),
                        str(var["function_type"]),
                        var["parameters"],  # type: ignore[arg-type]
                    )
                    if res is None:
                        st.error(
                            f"Failed to save {var['term']}. Backend may be unavailable."
                        )
                        success = False

                if success:
                    st.success("Saved.")

    with json_tab:
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

        if st.button("Save", key="save_json"):
            try:
                parsed = json.loads(edited_text)
            except json.JSONDecodeError as exc:
                st.error(f"Invalid JSON: {exc}")
                return
            if not isinstance(parsed, dict):
                st.error("Invalid JSON: root must be an object.")
                return

            linguistic_vars_parsed = parsed.get("linguistic_variables", [])
            if not isinstance(linguistic_vars_parsed, list):
                st.error("Invalid structure: must contain 'linguistic_variables' array")
                return

            success = True
            for var in linguistic_vars_parsed:
                if not isinstance(var, dict):
                    st.error(
                        "Invalid structure: linguistic_variables must contain objects"
                    )
                    return
                var_name = var.get("name")
                if not isinstance(var_name, str):
                    st.error("Invalid structure: variable name must be string")
                    return
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
                    if not isinstance(mf_name, str) or not isinstance(func_type, str):
                        st.error(
                            "Invalid structure: membership function name and type must be strings"
                        )
                        return
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
                        str(sensor_type), var_name, mf_name, func_type, float_params
                    )
                    if result is None:
                        st.error(
                            f"Failed to save {mf_name}. Backend may be unavailable."
                        )
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
