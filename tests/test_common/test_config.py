import json
from pathlib import Path

import pytest


@pytest.mark.unit
def test_config_loader_loads_json_file(tmp_path: Path) -> None:
    from src.common.config import ConfigLoader

    config_data = {"setting": "value", "number": 42}
    config_file = tmp_path / "test.json"
    config_file.write_text(json.dumps(config_data))

    loader = ConfigLoader(tmp_path)
    result = loader.load("test.json")

    assert result == config_data


@pytest.mark.unit
def test_config_loader_caches_by_default(tmp_path: Path) -> None:
    from src.common.config import ConfigLoader

    config_file = tmp_path / "test.json"
    config_file.write_text('{"key": "original"}')

    loader = ConfigLoader(tmp_path)
    first_load = loader.load("test.json")

    config_file.write_text('{"key": "modified"}')
    second_load = loader.load("test.json")

    assert first_load == second_load == {"key": "original"}


@pytest.mark.unit
def test_config_loader_raises_on_missing_file(tmp_path: Path) -> None:
    from src.common.config import ConfigLoader
    from src.common.exceptions import ConfigurationError

    loader = ConfigLoader(tmp_path)

    with pytest.raises(ConfigurationError, match="not found"):
        loader.load("nonexistent.json")


@pytest.mark.unit
def test_config_loader_invalidate_cache(tmp_path: Path) -> None:
    from src.common.config import ConfigLoader

    config_file = tmp_path / "test.json"
    config_file.write_text('{"key": "original"}')

    loader = ConfigLoader(tmp_path)
    loader.load("test.json")

    config_file.write_text('{"key": "modified"}')
    loader.invalidate_cache("test.json")

    result = loader.load("test.json")
    assert result == {"key": "modified"}


@pytest.mark.unit
def test_config_loader_get_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.common.config import ConfigLoader

    monkeypatch.setenv("TEST_VAR", "test_value")
    loader = ConfigLoader()

    assert loader.get_env("TEST_VAR") == "test_value"
    assert loader.get_env("NONEXISTENT", "default") == "default"


@pytest.mark.unit
def test_config_loader_get_env_required_raises(tmp_path: Path) -> None:
    from src.common.config import ConfigLoader
    from src.common.exceptions import ConfigurationError

    loader = ConfigLoader(tmp_path)

    with pytest.raises(ConfigurationError, match="Required environment variable"):
        loader.get_env_required("DEFINITELY_NOT_SET_VAR_12345")
