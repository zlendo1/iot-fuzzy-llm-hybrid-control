from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from src.common.exceptions import ConfigurationError
from src.common.utils import load_json


class ConfigLoader:
    def __init__(self, config_dir: str | Path = "config") -> None:
        self._config_dir = Path(config_dir)
        self._cache: dict[str, dict[str, Any]] = {}

    @property
    def config_dir(self) -> Path:
        return self._config_dir

    def load(self, filename: str, use_cache: bool = True) -> dict[str, Any]:
        if use_cache and filename in self._cache:
            return self._cache[filename]

        path = self._config_dir / filename
        if not path.exists():
            raise ConfigurationError(f"Configuration file not found: {path}")

        try:
            data = load_json(path)
        except Exception as e:
            raise ConfigurationError(f"Failed to load {path}: {e}") from e

        if use_cache:
            self._cache[filename] = data

        return data

    def get_env(self, key: str, default: str | None = None) -> str | None:
        return os.environ.get(key, default)

    def get_env_required(self, key: str) -> str:
        value = os.environ.get(key)
        if value is None:
            raise ConfigurationError(f"Required environment variable not set: {key}")
        return value

    def invalidate_cache(self, filename: str | None = None) -> None:
        if filename:
            self._cache.pop(filename, None)
        else:
            self._cache.clear()
