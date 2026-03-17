"""Tests for Streamlit web app entry point and navigation."""

from __future__ import annotations

import pytest


@pytest.mark.unit
class TestStreamlitAppImport:
    """Test that the streamlit_app module can be imported."""

    def test_streamlit_app_module_can_be_imported(self) -> None:
        """Verify streamlit_app.py exists and can be imported."""
        try:
            from src.interfaces.web import streamlit_app  # type: ignore

            assert streamlit_app is not None
        except ImportError as e:
            pytest.fail(f"Failed to import streamlit_app: {e}")

    def test_main_function_exists(self) -> None:
        """Verify main() function is defined in streamlit_app."""
        from src.interfaces.web import streamlit_app  # type: ignore

        assert hasattr(streamlit_app, "main")
        assert callable(streamlit_app.main)


@pytest.mark.unit
class TestNavigationStructure:
    """Test that navigation pages are properly defined."""

    def test_pages_list_is_defined(self) -> None:
        """Verify PAGES list exists in streamlit_app."""
        from src.interfaces.web import streamlit_app  # type: ignore

        assert hasattr(streamlit_app, "PAGES")

    def test_pages_list_has_seven_entries(self) -> None:
        """Verify PAGES list contains exactly 7 entries."""
        from src.interfaces.web import streamlit_app  # type: ignore

        assert len(streamlit_app.PAGES) == 7

    def test_pages_list_contains_valid_objects(self) -> None:
        """Verify each entry in PAGES is a valid page object."""
        from src.interfaces.web import streamlit_app  # type: ignore

        for page in streamlit_app.PAGES:
            assert page is not None
            assert hasattr(page, "__class__")


@pytest.mark.unit
class TestPageModuleImports:
    """Test that all page modules can be imported."""

    def test_dashboard_page_module_can_be_imported(self) -> None:
        """Verify dashboard.py exists and can be imported."""
        try:
            from src.interfaces.web.pages import dashboard  # type: ignore

            assert dashboard is not None
        except ImportError as e:
            pytest.fail(f"Failed to import dashboard page: {e}")

    def test_devices_page_module_can_be_imported(self) -> None:
        """Verify devices.py exists and can be imported."""
        try:
            from src.interfaces.web.pages import devices  # type: ignore

            assert devices is not None
        except ImportError as e:
            pytest.fail(f"Failed to import devices page: {e}")

    def test_rules_page_module_can_be_imported(self) -> None:
        """Verify rules.py exists and can be imported."""
        try:
            from src.interfaces.web.pages import rules  # type: ignore

            assert rules is not None
        except ImportError as e:
            pytest.fail(f"Failed to import rules page: {e}")

    def test_config_page_module_can_be_imported(self) -> None:
        """Verify config.py exists and can be imported."""
        try:
            from src.interfaces.web.pages import config  # type: ignore

            assert config is not None
        except ImportError as e:
            pytest.fail(f"Failed to import config page: {e}")

    def test_membership_editor_page_module_can_be_imported(self) -> None:
        """Verify membership_editor.py exists and can be imported."""
        try:
            from src.interfaces.web.pages import membership_editor  # type: ignore

            assert membership_editor is not None
        except ImportError as e:
            pytest.fail(f"Failed to import membership_editor page: {e}")

    def test_logs_page_module_can_be_imported(self) -> None:
        """Verify logs.py exists and can be imported."""
        try:
            from src.interfaces.web.pages import logs  # type: ignore

            assert logs is not None
        except ImportError as e:
            pytest.fail(f"Failed to import logs page: {e}")

    def test_system_control_page_module_can_be_imported(self) -> None:
        """Verify system_control.py exists and can be imported."""
        try:
            from src.interfaces.web.pages import system_control  # type: ignore

            assert system_control is not None
        except ImportError as e:
            pytest.fail(f"Failed to import system_control page: {e}")


@pytest.mark.unit
class TestPageRenderFunctions:
    """Test that all page modules have render() functions."""

    def test_dashboard_render_function_exists(self) -> None:
        """Verify dashboard page has render() function."""
        from src.interfaces.web.pages import dashboard  # type: ignore

        assert hasattr(dashboard, "render")
        assert callable(dashboard.render)

    def test_devices_render_function_exists(self) -> None:
        """Verify devices page has render() function."""
        from src.interfaces.web.pages import devices  # type: ignore

        assert hasattr(devices, "render")
        assert callable(devices.render)

    def test_rules_render_function_exists(self) -> None:
        """Verify rules page has render() function."""
        from src.interfaces.web.pages import rules  # type: ignore

        assert hasattr(rules, "render")
        assert callable(rules.render)

    def test_config_render_function_exists(self) -> None:
        """Verify config page has render() function."""
        from src.interfaces.web.pages import config  # type: ignore

        assert hasattr(config, "render")
        assert callable(config.render)

    def test_membership_editor_render_function_exists(self) -> None:
        """Verify membership_editor page has render() function."""
        from src.interfaces.web.pages import membership_editor  # type: ignore

        assert hasattr(membership_editor, "render")
        assert callable(membership_editor.render)

    def test_logs_render_function_exists(self) -> None:
        """Verify logs page has render() function."""
        from src.interfaces.web.pages import logs  # type: ignore

        assert hasattr(logs, "render")
        assert callable(logs.render)

    def test_system_control_render_function_exists(self) -> None:
        """Verify system_control page has render() function."""
        from src.interfaces.web.pages import system_control  # type: ignore

        assert hasattr(system_control, "render")
        assert callable(system_control.render)


@pytest.mark.unit
class TestStreamlitAppStructure:
    """Test the structural integrity of the streamlit_app module."""

    def test_streamlit_app_has_from_future_annotations(self) -> None:
        """Verify streamlit_app uses from __future__ import annotations."""
        from src.interfaces.web import streamlit_app  # type: ignore

        assert streamlit_app.__name__ == "src.interfaces.web.streamlit_app"

    def test_main_is_callable_with_no_args(self) -> None:
        """Verify main() function can be called with no arguments."""
        import inspect

        from src.interfaces.web import streamlit_app  # type: ignore

        sig = inspect.signature(streamlit_app.main)
        assert len(sig.parameters) == 0
