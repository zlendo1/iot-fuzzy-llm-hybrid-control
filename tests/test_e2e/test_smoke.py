from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from tests.conftest import create_sensor_reading


def test_fuzzy_pipeline_importable() -> None:
    from src.data_processing.fuzzy_pipeline import FuzzyProcessingPipeline

    assert FuzzyProcessingPipeline


def test_web_ui_importable() -> None:
    from src.interfaces.web.streamlit_app import main

    assert callable(main)


def test_orchestrator_bridge_instantiates() -> None:
    from src.interfaces.web.bridge import OrchestratorBridge

    bridge = OrchestratorBridge()

    assert bridge is not None


def test_sensor_reading_flows_through_fuzzy_pipeline(
    config_directory: Path,
) -> None:
    from src.data_processing.fuzzy_pipeline import FuzzyProcessingPipeline

    pipeline = FuzzyProcessingPipeline(
        config_dir=config_directory / "membership_functions",
        schema_path=config_directory / "schemas" / "membership_functions.schema.json",
    )
    pipeline.initialize()

    reading = create_sensor_reading(value=28.5)
    description = pipeline.process_reading(reading=reading, sensor_type="temperature")

    assert description.sensor_id == reading.sensor_id
    assert description.sensor_type == "temperature"
    assert description.terms


@pytest.mark.parametrize(
    "module_path",
    [
        "src.interfaces.web.pages.dashboard",
        "src.interfaces.web.pages.devices",
        "src.interfaces.web.pages.rules",
        "src.interfaces.web.pages.config",
        "src.interfaces.web.pages.membership_editor",
        "src.interfaces.web.pages.logs",
        "src.interfaces.web.pages.system_control",
    ],
)
def test_web_pages_importable(module_path: str) -> None:
    module = __import__(module_path, fromlist=["render"])

    assert callable(module.render)


def test_application_startup_smoke(
    config_directory: Path,
    rules_directory: Path,
    logs_directory: Path,
) -> None:
    from src.application import Application, ApplicationConfig, ApplicationState

    config = ApplicationConfig(
        config_dir=config_directory,
        rules_dir=rules_directory,
        logs_dir=logs_directory,
        skip_mqtt=True,
        skip_ollama=True,
    )

    with (
        patch(
            "src.control_reasoning.ollama_client.OllamaClient",
            autospec=True,
        ),
        patch(
            "src.device_interface.mqtt_client.mqtt.Client",
            autospec=True,
        ),
    ):
        app = Application(config)

        started = app.start()
        app.stop()

    assert started is True
    assert app.state == ApplicationState.STOPPED
