import json
import threading
import time
from pathlib import Path

import pytest


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    config_path = tmp_path / "config"
    config_path.mkdir()
    
    schemas_path = config_path / "schemas"
    schemas_path.mkdir()
    
    mf_path = config_path / "membership_functions"
    mf_path.mkdir()
    
    return config_path


@pytest.fixture
def mqtt_config() -> dict:
    return {
        "broker": {
            "host": "localhost",
            "port": 1883,
            "keepalive": 60,
        },
        "client": {
            "id": "test-client",
            "clean_session": True,
        },
    }


@pytest.fixture
def mqtt_schema() -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["broker"],
        "properties": {
            "broker": {
                "type": "object",
                "required": ["host"],
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                    "keepalive": {"type": "integer"},
                },
            },
            "client": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "clean_session": {"type": "boolean"},
                },
            },
        },
    }


@pytest.fixture
def llm_config() -> dict:
    return {
        "llm": {
            "provider": "ollama",
            "connection": {
                "host": "localhost",
                "port": 11434,
            },
            "model": {
                "name": "qwen3:0.6b",
            },
        },
    }


@pytest.fixture
def devices_config() -> dict:
    return {
        "devices": [
            {
                "id": "temp_sensor",
                "name": "Temperature Sensor",
                "type": "sensor",
                "device_class": "temperature",
            },
        ],
    }


@pytest.fixture
def temperature_mf() -> dict:
    return {
        "sensor_type": "temperature",
        "unit": "celsius",
        "universe_of_discourse": {"min": -10, "max": 50},
        "linguistic_variables": [
            {
                "term": "cold",
                "function_type": "triangular",
                "parameters": {"a": -10, "b": 0, "c": 15},
            },
        ],
    }


@pytest.fixture
def mf_schema() -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["sensor_type", "unit", "universe_of_discourse", "linguistic_variables"],
        "properties": {
            "sensor_type": {"type": "string"},
            "unit": {"type": "string"},
            "universe_of_discourse": {
                "type": "object",
                "properties": {
                    "min": {"type": "number"},
                    "max": {"type": "number"},
                },
            },
            "linguistic_variables": {
                "type": "array",
                "items": {"type": "object"},
            },
        },
    }


@pytest.fixture
def populated_config_dir(
    config_dir: Path,
    mqtt_config: dict,
    mqtt_schema: dict,
    llm_config: dict,
    devices_config: dict,
    temperature_mf: dict,
    mf_schema: dict,
) -> Path:
    (config_dir / "mqtt_config.json").write_text(json.dumps(mqtt_config))
    (config_dir / "llm_config.json").write_text(json.dumps(llm_config))
    (config_dir / "devices.json").write_text(json.dumps(devices_config))
    
    (config_dir / "schemas" / "mqtt.schema.json").write_text(json.dumps(mqtt_schema))
    (config_dir / "schemas" / "membership_functions.schema.json").write_text(
        json.dumps(mf_schema)
    )
    
    (config_dir / "membership_functions" / "temperature.json").write_text(
        json.dumps(temperature_mf)
    )
    
    return config_dir


class TestConfigurationManagerInit:
    @pytest.mark.unit
    def test_init_with_valid_config_dir(self, populated_config_dir: Path) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        
        assert manager.config_dir == populated_config_dir
        assert manager.schema_dir == populated_config_dir / "schemas"

    @pytest.mark.unit
    def test_init_with_custom_schema_dir(self, config_dir: Path) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        custom_schema_dir = config_dir / "custom_schemas"
        custom_schema_dir.mkdir()
        
        manager = ConfigurationManager(
            config_dir=config_dir,
            schema_dir=custom_schema_dir,
        )
        
        assert manager.schema_dir == custom_schema_dir

    @pytest.mark.unit
    def test_init_loads_schemas(self, populated_config_dir: Path) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        
        assert "mqtt" in manager._schemas
        assert "membership_functions" in manager._schemas

    @pytest.mark.unit
    def test_init_with_missing_schema_dir(self, config_dir: Path) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        (config_dir / "schemas").rmdir()
        
        manager = ConfigurationManager(config_dir=config_dir)
        
        assert len(manager._schemas) == 0


class TestSingletonPattern:
    @pytest.mark.unit
    def test_get_instance_returns_same_instance(self, populated_config_dir: Path) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        ConfigurationManager.reset_instance()
        
        instance1 = ConfigurationManager.get_instance(config_dir=populated_config_dir)
        instance2 = ConfigurationManager.get_instance()
        
        assert instance1 is instance2
        ConfigurationManager.reset_instance()

    @pytest.mark.unit
    def test_reset_instance_clears_singleton(self, populated_config_dir: Path) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        ConfigurationManager.reset_instance()
        
        instance1 = ConfigurationManager.get_instance(config_dir=populated_config_dir)
        ConfigurationManager.reset_instance()
        instance2 = ConfigurationManager.get_instance(config_dir=populated_config_dir)
        
        assert instance1 is not instance2
        ConfigurationManager.reset_instance()


