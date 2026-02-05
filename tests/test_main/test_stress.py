"""Stress and load tests for system capacity limits.

These tests verify the system can handle the capacity limits specified in
ADD Section 8.1:
- 200 devices
- 1000 rules
- 100 sensor readings/second
- 8GB memory footprint

Run with: pytest tests/test_main/test_stress.py -v
"""

from __future__ import annotations

import gc
import json
import time
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def stress_config_dir(
    tmp_path: Path,
    sample_mqtt_config: dict[str, Any],
    sample_llm_config: dict[str, Any],
    sample_temperature_mf: dict[str, Any],
    sample_humidity_mf: dict[str, Any],
) -> Path:
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    schemas_dir = config_dir / "schemas"
    schemas_dir.mkdir()

    mf_dir = config_dir / "membership_functions"
    mf_dir.mkdir()

    (config_dir / "mqtt_config.json").write_text(json.dumps(sample_mqtt_config))
    (config_dir / "llm_config.json").write_text(json.dumps(sample_llm_config))

    (mf_dir / "temperature.json").write_text(json.dumps(sample_temperature_mf))
    (mf_dir / "humidity.json").write_text(json.dumps(sample_humidity_mf))

    return config_dir


def generate_devices(count: int) -> dict[str, Any]:
    devices = []
    for i in range(count):
        device_type = "sensor" if i % 2 == 0 else "actuator"
        device_class = "temperature" if i % 4 < 2 else "humidity"

        device = {
            "id": f"device_{i:04d}",
            "name": f"Device {i}",
            "type": device_type,
            "device_class": device_class,
            "mqtt": {"topic": f"home/room_{i // 10}/device_{i}"},
        }

        if device_type == "actuator":
            device["capabilities"] = ["turn_on", "turn_off", "set_value"]
            device["constraints"] = {"min_value": 0, "max_value": 100}
            device["mqtt"]["command_topic"] = f"home/room_{i // 10}/device_{i}/set"

        if device_type == "sensor":
            device["unit"] = "celsius" if device_class == "temperature" else "percent"

        devices.append(device)

    return {"devices": devices}


def generate_rules(count: int) -> dict[str, Any]:
    rules = []
    conditions = [
        "the temperature is hot",
        "the temperature is cold",
        "humidity is high",
        "humidity is low",
        "motion is detected",
    ]
    actions = [
        "turn on the air conditioner",
        "turn off the air conditioner",
        "activate the dehumidifier",
        "turn on the fan",
        "turn on the light",
    ]

    for i in range(count):
        rule = {
            "rule_id": f"rule_{i:04d}",
            "rule_text": f"If {conditions[i % len(conditions)]}, {actions[i % len(actions)]}",
            "priority": (i % 10) + 1,
            "enabled": True,
        }
        rules.append(rule)

    return {"rules": rules}


class TestDeviceCapacity:
    """Test device registry capacity limits (200 devices target)."""

    TARGET_DEVICES = 200
    LOAD_TIME_TARGET_MS = 5000

    @pytest.mark.stress
    def test_registry_loads_200_devices(
        self,
        stress_config_dir: Path,
    ) -> None:
        from src.common.config import ConfigLoader
        from src.device_interface.registry import DeviceRegistry

        devices_config = generate_devices(self.TARGET_DEVICES)
        (stress_config_dir / "devices.json").write_text(json.dumps(devices_config))

        config_loader = ConfigLoader(config_dir=stress_config_dir)
        registry = DeviceRegistry(config_loader)

        start = time.perf_counter()
        registry.load("devices.json")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(registry.all_devices()) == self.TARGET_DEVICES
        assert elapsed_ms < self.LOAD_TIME_TARGET_MS, (
            f"Loading {self.TARGET_DEVICES} devices took {elapsed_ms:.2f}ms, "
            f"target is {self.LOAD_TIME_TARGET_MS}ms"
        )

    @pytest.mark.stress
    def test_registry_lookup_performance_at_scale(
        self,
        stress_config_dir: Path,
    ) -> None:
        from src.common.config import ConfigLoader
        from src.device_interface.registry import DeviceRegistry

        devices_config = generate_devices(self.TARGET_DEVICES)
        (stress_config_dir / "devices.json").write_text(json.dumps(devices_config))

        config_loader = ConfigLoader(config_dir=stress_config_dir)
        registry = DeviceRegistry(config_loader)
        registry.load("devices.json")

        lookup_times = []
        for i in range(100):
            device_id = f"device_{i:04d}"
            start = time.perf_counter()
            device = registry.get_optional(device_id)
            elapsed_us = (time.perf_counter() - start) * 1_000_000
            lookup_times.append(elapsed_us)
            assert device is not None

        avg_lookup_us = sum(lookup_times) / len(lookup_times)
        assert avg_lookup_us < 1000, (
            f"Average lookup time {avg_lookup_us:.2f}us exceeds 1ms target"
        )


