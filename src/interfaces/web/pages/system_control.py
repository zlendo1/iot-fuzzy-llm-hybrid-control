from __future__ import annotations

import time
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

    is_running = bridge.is_app_running()

    if is_running:
        st.success("✓ Application is running")

        status = bridge.get_system_status()
        if status:
            st.subheader("System Status")
            st.json(status)

        st.subheader("Actions")
        confirm = st.checkbox("Confirm shutdown")
        if st.button("Shutdown System"):
            if confirm:
                try:
                    result = bridge.shutdown()
                    if result:
                        st.success("✓ Shutdown initiated")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("❌ Shutdown failed")
                except Exception as exc:
                    render_error_message(f"Shutdown failed: {exc}")
            else:
                st.warning("⚠️ Check the confirmation box first.")
    else:
        st.warning("⚠️ Application is not running")

        st.info("**To start the system:**")

        st.subheader("Option 1: Docker Compose")
        st.code("docker compose up -d", language="bash")

        st.subheader("Option 2: Manual (Python)")
        st.code("python -m src.main", language="bash")


if __name__ == "__main__":
    render()