class TestLoadConfig:
    @pytest.mark.unit
    def test_load_config_returns_dict(self, populated_config_dir: Path) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        
        config = manager.load_config("mqtt_config")
        
        assert isinstance(config, dict)
        assert config["broker"]["host"] == "localhost"

    @pytest.mark.unit
    def test_load_config_validates_against_schema(
        self, populated_config_dir: Path
    ) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        
        config = manager.load_config("mqtt_config", validate=True)
        
        assert config["broker"]["host"] == "localhost"

    @pytest.mark.unit
    def test_load_config_raises_on_missing_file(self, config_dir: Path) -> None:
        from src.common.exceptions import ConfigurationError
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=config_dir)
        
        with pytest.raises(ConfigurationError) as exc_info:
            manager.load_config("nonexistent")
        
        assert "not found" in str(exc_info.value)

    @pytest.mark.unit
    def test_load_config_raises_on_invalid_json(self, config_dir: Path) -> None:
        from src.common.exceptions import ConfigurationError
        from src.configuration.config_manager import ConfigurationManager
        
        (config_dir / "invalid.json").write_text("not valid json")
        manager = ConfigurationManager(config_dir=config_dir)
        
        with pytest.raises(ConfigurationError):
            manager.load_config("invalid")

    @pytest.mark.unit
    def test_load_config_raises_on_schema_validation_failure(
        self, populated_config_dir: Path
    ) -> None:
        from src.common.exceptions import ValidationError
        from src.configuration.config_manager import ConfigurationManager
        
        invalid_mqtt = {"invalid": "structure"}
        (populated_config_dir / "mqtt_config.json").write_text(json.dumps(invalid_mqtt))
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        
        with pytest.raises(ValidationError) as exc_info:
            manager.load_config("mqtt_config", validate=True)
        
        assert "validation failed" in str(exc_info.value)

    @pytest.mark.unit
    def test_load_config_skips_validation_when_disabled(
        self, populated_config_dir: Path
    ) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        invalid_mqtt = {"invalid": "structure"}
        (populated_config_dir / "mqtt_config.json").write_text(json.dumps(invalid_mqtt))
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        
        config = manager.load_config("mqtt_config", validate=False)
        
        assert config["invalid"] == "structure"


class TestCaching:
    @pytest.mark.unit
    def test_load_config_caches_result(self, populated_config_dir: Path) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        
        manager.load_config("mqtt_config")
        
        assert "mqtt_config" in manager._cache

    @pytest.mark.unit
    def test_load_config_returns_cached_value(
        self, populated_config_dir: Path
    ) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        
        config1 = manager.load_config("mqtt_config")
        config2 = manager.load_config("mqtt_config")
        
        assert config1 is config2

    @pytest.mark.unit
    def test_cache_invalidated_after_ttl(self, populated_config_dir: Path) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir, cache_ttl=0.1)
        
        config1 = manager.load_config("mqtt_config")
        time.sleep(0.15)
        config2 = manager.load_config("mqtt_config")
        
        assert config1 is not config2

    @pytest.mark.unit
    def test_cache_invalidated_on_file_change(
        self, populated_config_dir: Path, mqtt_config: dict
    ) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        
        manager.load_config("mqtt_config")
        
        time.sleep(0.01)
        mqtt_config["broker"]["port"] = 1884
        (populated_config_dir / "mqtt_config.json").write_text(json.dumps(mqtt_config))
        
        config2 = manager.load_config("mqtt_config")
        
        assert config2["broker"]["port"] == 1884

    @pytest.mark.unit
    def test_reload_invalidates_specific_cache(
        self, populated_config_dir: Path
    ) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        
        manager.load_config("mqtt_config")
        manager.load_config("devices")
        
        manager.reload("mqtt_config")
        
        assert "mqtt_config" not in manager._cache
        assert "devices" in manager._cache

    @pytest.mark.unit
    def test_reload_invalidates_all_cache(self, populated_config_dir: Path) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        
        manager.load_config("mqtt_config")
        manager.load_config("devices")
        
        manager.reload()
        
        assert len(manager._cache) == 0


class TestMembershipFunctions:
    @pytest.mark.unit
    def test_load_membership_function(self, populated_config_dir: Path) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        
        mf = manager.load_membership_function("temperature")
        
        assert mf["sensor_type"] == "temperature"
        assert len(mf["linguistic_variables"]) == 1

    @pytest.mark.unit
    def test_load_membership_function_validates(
        self, populated_config_dir: Path
    ) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        
        mf = manager.load_membership_function("temperature", validate=True)
        
        assert mf["sensor_type"] == "temperature"

    @pytest.mark.unit
    def test_load_membership_function_raises_on_missing(
        self, populated_config_dir: Path
    ) -> None:
        from src.common.exceptions import ConfigurationError
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        
        with pytest.raises(ConfigurationError) as exc_info:
            manager.load_membership_function("nonexistent")
        
        assert "not found" in str(exc_info.value)

    @pytest.mark.unit
    def test_list_membership_functions(self, populated_config_dir: Path) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        
        mf_list = manager.list_membership_functions()
        
        assert "temperature" in mf_list