class TestRuleCapacity:
    """Test rule manager capacity limits (1000 rules target)."""

    TARGET_RULES = 1000
    LOAD_TIME_TARGET_MS = 10000

    @pytest.mark.stress
    def test_rule_manager_loads_1000_rules(
        self,
        tmp_path: Path,
    ) -> None:
        from src.configuration.rule_manager import RuleManager

        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()

        rules_file = rules_dir / "active_rules.json"
        rules_config = generate_rules(self.TARGET_RULES)
        rules_file.write_text(json.dumps(rules_config))

        start = time.perf_counter()
        rule_manager = RuleManager(rules_file=rules_file)
        elapsed_ms = (time.perf_counter() - start) * 1000

        rules = rule_manager.get_enabled_rules()
        assert len(rules) == self.TARGET_RULES
        assert elapsed_ms < self.LOAD_TIME_TARGET_MS, (
            f"Loading {self.TARGET_RULES} rules took {elapsed_ms:.2f}ms, "
            f"target is {self.LOAD_TIME_TARGET_MS}ms"
        )

    @pytest.mark.stress
    def test_rule_lookup_performance_at_scale(
        self,
        tmp_path: Path,
    ) -> None:
        from src.configuration.rule_manager import RuleManager

        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()

        rules_file = rules_dir / "active_rules.json"
        rules_config = generate_rules(self.TARGET_RULES)
        rules_file.write_text(json.dumps(rules_config))

        rule_manager = RuleManager(rules_file=rules_file)

        lookup_times = []
        for i in range(100):
            rule_id = f"rule_{i:04d}"
            start = time.perf_counter()
            rule = rule_manager.get_rule_optional(rule_id)
            elapsed_us = (time.perf_counter() - start) * 1_000_000
            lookup_times.append(elapsed_us)
            assert rule is not None

        avg_lookup_us = sum(lookup_times) / len(lookup_times)
        assert avg_lookup_us < 1000, (
            f"Average lookup time {avg_lookup_us:.2f}us exceeds 1ms target"
        )


