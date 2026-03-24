from __future__ import annotations

import streamlit as st

from src.interfaces.web.bridge import get_bridge
from src.interfaces.web.components.common import render_error_message, render_header
from src.interfaces.web.session import init_session_state


def render() -> None:
    init_session_state()
    render_header("Rules", "Create and manage natural language automation rules")

    try:
        bridge = get_bridge()
    except RuntimeError as exc:
        render_error_message(str(exc))
        return

    st.subheader("Add Rule")
    with st.form("add_rule_form", clear_on_submit=True):
        rule_text = st.text_input(
            "Rule text", value="", placeholder="If room is hot, turn on AC"
        )
        submitted = st.form_submit_button("Add Rule")
        if submitted:
            if not rule_text.strip():
                st.warning("Rule text cannot be empty.")
            else:
                result = bridge.add_rule(rule_text.strip())
                if result:
                    rule_id = result.get("id", "unknown")
                    st.success(f"Rule {rule_id} added.")
                    st.rerun()
                else:
                    render_error_message("Failed to add rule")

    st.subheader("Existing Rules")
    rules = bridge.get_rules()
    if not rules:
        st.info("No rules configured yet. Add one above.")
    else:
        for rule in rules:
            rule_id = rule.get("id", "unknown")
            rule_text = rule.get("text", "")
            enabled = rule.get("enabled", False)

            status_indicator = "🟢" if enabled else "🔴"

            with st.expander(
                f"{status_indicator} {rule_id} - {rule_text}", expanded=False
            ):
                st.markdown(f"**Rule ID:** `{rule_id}`")
                st.markdown(f"**Condition & Action:** {rule_text}")

                col1, col2 = st.columns([1, 1])
                with col1:
                    toggle_key = f"toggle_{rule_id}"
                    new_enabled = st.toggle("Enabled", value=enabled, key=toggle_key)
                    if new_enabled != enabled:
                        if new_enabled:
                            success = bridge.enable_rule(rule_id)
                        else:
                            success = bridge.disable_rule(rule_id)

                        if success:
                            st.success("Rule updated.")
                            st.rerun()
                        else:
                            render_error_message("Failed to update rule")

                with col2:
                    delete_key = f"delete_{rule_id}"
                    if st.button("Delete Rule", key=delete_key, type="primary"):
                        if bridge.remove_rule(rule_id):
                            st.success("Rule deleted.")
                            st.rerun()
                        else:
                            render_error_message("Failed to delete rule")


if __name__ == "__main__":
    render()