class TestGetConfig:
    @pytest.mark.unit
    def test_get_config_returns_nested_value(
        self, populated_config_dir: Path
    ) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        
        host = manager.get_config("mqtt_config", "broker", "host")
        
        assert host == "localhost"

    @pytest.mark.unit
    def test_get_config_returns_default_on_missing_key(
        self, populated_config_dir: Path
    ) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        
        value = manager.get_config("mqtt_config", "nonexistent", "key", default="default")
        
        assert value == "default"

    @pytest.mark.unit
    def test_get_config_returns_default_on_missing_file(
        self, config_dir: Path
    ) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=config_dir)
        
        value = manager.get_config("nonexistent", "key", default="default")
        
        assert value == "default"


class TestListConfigs:
    @pytest.mark.unit
    def test_list_configs_returns_all_json_files(
        self, populated_config_dir: Path
    ) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        
        configs = manager.list_configs()
        
        assert "mqtt_config" in configs
        assert "llm_config" in configs
        assert "devices" in configs

    @pytest.mark.unit
    def test_list_configs_returns_sorted(self, populated_config_dir: Path) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        
        configs = manager.list_configs()
        
        assert configs == sorted(configs)


class TestSaveConfig:
    @pytest.mark.unit
    def test_save_config_writes_file(self, config_dir: Path) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=config_dir)
        new_config = {"key": "value"}
        
        manager.save_config("new_config", new_config, validate=False, backup=False)
        
        saved_file = config_dir / "new_config.json"
        assert saved_file.exists()
        assert json.loads(saved_file.read_text())["key"] == "value"

    @pytest.mark.unit
    def test_save_config_creates_backup(
        self, populated_config_dir: Path
    ) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        new_config = {"broker": {"host": "newhost"}}
        
        manager.save_config("mqtt_config", new_config, validate=False, backup=True)
        
        backup_dir = populated_config_dir / "backups"
        assert backup_dir.exists()
        backups = list(backup_dir.glob("mqtt_config_*.json"))
        assert len(backups) == 1

    @pytest.mark.unit
    def test_save_config_invalidates_cache(
        self, populated_config_dir: Path
    ) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        
        manager.load_config("mqtt_config")
        assert "mqtt_config" in manager._cache
        
        new_config = {"broker": {"host": "newhost"}}
        manager.save_config("mqtt_config", new_config, validate=False, backup=False)
        
        assert "mqtt_config" not in manager._cache

    @pytest.mark.unit
    def test_save_config_validates_before_save(
        self, populated_config_dir: Path
    ) -> None:
        from src.common.exceptions import ValidationError
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        invalid_config = {"invalid": "structure"}
        
        with pytest.raises(ValidationError):
            manager.save_config("mqtt_config", invalid_config, validate=True)


class TestPropertyAccessors:
    @pytest.mark.unit
    def test_mqtt_config_property(self, populated_config_dir: Path) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        
        config = manager.mqtt_config
        
        assert config["broker"]["host"] == "localhost"

    @pytest.mark.unit
    def test_llm_config_property(self, populated_config_dir: Path) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        
        config = manager.llm_config
        
        assert config["llm"]["provider"] == "ollama"

    @pytest.mark.unit
    def test_devices_config_property(self, populated_config_dir: Path) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        
        config = manager.devices_config
        
        assert len(config["devices"]) == 1


class TestGetAllConfigs:
    @pytest.mark.unit
    def test_get_all_configs_returns_all(self, populated_config_dir: Path) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        
        configs = manager.get_all_configs()
        
        assert "mqtt_config" in configs
        assert "llm_config" in configs
        assert "devices" in configs

    @pytest.mark.unit
    def test_get_all_configs_skips_invalid(self, populated_config_dir: Path) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        (populated_config_dir / "invalid.json").write_text("not json")
        manager = ConfigurationManager(config_dir=populated_config_dir)
        
        configs = manager.get_all_configs()
        
        assert "invalid" not in configs
        assert "mqtt_config" in configs


class TestThreadSafety:
    @pytest.mark.unit
    def test_concurrent_load_config(self, populated_config_dir: Path) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        results: list[dict] = []
        errors: list[Exception] = []

        def load_config() -> None:
            try:
                config = manager.load_config("mqtt_config")
                results.append(config)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=load_config) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 10
        assert all(r["broker"]["host"] == "localhost" for r in results)

    @pytest.mark.unit
    def test_concurrent_reload(self, populated_config_dir: Path) -> None:
        from src.configuration.config_manager import ConfigurationManager
        
        manager = ConfigurationManager(config_dir=populated_config_dir)
        manager.load_config("mqtt_config")
        errors: list[Exception] = []

        def reload_config() -> None:
            try:
                manager.reload("mqtt_config")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=reload_config) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestCacheEntry:
    @pytest.mark.unit
    def test_cache_entry_creation(self) -> None:
        from src.configuration.config_manager import CacheEntry
        
        entry = CacheEntry(
            data={"key": "value"},
            timestamp=time.time(),
            file_mtime=1234567890.0,
        )
        
        assert entry.data == {"key": "value"}
        assert entry.file_mtime == 1234567890.0