class TestThroughput:
    """Test sensor reading throughput (100 readings/second target)."""

    TARGET_READINGS_PER_SEC = 100
    TEST_DURATION_SEC = 1.0

    @pytest.mark.stress
    def test_fuzzy_processing_throughput(
        self,
        stress_config_dir: Path,
    ) -> None:
        from src.data_processing.fuzzy_engine import FuzzyEngine

        mf_dir = stress_config_dir / "membership_functions"
        engine = FuzzyEngine()
        engine.load_configs_from_directory(mf_dir)

        total_readings = int(self.TARGET_READINGS_PER_SEC * self.TEST_DURATION_SEC)

        start = time.perf_counter()
        for i in range(total_readings):
            value = 20.0 + (i % 20)
            engine.fuzzify("temperature", value)
        elapsed = time.perf_counter() - start

        actual_rate = total_readings / elapsed
        assert actual_rate >= self.TARGET_READINGS_PER_SEC, (
            f"Processing rate {actual_rate:.1f}/sec below target "
            f"{self.TARGET_READINGS_PER_SEC}/sec"
        )

    @pytest.mark.stress
    def test_pipeline_throughput(
        self,
        stress_config_dir: Path,
    ) -> None:
        from src.data_processing.fuzzy_pipeline import FuzzyProcessingPipeline
        from src.device_interface.messages import SensorReading

        mf_dir = stress_config_dir / "membership_functions"

        pipeline = FuzzyProcessingPipeline(
            config_dir=mf_dir,
            validate_configs=False,
        )
        pipeline.initialize()

        total_readings = int(self.TARGET_READINGS_PER_SEC * self.TEST_DURATION_SEC)

        processed = 0
        start = time.perf_counter()
        for i in range(total_readings):
            reading = SensorReading(
                sensor_id=f"sensor_{i % 25}",
                value=20.0 + (i % 20),
                unit="celsius",
            )
            result = pipeline.process_reading(reading, sensor_type="temperature")
            if result is not None:
                processed += 1
        elapsed = time.perf_counter() - start

        actual_rate = processed / elapsed if elapsed > 0 else 0
        assert actual_rate >= self.TARGET_READINGS_PER_SEC * 0.9, (
            f"Pipeline throughput {actual_rate:.1f}/sec below 90% of target "
            f"({self.TARGET_READINGS_PER_SEC * 0.9:.1f}/sec)"
        )


class TestMemoryConstraints:
    """Test memory usage stays within 8GB footprint."""

    MAX_MEMORY_MB = 512

    @pytest.mark.stress
    def test_memory_with_max_devices(
        self,
        stress_config_dir: Path,
    ) -> None:
        from src.common.config import ConfigLoader
        from src.device_interface.registry import DeviceRegistry

        gc.collect()
        baseline_mb = self._get_memory_usage_mb()

        devices_config = generate_devices(200)
        (stress_config_dir / "devices.json").write_text(json.dumps(devices_config))

        config_loader = ConfigLoader(config_dir=stress_config_dir)
        registry = DeviceRegistry(config_loader)
        registry.load("devices.json")

        gc.collect()
        current_mb = self._get_memory_usage_mb()
        delta_mb = current_mb - baseline_mb

        assert delta_mb < self.MAX_MEMORY_MB, (
            f"Device registry used {delta_mb:.1f}MB, exceeds {self.MAX_MEMORY_MB}MB limit"
        )

    @pytest.mark.stress
    def test_memory_with_max_rules(
        self,
        tmp_path: Path,
    ) -> None:
        from src.configuration.rule_manager import RuleManager

        gc.collect()
        baseline_mb = self._get_memory_usage_mb()

        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()

        rules_file = rules_dir / "active_rules.json"
        rules_config = generate_rules(1000)
        rules_file.write_text(json.dumps(rules_config))

        rule_manager = RuleManager(rules_file=rules_file)
        _ = rule_manager.get_all_rules()

        gc.collect()
        current_mb = self._get_memory_usage_mb()
        delta_mb = current_mb - baseline_mb

        assert delta_mb < self.MAX_MEMORY_MB, (
            f"Rule manager used {delta_mb:.1f}MB, exceeds {self.MAX_MEMORY_MB}MB limit"
        )

    def _get_memory_usage_mb(self) -> float:
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF)
        return usage.ru_maxrss / 1024


