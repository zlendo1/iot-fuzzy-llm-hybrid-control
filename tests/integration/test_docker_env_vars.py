"""Test environment variable overrides for Docker deployment."""

from __future__ import annotations

import pytest


class TestMQTTClientDockerEnvVars:
    """Integration tests for MQTT client environment variable overrides."""

    @pytest.mark.integration
    def test_mqtt_host_env_var_overrides_config(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """MQTT_HOST environment variable should override broker.host config value."""
        from src.device_interface.mqtt_client import MQTTClientConfig

        # Set env var
        monkeypatch.setenv("MQTT_HOST", "docker-mqtt-host")

        config_data = {"broker": {"host": "localhost", "port": 1883}}
        config = MQTTClientConfig.from_dict(config_data)

        assert config.host == "docker-mqtt-host"

    @pytest.mark.integration
    def test_mqtt_port_env_var_overrides_config(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """MQTT_PORT environment variable should override broker.port config value."""
        from src.device_interface.mqtt_client import MQTTClientConfig

        # Set env var
        monkeypatch.setenv("MQTT_PORT", "9999")

        config_data = {"broker": {"host": "localhost", "port": 1883}}
        config = MQTTClientConfig.from_dict(config_data)

        assert config.port == 9999

    @pytest.mark.integration
    def test_mqtt_both_env_vars_override_config(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Both MQTT_HOST and MQTT_PORT should override config when both set."""
        from src.device_interface.mqtt_client import MQTTClientConfig

        # Set both env vars
        monkeypatch.setenv("MQTT_HOST", "mqtt-docker-server")
        monkeypatch.setenv("MQTT_PORT", "8883")

        config_data = {"broker": {"host": "localhost", "port": 1883}}
        config = MQTTClientConfig.from_dict(config_data)

        assert config.host == "mqtt-docker-server"
        assert config.port == 8883

    @pytest.mark.integration
    def test_mqtt_host_env_var_empty_uses_config(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Empty MQTT_HOST should fall back to config value."""
        from src.device_interface.mqtt_client import MQTTClientConfig

        # Set empty env var
        monkeypatch.setenv("MQTT_HOST", "")

        config_data = {"broker": {"host": "config-host", "port": 1883}}
        config = MQTTClientConfig.from_dict(config_data)

        assert config.host == "config-host"

    @pytest.mark.integration
    def test_mqtt_port_env_var_integer_conversion(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """MQTT_PORT should be converted to integer from string."""
        from src.device_interface.mqtt_client import MQTTClientConfig

        monkeypatch.setenv("MQTT_PORT", "12345")

        config_data = {"broker": {"host": "localhost", "port": 1883}}
        config = MQTTClientConfig.from_dict(config_data)

        assert isinstance(config.port, int)
        assert config.port == 12345

    @pytest.mark.integration
    def test_mqtt_config_without_env_vars_uses_defaults(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Without env vars, should use config values."""
        from src.device_interface.mqtt_client import MQTTClientConfig

        # Ensure env vars are not set
        monkeypatch.delenv("MQTT_HOST", raising=False)
        monkeypatch.delenv("MQTT_PORT", raising=False)

        config_data = {"broker": {"host": "my-broker", "port": 1883}}
        config = MQTTClientConfig.from_dict(config_data)

        assert config.host == "my-broker"
        assert config.port == 1883

    @pytest.mark.integration
    def test_mqtt_preserves_other_config_values(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Env vars should only override host/port, not other config values."""
        from src.device_interface.mqtt_client import MQTTClientConfig

        monkeypatch.setenv("MQTT_HOST", "env-host")
        monkeypatch.setenv("MQTT_PORT", "9999")

        config_data = {
            "broker": {"host": "config-host", "port": 1883, "keepalive": 120},
            "client": {"id": "test-client", "clean_session": False},
            "auth": {"username": "user", "password": "pass"},
        }
        config = MQTTClientConfig.from_dict(config_data)

        # Env vars applied
        assert config.host == "env-host"
        assert config.port == 9999
        # Other values preserved
        assert config.keepalive == 120
        assert config.client_id == "test-client"
        assert config.clean_session is False
        assert config.username == "user"
        assert config.password == "pass"


class TestOllamaClientDockerEnvVars:
    """Integration tests for Ollama client environment variable overrides."""

    @pytest.mark.integration
    def test_ollama_host_env_var_overrides_config(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """OLLAMA_HOST environment variable should override connection.host config value."""
        from src.control_reasoning.ollama_client import OllamaConnectionConfig

        # Set env var
        monkeypatch.setenv("OLLAMA_HOST", "docker-ollama-host")

        config_data = {"host": "localhost", "port": 11434}
        config = OllamaConnectionConfig.from_dict(config_data)

        assert config.host == "docker-ollama-host"

    @pytest.mark.integration
    def test_ollama_port_env_var_overrides_config(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """OLLAMA_PORT environment variable should override connection.port config value."""
        from src.control_reasoning.ollama_client import OllamaConnectionConfig

        # Set env var
        monkeypatch.setenv("OLLAMA_PORT", "5555")

        config_data = {"host": "localhost", "port": 11434}
        config = OllamaConnectionConfig.from_dict(config_data)

        assert config.port == 5555

    @pytest.mark.integration
    def test_ollama_both_env_vars_override_config(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Both OLLAMA_HOST and OLLAMA_PORT should override config when both set."""
        from src.control_reasoning.ollama_client import OllamaConnectionConfig

        # Set both env vars
        monkeypatch.setenv("OLLAMA_HOST", "ollama-docker-server")
        monkeypatch.setenv("OLLAMA_PORT", "7777")

        config_data = {"host": "localhost", "port": 11434}
        config = OllamaConnectionConfig.from_dict(config_data)

        assert config.host == "ollama-docker-server"
        assert config.port == 7777

    @pytest.mark.integration
    def test_ollama_host_env_var_empty_uses_config(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Empty OLLAMA_HOST should fall back to config value."""
        from src.control_reasoning.ollama_client import OllamaConnectionConfig

        # Set empty env var
        monkeypatch.setenv("OLLAMA_HOST", "")

        config_data = {"host": "config-ollama", "port": 11434}
        config = OllamaConnectionConfig.from_dict(config_data)

        assert config.host == "config-ollama"

    @pytest.mark.integration
    def test_ollama_port_env_var_integer_conversion(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """OLLAMA_PORT should be converted to integer from string."""
        from src.control_reasoning.ollama_client import OllamaConnectionConfig

        monkeypatch.setenv("OLLAMA_PORT", "54321")

        config_data = {"host": "localhost", "port": 11434}
        config = OllamaConnectionConfig.from_dict(config_data)

        assert isinstance(config.port, int)
        assert config.port == 54321

    @pytest.mark.integration
    def test_ollama_config_without_env_vars_uses_defaults(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Without env vars, should use config values."""
        from src.control_reasoning.ollama_client import OllamaConnectionConfig

        # Ensure env vars are not set
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        monkeypatch.delenv("OLLAMA_PORT", raising=False)

        config_data = {"host": "my-ollama", "port": 11434}
        config = OllamaConnectionConfig.from_dict(config_data)

        assert config.host == "my-ollama"
        assert config.port == 11434

    @pytest.mark.integration
    def test_ollama_preserves_other_config_values(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Env vars should only override host/port, not other config values."""
        from src.control_reasoning.ollama_client import OllamaConnectionConfig

        monkeypatch.setenv("OLLAMA_HOST", "env-ollama")
        monkeypatch.setenv("OLLAMA_PORT", "9999")

        config_data = {
            "host": "config-host",
            "port": 11434,
            "timeout_seconds": 60.0,
        }
        config = OllamaConnectionConfig.from_dict(config_data)

        # Env vars applied
        assert config.host == "env-ollama"
        assert config.port == 9999
        # Other values preserved
        assert config.timeout_seconds == 60.0

    @pytest.mark.integration
    def test_ollama_base_url_uses_env_var_values(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """base_url property should use env var values for host and port."""
        from src.control_reasoning.ollama_client import OllamaConnectionConfig

        monkeypatch.setenv("OLLAMA_HOST", "my-ollama-server")
        monkeypatch.setenv("OLLAMA_PORT", "8888")

        config_data = {"host": "localhost", "port": 11434}
        config = OllamaConnectionConfig.from_dict(config_data)

        assert config.base_url == "http://my-ollama-server:8888"


class TestDockerEnvVarsIntegration:
    """Integration tests for env var handling across multiple components."""

    @pytest.mark.integration
    def test_mqtt_config_from_full_config_dict(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test MQTT config extraction from full config dictionary with env vars."""
        from src.device_interface.mqtt_client import MQTTClientConfig

        monkeypatch.setenv("MQTT_HOST", "mqtt-server")
        monkeypatch.setenv("MQTT_PORT", "8883")

        # Simulate full config structure
        full_config = {
            "broker": {
                "host": "localhost",
                "port": 1883,
                "keepalive": 60,
            },
            "client": {
                "id": "device-001",
                "clean_session": True,
            },
            "auth": {
                "username": "user",
                "password": "pass",
            },
            "reconnect": {
                "enabled": True,
                "min_delay": 1.0,
                "max_delay": 60.0,
            },
        }

        config = MQTTClientConfig.from_dict(full_config)

        # Verify env vars took precedence
        assert config.host == "mqtt-server"
        assert config.port == 8883
        # Verify rest of config still works
        assert config.keepalive == 60
        assert config.client_id == "device-001"

    @pytest.mark.integration
    def test_ollama_config_from_full_config_dict(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test Ollama config extraction from full config dictionary with env vars."""
        from src.control_reasoning.ollama_client import OllamaConfig

        monkeypatch.setenv("OLLAMA_HOST", "ollama-server")
        monkeypatch.setenv("OLLAMA_PORT", "6666")

        # Simulate full config structure
        full_config = {
            "llm": {
                "connection": {
                    "host": "localhost",
                    "port": 11434,
                    "timeout_seconds": 30.0,
                },
                "model": {
                    "name": "qwen3:0.6b",
                    "fallback_models": ["llama3.2"],
                },
                "inference": {
                    "temperature": 0.3,
                    "max_tokens": 512,
                },
            },
        }

        config = OllamaConfig.from_dict(full_config)

        # Verify env vars took precedence
        assert config.connection.host == "ollama-server"
        assert config.connection.port == 6666
        # Verify rest of config still works
        assert config.model.name == "qwen3:0.6b"
        assert config.connection.timeout_seconds == 30.0

    @pytest.mark.integration
    def test_mqtt_and_ollama_separate_env_vars(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that MQTT and Ollama use separate, independent env vars."""
        from src.control_reasoning.ollama_client import OllamaConnectionConfig
        from src.device_interface.mqtt_client import MQTTClientConfig

        # Set env vars for both services
        monkeypatch.setenv("MQTT_HOST", "mqtt-docker")
        monkeypatch.setenv("MQTT_PORT", "8883")
        monkeypatch.setenv("OLLAMA_HOST", "ollama-docker")
        monkeypatch.setenv("OLLAMA_PORT", "7777")

        mqtt_config = MQTTClientConfig.from_dict(
            {"broker": {"host": "localhost", "port": 1883}}
        )
        ollama_config = OllamaConnectionConfig.from_dict(
            {"host": "localhost", "port": 11434}
        )

        # Each service gets its own env vars
        assert mqtt_config.host == "mqtt-docker"
        assert mqtt_config.port == 8883
        assert ollama_config.host == "ollama-docker"
        assert ollama_config.port == 7777
