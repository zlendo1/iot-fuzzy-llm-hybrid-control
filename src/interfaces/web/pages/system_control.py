from __future__ import annotations

from typing import Any

import streamlit as st

from src.interfaces.web.bridge import get_bridge
from src.interfaces.web.components.common import (
    render_error_message,
    render_header,
    render_status_badge,
)
from src.interfaces.web.session import init_session_state


def render() -> None:
    init_session_state()
    render_header("System Control")

    try:
        bridge = get_bridge()
    except RuntimeError as exc:
        render_error_message(str(exc))
        return

    try:
        orch = bridge.get_orchestrator()
    except RuntimeError as exc:
        render_error_message(str(exc))
        return

    col1, col2 = st.columns(2)
    with col1:
        st.write("**State:**")
        render_status_badge(orch.state.value)
    with col2:
        st.write(f"**Ready:** {orch.is_ready}")

    status: dict[str, Any] = orch.get_system_status()

    components = status.get("components", {})
    if components:
        st.subheader("Components")
        for name, available in components.items():
            icon = "✅" if available else "❌"
            st.write(f"{icon} {name}")

    init_steps = status.get("initialization_steps", [])
    if init_steps:
        with st.expander("Initialization Steps"):
            for step in init_steps:
                completed_icon = "✅" if step.get("completed") else "❌"
                error_text = f" ERROR: {step['error']}" if step.get("error") else ""
                st.write(
                    f"{completed_icon} **{step.get('name', '')}** — {step.get('description', '')}{error_text}"
                )

    st.subheader("Actions")
    confirm = st.checkbox("Confirm shutdown")
    if st.button("Shutdown System"):
        if confirm:
            try:
                result = orch.shutdown()
                if result:
                    st.success("System shutdown successfully.")
                else:
                    st.warning("Shutdown returned False.")
            except Exception as exc:
                render_error_message(f"Shutdown failed: {exc}")
        else:
            st.warning("Check the confirmation box first.")


if __name__ == "__main__":
    render()