class TestCacheEviction:
    """Test cache behavior under load."""

    @pytest.mark.stress
    def test_fuzzy_cache_eviction_under_load(
        self,
        stress_config_dir: Path,
    ) -> None:
        from src.data_processing.fuzzy_engine import FuzzyEngine

        mf_dir = stress_config_dir / "membership_functions"
        engine = FuzzyEngine()
        engine.load_configs_from_directory(mf_dir)

        unique_values = 10000
        for i in range(unique_values):
            value = (i % 1000) / 10.0
            engine.fuzzify("temperature", value)

        cache_size = engine.cache_size
        assert cache_size <= 1000, f"Cache exceeded maximum size: {cache_size}"

    @pytest.mark.stress
    def test_description_builder_handles_load(
        self,
    ) -> None:
        from src.data_processing.fuzzy_engine import FuzzificationResult
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescriptorBuilder,
        )

        builder = LinguisticDescriptorBuilder()

        for i in range(5000):
            memberships = (
                ("cold", 0.1 * (i % 10)),
                ("comfortable", 0.2 * ((i + 1) % 5)),
                ("warm", 0.15 * ((i + 2) % 7)),
                ("hot", 0.3 * ((i + 3) % 4)),
            )
            result = FuzzificationResult(
                sensor_type="temperature",
                raw_value=20.0 + (i % 20),
                memberships=memberships,
            )
            builder.build(f"sensor_{i % 100}", result)

        assert True


class TestGracefulDegradation:
    """Test system behavior under stress conditions."""

    @pytest.mark.stress
    def test_continues_on_individual_reading_failure(
        self,
        stress_config_dir: Path,
    ) -> None:
        from src.data_processing.fuzzy_engine import FuzzyEngine, FuzzyEngineError

        mf_dir = stress_config_dir / "membership_functions"
        engine = FuzzyEngine()
        engine.load_configs_from_directory(mf_dir)

        successful = 0
        failed = 0

        for i in range(200):
            try:
                if i % 50 == 0:
                    engine.fuzzify("unknown_sensor_type", 20.0)
                else:
                    result = engine.fuzzify("temperature", 20.0 + i % 20)
                    if result:
                        successful += 1
            except (ValueError, RuntimeError, FuzzyEngineError):
                failed += 1

        assert successful > 150, f"Too few successful operations: {successful}"
        assert failed == 4, f"Expected 4 failures (i=0,50,100,150), got {failed}"

    @pytest.mark.stress
    def test_handles_rapid_device_queries(
        self,
        stress_config_dir: Path,
    ) -> None:
        from src.common.config import ConfigLoader
        from src.device_interface.registry import DeviceRegistry

        devices_config = generate_devices(100)
        (stress_config_dir / "devices.json").write_text(json.dumps(devices_config))

        config_loader = ConfigLoader(config_dir=stress_config_dir)
        registry = DeviceRegistry(config_loader)
        registry.load("devices.json")

        query_times = []
        for iteration in range(1000):
            device_id = f"device_{(iteration % 100):04d}"
            start = time.perf_counter()
            registry.get_optional(device_id)
            elapsed_us = (time.perf_counter() - start) * 1_000_000
            query_times.append(elapsed_us)

        first_100_avg = sum(query_times[:100]) / 100
        last_100_avg = sum(query_times[-100:]) / 100

        assert last_100_avg < first_100_avg * 2, (
            f"Performance degraded: first 100 avg={first_100_avg:.2f}us, "
            f"last 100 avg={last_100_avg:.2f}us"
        )


class TestConcurrentLoad:
    """Test system under simulated concurrent load."""

    @pytest.mark.stress
    def test_batch_processing_performance(
        self,
        stress_config_dir: Path,
    ) -> None:
        from src.data_processing.fuzzy_engine import FuzzyEngine

        mf_dir = stress_config_dir / "membership_functions"
        engine = FuzzyEngine()
        engine.load_configs_from_directory(mf_dir)

        batch_sizes = [10, 50, 100, 200]
        results = {}

        for batch_size in batch_sizes:
            values = [20.0 + (i % 20) for i in range(batch_size)]

            start = time.perf_counter()
            for value in values:
                engine.fuzzify("temperature", value)
            elapsed = time.perf_counter() - start

            rate = batch_size / elapsed
            results[batch_size] = rate

        base_rate = results[10]
        for batch_size, rate in results.items():
            assert rate >= base_rate * 0.5, (
                f"Batch size {batch_size} rate ({rate:.1f}/s) dropped below "
                f"50% of baseline ({base_rate:.1f}/s)"
            )
