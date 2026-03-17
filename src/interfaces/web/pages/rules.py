from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import TYPE_CHECKING

import streamlit as st

from src.interfaces.web.bridge import get_bridge
from src.interfaces.web.components.common import render_error_message, render_header
from src.interfaces.web.session import init_session_state

if TYPE_CHECKING:
    from src.configuration.rule_manager import RuleManager
    from src.control_reasoning.rule_interpreter import NaturalLanguageRule


def _render_add_rule_form(rule_mgr: RuleManager) -> None:
    st.subheader("Add Rule")
    rule_text = st.text_input(
        "Rule text", value="", placeholder="If room is hot, turn on AC"
    )
    if st.button("Add Rule"):
        if not rule_text.strip():
            st.warning("Rule text cannot be empty.")
            return
        rule_id = str(uuid.uuid4())[:8]
        try:
            rule_mgr.add_rule(rule_id, rule_text.strip())
        except Exception as exc:
            render_error_message(f"Failed to add rule: {exc}")
            return
        st.success(f"Rule {rule_id} added.")


def _render_rules_list(
    rule_mgr: RuleManager,
    rules: Sequence[NaturalLanguageRule],
) -> None:
    st.subheader("Existing Rules")
    if not rules:
        st.info("No rules configured yet. Add one above.")
        return

    for rule in rules:
        with st.expander(f"{rule.rule_id} - {rule.rule_text}", expanded=False):
            st.write(f"**ID:** {rule.rule_id}")
            st.write(f"**Text:** {rule.rule_text}")
            enabled = bool(rule.enabled)

            toggle_key = f"toggle_{rule.rule_id}"
            new_enabled = st.toggle("Enabled", value=enabled, key=toggle_key)
            if new_enabled != enabled:
                try:
                    if new_enabled:
                        rule_mgr.enable_rule(rule.rule_id)
                    else:
                        rule_mgr.disable_rule(rule.rule_id)
                    st.success("Rule updated.")
                except Exception as exc:
                    render_error_message(f"Failed to update rule: {exc}")

            delete_key = f"delete_{rule.rule_id}"
            if st.button(f"Delete##{rule.rule_id}", key=delete_key):
                try:
                    rule_mgr.delete_rule(rule.rule_id)
                    st.success("Rule deleted.")
                except Exception as exc:
                    render_error_message(f"Failed to delete rule: {exc}")


def render() -> None:
    init_session_state()
    render_header("Rules")

    try:
        bridge = get_bridge()
    except RuntimeError as exc:
        render_error_message(str(exc))
        return

    rule_mgr = bridge.get_rule_manager()
    if rule_mgr is None:
        st.warning("Rule manager not available. Start the system first.")
        return

    _render_add_rule_form(rule_mgr)

    try:
        rules = rule_mgr.get_all_rules()
    except Exception as exc:
        render_error_message(f"Failed to load rules: {exc}")
        return

    _render_rules_list(rule_mgr, rules)


if __name__ == "__main__":
    render()
