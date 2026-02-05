"""Configuration Manager - Singleton for global config access with schema validation."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema

from src.common.exceptions import ConfigurationError, ValidationError
from src.common.logging import get_logger
from src.common.utils import load_json, save_json

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    data: dict[str, Any]
    timestamp: float
    file_mtime: float


@dataclass
class ConfigurationManager:
    config_dir: Path = field(default_factory=lambda: Path("config"))
    schema_dir: Path | None = None
    cache_ttl: float = 300.0

    _cache: dict[str, CacheEntry] = field(default_factory=dict, repr=False)
    _schemas: dict[str, dict[str, Any]] = field(default_factory=dict, repr=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    _instance: ConfigurationManager | None = field(default=None, init=False, repr=False)
    _initialized: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        self.config_dir = Path(self.config_dir)
        if self.schema_dir is None:
            self.schema_dir = self.config_dir / "schemas"
        else:
            self.schema_dir = Path(self.schema_dir)

        self._load_schemas()
        logger.info(
            "ConfigurationManager initialized",
            extra={
                "config_dir": str(self.config_dir),
                "schema_dir": str(self.schema_dir),
            },
        )

    @classmethod
    def get_instance(
        cls,
        config_dir: Path | str | None = None,
        schema_dir: Path | str | None = None,
        cache_ttl: float = 300.0,
    ) -> ConfigurationManager:
        if cls._instance is None:
            cls._instance = cls(
                config_dir=Path(config_dir) if config_dir else Path("config"),
                schema_dir=Path(schema_dir) if schema_dir else None,
                cache_ttl=cache_ttl,
            )
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        cls._instance = None

    def _load_schemas(self) -> None:
        if not self.schema_dir or not self.schema_dir.exists():
            logger.warning(
                "Schema directory not found",
                extra={"schema_dir": str(self.schema_dir)},
            )
            return

        for schema_file in self.schema_dir.glob("*.schema.json"):
            try:
                schema = load_json(schema_file)
                schema_name = schema_file.stem.replace(".schema", "")
                self._schemas[schema_name] = schema
                logger.debug("Loaded schema", extra={"schema_name": schema_name})
            except Exception as e:
                logger.error(
                    "Failed to load schema",
                    extra={"schema_file": str(schema_file), "error": str(e)},
                )

    def _get_schema_for_config(self, config_name: str) -> dict[str, Any] | None:
        schema_mapping = {
            "mqtt_config": "mqtt",
            "llm_config": "llm",
            "devices": "devices",
            "system_config": "system",
        }

        schema_name = schema_mapping.get(config_name, config_name)
        return self._schemas.get(schema_name)

    def _is_cache_valid(self, config_name: str, file_path: Path) -> bool:
        if config_name not in self._cache:
            return False

        entry = self._cache[config_name]
        current_time = time.time()

        if current_time - entry.timestamp > self.cache_ttl:
            return False

        try:
            current_mtime = file_path.stat().st_mtime
            if current_mtime != entry.file_mtime:
                return False
        except OSError:
            return False

        return True

    def _validate_config(
        self, config: dict[str, Any], schema: dict[str, Any], config_name: str
    ) -> None:
        try:
            jsonschema.validate(config, schema)
        except jsonschema.ValidationError as e:
            raise ValidationError(
                f"Configuration '{config_name}' validation failed: {e.message}"
            ) from e
        except jsonschema.SchemaError as e:
            raise ValidationError(
                f"Invalid schema for '{config_name}': {e.message}"
            ) from e

    def load_config(self, config_name: str, validate: bool = True) -> dict[str, Any]:
        with self._lock:
            file_path = self.config_dir / f"{config_name}.json"

            if self._is_cache_valid(config_name, file_path):
                logger.debug("Cache hit", extra={"config_name": config_name})
                return self._cache[config_name].data

            if not file_path.exists():
                raise ConfigurationError(f"Configuration file not found: {file_path}")

            try:
                config = load_json(file_path)
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to load configuration '{config_name}': {e}"
                ) from e

            if validate:
                schema = self._get_schema_for_config(config_name)
                if schema:
                    self._validate_config(config, schema, config_name)

            self._cache[config_name] = CacheEntry(
                data=config,
                timestamp=time.time(),
                file_mtime=file_path.stat().st_mtime,
            )

            logger.debug("Loaded configuration", extra={"config_name": config_name})
            return config

    def load_membership_function(
        self, sensor_type: str, validate: bool = True
    ) -> dict[str, Any]:
        with self._lock:
            cache_key = f"membership_{sensor_type}"
            file_path = self.config_dir / "membership_functions" / f"{sensor_type}.json"

            if self._is_cache_valid(cache_key, file_path):
                logger.debug("Cache hit", extra={"cache_key": cache_key})
                return self._cache[cache_key].data

            if not file_path.exists():
                raise ConfigurationError(
                    f"Membership function not found for sensor type: {sensor_type}"
                )

            try:
                config = load_json(file_path)
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to load membership function '{sensor_type}': {e}"
                ) from e

            if validate:
                schema = self._schemas.get("membership_functions")
                if schema:
                    self._validate_config(config, schema, f"membership_{sensor_type}")

            self._cache[cache_key] = CacheEntry(
                data=config,
                timestamp=time.time(),
                file_mtime=file_path.stat().st_mtime,
            )

            logger.debug(
                "Loaded membership function",
                extra={"sensor_type": sensor_type},
            )
            return config

    def get_config(self, config_name: str, *keys: str, default: Any = None) -> Any:
        try:
            config = self.load_config(config_name)
        except (ConfigurationError, ValidationError):
            return default

        result = config
        for key in keys:
            if isinstance(result, dict) and key in result:
                result = result[key]
            else:
                return default

        return result

    def reload(self, config_name: str | None = None) -> None:
        with self._lock:
            if config_name:
                if config_name in self._cache:
                    del self._cache[config_name]
                logger.info("Invalidated cache", extra={"config_name": config_name})
            else:
                self._cache.clear()
                logger.info("Cleared all configuration cache")

    def list_configs(self) -> list[str]:
        configs = []
        if self.config_dir.exists():
            for f in self.config_dir.glob("*.json"):
                configs.append(f.stem)
        return sorted(configs)

    def list_membership_functions(self) -> list[str]:
        mf_dir = self.config_dir / "membership_functions"
        if not mf_dir.exists():
            return []

        return sorted([f.stem for f in mf_dir.glob("*.json")])

    def save_config(
        self,
        config_name: str,
        config: dict[str, Any],
        validate: bool = True,
        backup: bool = True,
    ) -> None:
        with self._lock:
            file_path = self.config_dir / f"{config_name}.json"

            if validate:
                schema = self._get_schema_for_config(config_name)
                if schema:
                    self._validate_config(config, schema, config_name)

            if backup and file_path.exists():
                backup_dir = self.config_dir / "backups"
                backup_dir.mkdir(parents=True, exist_ok=True)
                timestamp = int(time.time())
                backup_path = backup_dir / f"{config_name}_{timestamp}.json"
                try:
                    existing = load_json(file_path)
                    save_json(backup_path, existing)
                    logger.info(
                        "Created backup",
                        extra={
                            "config_name": config_name,
                            "backup_path": str(backup_path),
                        },
                    )
                except Exception as e:
                    logger.warning(
                        "Failed to create backup",
                        extra={"config_name": config_name, "error": str(e)},
                    )

            try:
                save_json(file_path, config)
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to save configuration '{config_name}': {e}"
                ) from e

            if config_name in self._cache:
                del self._cache[config_name]

            logger.info("Saved configuration", extra={"config_name": config_name})

    def get_all_configs(self) -> dict[str, dict[str, Any]]:
        configs = {}
        for config_name in self.list_configs():
            try:
                configs[config_name] = self.load_config(config_name)
            except (ConfigurationError, ValidationError) as e:
                logger.warning(
                    "Failed to load config",
                    extra={"config_name": config_name, "error": str(e)},
                )
        return configs

    @property
    def mqtt_config(self) -> dict[str, Any]:
        return self.load_config("mqtt_config")

    @property
    def llm_config(self) -> dict[str, Any]:
        return self.load_config("llm_config")

    @property
    def devices_config(self) -> dict[str, Any]:
        return self.load_config("devices")
