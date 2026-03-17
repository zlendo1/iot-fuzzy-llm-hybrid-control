"""Conftest for Streamlit web UI tests."""

from __future__ import annotations

import pytest


@pytest.fixture
def app_test_factory():
    """Factory fixture for creating AppTest instances.

    Usage:
        def test_something(app_test_factory):
            at = app_test_factory("src/interfaces/web/streamlit_app.py")
            at.run()
    """
    from streamlit.testing.v1 import AppTest

    def factory(script_path: str) -> AppTest:
        return AppTest.from_file(script_path)

    return factory
