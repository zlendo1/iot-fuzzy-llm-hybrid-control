from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from src.interfaces.web.bridge import get_bridge
from src.interfaces.web.components.common import render_error_message, render_header
from src.interfaces.web.session import init_session_state


def _load_rules() -> list[dict] | None:
    """Load rules from rules config file."""
    rules_path = Path("rules") / "active_rules.json"
    if not rules_path.exists():
        return None
    try:
        with rules_path.open(encoding="utf-8") as f:
            data = json.load(f)
            return data.get("rules", [])
    except (OSError, json.JSONDecodeError):
        return None


def _add_rule_to_file(rule_id: str, rule_text: str) -> bool:
    """Add a rule to the active rules file."""
    rules_path = Path("rules") / "active_rules.json"
    try:
        if rules_path.exists():
            with rules_path.open(encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"rules": []}

        rules = data.get("rules", [])
        rules.append({"rule_id": rule_id, "rule_text": rule_text, "enabled": True})
        data["rules"] = rules

        with rules_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except (OSError, json.JSONDecodeError):
        return False


def _delete_rule_from_file(rule_id: str) -> bool:
    """Delete a rule from the active rules file."""
    rules_path = Path("rules") / "active_rules.json"
    try:
        with rules_path.open(encoding="utf-8") as f:
            data = json.load(f)

        rules = data.get("rules", [])
        rules = [r for r in rules if r.get("rule_id") != rule_id]
        data["rules"] = rules

        with rules_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except (OSError, json.JSONDecodeError):
        return False


def _update_rule_enabled(rule_id: str, enabled: bool) -> bool:
    """Update rule enabled status."""
    rules_path = Path("rules") / "active_rules.json"
    try:
        with rules_path.open(encoding="utf-8") as f:
            data = json.load(f)

        rules = data.get("rules", [])
        for rule in rules:
            if rule.get("rule_id") == rule_id:
                rule["enabled"] = enabled
                break
        data["rules"] = rules

        with rules_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except (OSError, json.JSONDecodeError):
        return False


def render() -> None:
    init_session_state()
    render_header("Rules")

    try:
        bridge = get_bridge()
    except RuntimeError as exc:
        render_error_message(str(exc))
        return

    st.subheader("Add Rule")
    rule_text = st.text_input(
        "Rule text", value="", placeholder="If room is hot, turn on AC"
    )
    if st.button("Add Rule"):
        if not rule_text.strip():
            st.warning("Rule text cannot be empty.")
        else:
            import uuid

            rule_id = str(uuid.uuid4())[:8]
            if _add_rule_to_file(rule_id, rule_text.strip()):
                st.success(f"Rule {rule_id} added.")
                st.rerun()
            else:
                render_error_message("Failed to add rule")

    st.subheader("Existing Rules")
    rules = _load_rules()
    if not rules:
        st.info("No rules configured yet. Add one above.")
    else:
        for rule in rules:
            rule_id = rule.get("rule_id", "unknown")
            rule_text = rule.get("rule_text", "")
            enabled = rule.get("enabled", False)

            with st.expander(f"{rule_id} - {rule_text}", expanded=False):
                st.write(f"**ID:** {rule_id}")
                st.write(f"**Text:** {rule_text}")

                toggle_key = f"toggle_{rule_id}"
                new_enabled = st.toggle("Enabled", value=enabled, key=toggle_key)
                if new_enabled != enabled:
                    if _update_rule_enabled(rule_id, new_enabled):
                        st.success("Rule updated.")
                        st.rerun()
                    else:
                        render_error_message("Failed to update rule")

                delete_key = f"delete_{rule_id}"
                if st.button(f"Delete##{rule_id}", key=delete_key):
                    if _delete_rule_from_file(rule_id):
                        st.success("Rule deleted.")
                        st.rerun()
                    else:
                        render_error_message("Failed to delete rule")


if __name__ == "__main__":
    render()
