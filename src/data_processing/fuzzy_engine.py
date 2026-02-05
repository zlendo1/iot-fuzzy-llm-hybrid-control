from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.common.utils import load_json
from src.data_processing.membership_functions import (
    MembershipFunction,
    create_membership_function,
)


@dataclass(frozen=True)
class UniverseOfDiscourse:
    min: float
    max: float

    def contains(self, value: float) -> bool:
        return self.min <= value <= self.max

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UniverseOfDiscourse:
        return cls(min=data["min"], max=data["max"])


@dataclass(frozen=True)
class LinguisticVariable:
    term: str
    membership_function: MembershipFunction

    def compute_degree(self, value: float) -> float:
        return self.membership_function.compute_degree(value)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LinguisticVariable:
        mf = create_membership_function(data)
        return cls(term=data["term"], membership_function=mf)


@dataclass(frozen=True)
class SensorTypeConfig:
    sensor_type: str
    unit: str
    universe_of_discourse: UniverseOfDiscourse
    confidence_threshold: float
    linguistic_variables: tuple[LinguisticVariable, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SensorTypeConfig:
        universe = UniverseOfDiscourse.from_dict(data["universe_of_discourse"])
        variables = tuple(
            LinguisticVariable.from_dict(v) for v in data["linguistic_variables"]
        )
        return cls(
            sensor_type=data["sensor_type"],
            unit=data["unit"],
            universe_of_discourse=universe,
            confidence_threshold=data.get("confidence_threshold", 0.1),
            linguistic_variables=variables,
        )

    @classmethod
    def from_json_file(cls, path: Path) -> SensorTypeConfig:
        data = load_json(path)
        return cls.from_dict(data)


@dataclass(frozen=True)
class FuzzificationResult:
    sensor_type: str
    raw_value: float
    memberships: tuple[tuple[str, float], ...]
    timestamp: float = field(default_factory=time.time)

    def get_dominant_term(self) -> tuple[str, float] | None:
        if not self.memberships:
            return None
        return max(self.memberships, key=lambda x: x[1])

    def to_dict(self) -> dict[str, Any]:
        return {
            "sensor_type": self.sensor_type,
            "raw_value": self.raw_value,
            "memberships": dict(self.memberships),
            "timestamp": self.timestamp,
        }


class _LRUCache:
    def __init__(self, max_size: int, ttl_seconds: float) -> None:
        self._cache: OrderedDict[tuple[str, float], tuple[FuzzificationResult, float]] = OrderedDict()
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds

    def get(self, key: tuple[str, float]) -> FuzzificationResult | None:
        if key not in self._cache:
            return None
        result, timestamp = self._cache[key]
        if time.time() - timestamp > self._ttl_seconds:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return result

    def put(self, key: tuple[str, float], value: FuzzificationResult) -> None:
        self._cache[key] = (value, time.time())
        self._cache.move_to_end(key)
        while len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def invalidate(self, sensor_type: str | None = None) -> None:
        if sensor_type is None:
            self._cache.clear()
        else:
            keys_to_remove = [k for k in self._cache if k[0] == sensor_type]
            for key in keys_to_remove:
                del self._cache[key]

    def __len__(self) -> int:
        return len(self._cache)


class FuzzyEngine:
    def __init__(
        self,
        cache_max_size: int = 1000,
        cache_ttl_seconds: float = 300.0,
    ) -> None:
        self._configs: dict[str, SensorTypeConfig] = {}
        self._cache = _LRUCache(max_size=cache_max_size, ttl_seconds=cache_ttl_seconds)

    def load_config(self, config: SensorTypeConfig) -> None:
        self._configs[config.sensor_type] = config
        self._cache.invalidate(config.sensor_type)

    def load_config_from_dict(self, data: dict[str, Any]) -> None:
        config = SensorTypeConfig.from_dict(data)
        self.load_config(config)

    def load_config_from_file(self, path: Path) -> None:
        config = SensorTypeConfig.from_json_file(path)
        self.load_config(config)

    def load_configs_from_directory(self, directory: Path) -> int:
        count = 0
        for json_file in sorted(directory.glob("*.json")):
            self.load_config_from_file(json_file)
            count += 1
        return count

    def get_config(self, sensor_type: str) -> SensorTypeConfig | None:
        return self._configs.get(sensor_type)

    def get_supported_sensor_types(self) -> list[str]:
        return list(self._configs.keys())

    def fuzzify(
        self,
        sensor_type: str,
        value: float,
        use_cache: bool = True,
    ) -> FuzzificationResult:
        if sensor_type not in self._configs:
            raise FuzzyEngineError(f"Unknown sensor type: '{sensor_type}'")

        cache_key = (sensor_type, value)
        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        config = self._configs[sensor_type]
        memberships: list[tuple[str, float]] = []

        for var in config.linguistic_variables:
            degree = var.compute_degree(value)
            if degree >= config.confidence_threshold:
                memberships.append((var.term, degree))

        memberships.sort(key=lambda x: x[1], reverse=True)

        result = FuzzificationResult(
            sensor_type=sensor_type,
            raw_value=value,
            memberships=tuple(memberships),
        )

        if use_cache:
            self._cache.put(cache_key, result)

        return result

    def fuzzify_batch(
        self,
        readings: list[tuple[str, float]],
        use_cache: bool = True,
    ) -> list[FuzzificationResult]:
        return [self.fuzzify(sensor_type, value, use_cache) for sensor_type, value in readings]

    def clear_cache(self) -> None:
        self._cache.invalidate()

    @property
    def cache_size(self) -> int:
        return len(self._cache)


class FuzzyEngineError(Exception):
    pass
