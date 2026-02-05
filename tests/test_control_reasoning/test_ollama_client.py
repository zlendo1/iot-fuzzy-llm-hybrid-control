from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# =============================================================================
# OllamaConnectionConfig Tests
# =============================================================================


class TestOllamaConnectionConfig:
    @pytest.mark.unit
    def test_connection_config_defaults(self) -> None:
        from src.control_reasoning.ollama_client import OllamaConnectionConfig

        config = OllamaConnectionConfig()
        assert config.host == "localhost"
        assert config.port == 11434
        assert config.timeout_seconds == 30.0

    @pytest.mark.unit
    def test_connection_config_custom_values(self) -> None:
        from src.control_reasoning.ollama_client import OllamaConnectionConfig

        config = OllamaConnectionConfig(
            host="192.168.1.100",
            port=8080,
            timeout_seconds=60.0,
        )
        assert config.host == "192.168.1.100"
        assert config.port == 8080
        assert config.timeout_seconds == 60.0

    @pytest.mark.unit
    def test_connection_config_base_url(self) -> None:
        from src.control_reasoning.ollama_client import OllamaConnectionConfig

        config = OllamaConnectionConfig(host="myserver", port=1234)
        assert config.base_url == "http://myserver:1234"

    @pytest.mark.unit
    def test_connection_config_from_dict(self) -> None:
        from src.control_reasoning.ollama_client import OllamaConnectionConfig

        data = {"host": "ollama-host", "port": 9999, "timeout_seconds": 45.0}
        config = OllamaConnectionConfig.from_dict(data)
        assert config.host == "ollama-host"
        assert config.port == 9999
        assert config.timeout_seconds == 45.0

    @pytest.mark.unit
    def test_connection_config_from_dict_with_defaults(self) -> None:
        from src.control_reasoning.ollama_client import OllamaConnectionConfig

        data: dict[str, Any] = {}
        config = OllamaConnectionConfig.from_dict(data)
        assert config.host == "localhost"
        assert config.port == 11434
        assert config.timeout_seconds == 30.0

    @pytest.mark.unit
    def test_connection_config_is_frozen(self) -> None:
        from src.control_reasoning.ollama_client import OllamaConnectionConfig

        config = OllamaConnectionConfig()
        with pytest.raises(FrozenInstanceError):
            config.host = "other"  # type: ignore[misc]


# =============================================================================
# OllamaModelConfig Tests
# =============================================================================


class TestOllamaModelConfig:
    @pytest.mark.unit
    def test_model_config_with_name_only(self) -> None:
        from src.control_reasoning.ollama_client import OllamaModelConfig

        config = OllamaModelConfig(name="qwen3:0.6b")
        assert config.name == "qwen3:0.6b"
        assert config.fallback_models == ()

    @pytest.mark.unit
    def test_model_config_with_fallbacks(self) -> None:
        from src.control_reasoning.ollama_client import OllamaModelConfig

        config = OllamaModelConfig(
            name="qwen3:0.6b",
            fallback_models=("tinyllama", "phi3"),
        )
        assert config.name == "qwen3:0.6b"
        assert config.fallback_models == ("tinyllama", "phi3")

    @pytest.mark.unit
    def test_model_config_from_dict(self) -> None:
        from src.control_reasoning.ollama_client import OllamaModelConfig

        data = {
            "name": "mistral",
            "fallback_models": ["llama3.2", "phi3"],
        }
        config = OllamaModelConfig.from_dict(data)
        assert config.name == "mistral"
        assert config.fallback_models == ("llama3.2", "phi3")

    @pytest.mark.unit
    def test_model_config_from_dict_without_fallbacks(self) -> None:
        from src.control_reasoning.ollama_client import OllamaModelConfig

        data = {"name": "tinyllama"}
        config = OllamaModelConfig.from_dict(data)
        assert config.name == "tinyllama"
        assert config.fallback_models == ()

    @pytest.mark.unit
    def test_model_config_is_frozen(self) -> None:
        from src.control_reasoning.ollama_client import OllamaModelConfig

        config = OllamaModelConfig(name="test")
        with pytest.raises(FrozenInstanceError):
            config.name = "other"  # type: ignore[misc]


# =============================================================================
# OllamaInferenceConfig Tests
# =============================================================================


class TestOllamaInferenceConfig:
    @pytest.mark.unit
    def test_inference_config_defaults(self) -> None:
        from src.control_reasoning.ollama_client import OllamaInferenceConfig

        config = OllamaInferenceConfig()
        assert config.temperature == 0.3
        assert config.max_tokens == 512
        assert config.top_p == 0.9
        assert config.top_k == 40
        assert config.repeat_penalty == 1.1

    @pytest.mark.unit
    def test_inference_config_custom_values(self) -> None:
        from src.control_reasoning.ollama_client import OllamaInferenceConfig

        config = OllamaInferenceConfig(
            temperature=0.7,
            max_tokens=1024,
            top_p=0.95,
            top_k=50,
            repeat_penalty=1.2,
        )
        assert config.temperature == 0.7
        assert config.max_tokens == 1024
        assert config.top_p == 0.95
        assert config.top_k == 50
        assert config.repeat_penalty == 1.2

    @pytest.mark.unit
    def test_inference_config_from_dict(self) -> None:
        from src.control_reasoning.ollama_client import OllamaInferenceConfig

        data = {
            "temperature": 0.5,
            "max_tokens": 256,
            "top_p": 0.8,
            "top_k": 30,
            "repeat_penalty": 1.0,
        }
        config = OllamaInferenceConfig.from_dict(data)
        assert config.temperature == 0.5
        assert config.max_tokens == 256
        assert config.top_p == 0.8
        assert config.top_k == 30
        assert config.repeat_penalty == 1.0

    @pytest.mark.unit
    def test_inference_config_from_none(self) -> None:
        from src.control_reasoning.ollama_client import OllamaInferenceConfig

        config = OllamaInferenceConfig.from_dict(None)
        assert config.temperature == 0.3
        assert config.max_tokens == 512

    @pytest.mark.unit
    def test_inference_config_to_ollama_options(self) -> None:
        from src.control_reasoning.ollama_client import OllamaInferenceConfig

        config = OllamaInferenceConfig(
            temperature=0.5,
            max_tokens=256,
            top_p=0.8,
            top_k=30,
            repeat_penalty=1.0,
        )
        options = config.to_ollama_options()
        assert options == {
            "temperature": 0.5,
            "num_predict": 256,
            "top_p": 0.8,
            "top_k": 30,
            "repeat_penalty": 1.0,
        }

    @pytest.mark.unit
    def test_inference_config_is_frozen(self) -> None:
        from src.control_reasoning.ollama_client import OllamaInferenceConfig

        config = OllamaInferenceConfig()
        with pytest.raises(FrozenInstanceError):
            config.temperature = 0.9  # type: ignore[misc]


# =============================================================================
# OllamaConfig Tests
# =============================================================================


class TestOllamaConfig:
    @pytest.mark.unit
    def test_ollama_config_from_dict(self) -> None:
        from src.control_reasoning.ollama_client import OllamaConfig

        data = {
            "llm": {
                "connection": {
                    "host": "localhost",
                    "port": 11434,
                    "timeout_seconds": 30,
                },
                "model": {
                    "name": "qwen3:0.6b",
                    "fallback_models": ["tinyllama"],
                },
                "inference": {
                    "temperature": 0.3,
                    "max_tokens": 512,
                },
            }
        }
        config = OllamaConfig.from_dict(data)
        assert config.connection.host == "localhost"
        assert config.connection.port == 11434
        assert config.model.name == "qwen3:0.6b"
        assert config.model.fallback_models == ("tinyllama",)
        assert config.inference.temperature == 0.3

    @pytest.mark.unit
    def test_ollama_config_from_dict_without_llm_wrapper(self) -> None:
        from src.control_reasoning.ollama_client import OllamaConfig

        data = {
            "connection": {"host": "myhost", "port": 8080},
            "model": {"name": "phi3"},
        }
        config = OllamaConfig.from_dict(data)
        assert config.connection.host == "myhost"
        assert config.model.name == "phi3"

    @pytest.mark.unit
    def test_ollama_config_from_dict_without_inference(self) -> None:
        from src.control_reasoning.ollama_client import OllamaConfig

        data = {
            "connection": {"host": "localhost", "port": 11434},
            "model": {"name": "tinyllama"},
        }
        config = OllamaConfig.from_dict(data)
        # Should use defaults for inference
        assert config.inference.temperature == 0.3
        assert config.inference.max_tokens == 512

    @pytest.mark.unit
    def test_ollama_config_from_json_file(self, tmp_path: Path) -> None:
        from src.control_reasoning.ollama_client import OllamaConfig

        config_data = {
            "llm": {
                "connection": {"host": "testhost", "port": 5555},
                "model": {"name": "testmodel", "fallback_models": ["backup"]},
                "inference": {"temperature": 0.7},
            }
        }
        config_file = tmp_path / "llm_config.json"
        config_file.write_text(json.dumps(config_data))

        config = OllamaConfig.from_json_file(config_file)
        assert config.connection.host == "testhost"
        assert config.connection.port == 5555
        assert config.model.name == "testmodel"
        assert config.model.fallback_models == ("backup",)
        assert config.inference.temperature == 0.7


# =============================================================================
# OllamaResponse Tests
# =============================================================================


class TestOllamaResponse:
    @pytest.mark.unit
    def test_response_attributes(self) -> None:
        from src.control_reasoning.ollama_client import OllamaResponse

        response = OllamaResponse(
            text="Hello, world!",
            model="qwen3:0.6b",
            total_duration_ns=1_500_000_000,
            prompt_eval_count=10,
            eval_count=5,
        )
        assert response.text == "Hello, world!"
        assert response.model == "qwen3:0.6b"
        assert response.total_duration_ns == 1_500_000_000
        assert response.prompt_eval_count == 10
        assert response.eval_count == 5

    @pytest.mark.unit
    def test_response_total_duration_seconds(self) -> None:
        from src.control_reasoning.ollama_client import OllamaResponse

        response = OllamaResponse(
            text="test",
            model="model",
            total_duration_ns=2_500_000_000,
            prompt_eval_count=0,
            eval_count=0,
        )
        assert response.total_duration_seconds == 2.5

    @pytest.mark.unit
    def test_response_from_api_response(self) -> None:
        from src.control_reasoning.ollama_client import OllamaResponse

        api_data = {
            "response": "Generated text here",
            "model": "tinyllama",
            "total_duration": 3_000_000_000,
            "prompt_eval_count": 15,
            "eval_count": 20,
        }
        response = OllamaResponse.from_api_response(api_data)
        assert response.text == "Generated text here"
        assert response.model == "tinyllama"
        assert response.total_duration_ns == 3_000_000_000
        assert response.prompt_eval_count == 15
        assert response.eval_count == 20

    @pytest.mark.unit
    def test_response_from_api_response_with_missing_fields(self) -> None:
        from src.control_reasoning.ollama_client import OllamaResponse

        api_data: dict[str, Any] = {}
        response = OllamaResponse.from_api_response(api_data)
        assert response.text == ""
        assert response.model == ""
        assert response.total_duration_ns == 0
        assert response.prompt_eval_count == 0
        assert response.eval_count == 0


# =============================================================================
# OllamaClient Tests
# =============================================================================


def _create_test_config() -> Any:
    """Helper to create a test OllamaConfig."""
    from src.control_reasoning.ollama_client import (
        OllamaConfig,
        OllamaConnectionConfig,
        OllamaInferenceConfig,
        OllamaModelConfig,
    )

    return OllamaConfig(
        connection=OllamaConnectionConfig(
            host="localhost", port=11434, timeout_seconds=30.0
        ),
        model=OllamaModelConfig(
            name="qwen3:0.6b", fallback_models=("tinyllama", "phi3")
        ),
        inference=OllamaInferenceConfig(temperature=0.3, max_tokens=512),
    )


class TestOllamaClientProperties:
    @pytest.mark.unit
    def test_client_config_property(self) -> None:
        from src.control_reasoning.ollama_client import OllamaClient

        config = _create_test_config()
        client = OllamaClient(config)
        assert client.config is config

    @pytest.mark.unit
    def test_client_base_url_property(self) -> None:
        from src.control_reasoning.ollama_client import OllamaClient

        config = _create_test_config()
        client = OllamaClient(config)
        assert client.base_url == "http://localhost:11434"

    @pytest.mark.unit
    def test_client_timeout_property(self) -> None:
        from src.control_reasoning.ollama_client import OllamaClient

        config = _create_test_config()
        client = OllamaClient(config)
        assert client.timeout == 30.0

    @pytest.mark.unit
    def test_client_active_model_initially_none(self) -> None:
        from src.control_reasoning.ollama_client import OllamaClient

        config = _create_test_config()
        client = OllamaClient(config)
        assert client.active_model is None


class TestOllamaClientHealthCheck:
    @pytest.mark.unit
    def test_is_healthy_returns_true_on_success(self) -> None:
        from src.control_reasoning.ollama_client import OllamaClient

        config = _create_test_config()
        client = OllamaClient(config)

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(client._session, "get", return_value=mock_response):
            assert client.is_healthy() is True

    @pytest.mark.unit
    def test_is_healthy_returns_false_on_non_200(self) -> None:
        from src.control_reasoning.ollama_client import OllamaClient

        config = _create_test_config()
        client = OllamaClient(config)

        mock_response = MagicMock()
        mock_response.status_code = 503

        with patch.object(client._session, "get", return_value=mock_response):
            assert client.is_healthy() is False

    @pytest.mark.unit
    def test_is_healthy_returns_false_on_connection_error(self) -> None:
        import requests

        from src.control_reasoning.ollama_client import OllamaClient

        config = _create_test_config()
        client = OllamaClient(config)

        with patch.object(
            client._session, "get", side_effect=requests.ConnectionError()
        ):
            assert client.is_healthy() is False

    @pytest.mark.unit
    def test_is_healthy_uses_limited_timeout(self) -> None:
        from src.control_reasoning.ollama_client import OllamaClient

        config = _create_test_config()
        client = OllamaClient(config)

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(client._session, "get", return_value=mock_response) as mock_get:
            client.is_healthy()
            # Should use min(5.0, timeout) = 5.0
            mock_get.assert_called_once_with("http://localhost:11434", timeout=5.0)


class TestOllamaClientGetAvailableModels:
    @pytest.mark.unit
    def test_get_available_models_returns_model_names(self) -> None:
        from src.control_reasoning.ollama_client import OllamaClient

        config = _create_test_config()
        client = OllamaClient(config)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "qwen3:0.6b"},
                {"name": "tinyllama"},
                {"name": "phi3"},
            ]
        }

        with patch.object(client._session, "get", return_value=mock_response):
            models = client.get_available_models()
            assert models == ["qwen3:0.6b", "tinyllama", "phi3"]

    @pytest.mark.unit
    def test_get_available_models_returns_empty_list_when_none(self) -> None:
        from src.control_reasoning.ollama_client import OllamaClient

        config = _create_test_config()
        client = OllamaClient(config)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": []}

        with patch.object(client._session, "get", return_value=mock_response):
            models = client.get_available_models()
            assert models == []

    @pytest.mark.unit
    def test_get_available_models_raises_on_timeout(self) -> None:
        import requests

        from src.control_reasoning.ollama_client import OllamaClient, OllamaTimeoutError

        config = _create_test_config()
        client = OllamaClient(config)

        with patch.object(client._session, "get", side_effect=requests.Timeout()):
            with pytest.raises(OllamaTimeoutError) as exc_info:
                client.get_available_models()
            assert "Timeout getting model list" in str(exc_info.value)

    @pytest.mark.unit
    def test_get_available_models_raises_on_connection_error(self) -> None:
        import requests

        from src.control_reasoning.ollama_client import (
            OllamaClient,
            OllamaConnectionError,
        )

        config = _create_test_config()
        client = OllamaClient(config)

        with patch.object(
            client._session, "get", side_effect=requests.ConnectionError("refused")
        ):
            with pytest.raises(OllamaConnectionError) as exc_info:
                client.get_available_models()
            assert "Failed to get models" in str(exc_info.value)


class TestOllamaClientVerifyModel:
    @pytest.mark.unit
    def test_verify_model_selects_primary_model(self) -> None:
        from src.control_reasoning.ollama_client import OllamaClient

        config = _create_test_config()
        client = OllamaClient(config)

        with patch.object(
            client, "get_available_models", return_value=["qwen3:0.6b", "tinyllama"]
        ):
            model = client.verify_model()
            assert model == "qwen3:0.6b"
            assert client.active_model == "qwen3:0.6b"

    @pytest.mark.unit
    def test_verify_model_selects_first_fallback_when_primary_unavailable(self) -> None:
        from src.control_reasoning.ollama_client import OllamaClient

        config = _create_test_config()
        client = OllamaClient(config)

        with patch.object(
            client, "get_available_models", return_value=["tinyllama", "phi3"]
        ):
            model = client.verify_model()
            assert model == "tinyllama"
            assert client.active_model == "tinyllama"

    @pytest.mark.unit
    def test_verify_model_selects_second_fallback(self) -> None:
        from src.control_reasoning.ollama_client import OllamaClient

        config = _create_test_config()
        client = OllamaClient(config)

        with patch.object(client, "get_available_models", return_value=["phi3"]):
            model = client.verify_model()
            assert model == "phi3"
            assert client.active_model == "phi3"

    @pytest.mark.unit
    def test_verify_model_raises_when_no_models_available(self) -> None:
        from src.control_reasoning.ollama_client import (
            OllamaClient,
            OllamaModelNotFoundError,
        )

        config = _create_test_config()
        client = OllamaClient(config)

        with patch.object(
            client, "get_available_models", return_value=["mistral", "llama3"]
        ):
            with pytest.raises(OllamaModelNotFoundError) as exc_info:
                client.verify_model()
            assert "No configured models available" in str(exc_info.value)
            assert "qwen3:0.6b" in str(exc_info.value)

    @pytest.mark.unit
    def test_verify_model_raises_when_no_models_at_all(self) -> None:
        from src.control_reasoning.ollama_client import (
            OllamaClient,
            OllamaModelNotFoundError,
        )

        config = _create_test_config()
        client = OllamaClient(config)

        with (
            patch.object(client, "get_available_models", return_value=[]),
            pytest.raises(OllamaModelNotFoundError),
        ):
            client.verify_model()


class TestOllamaClientGenerate:
    @pytest.mark.unit
    def test_generate_returns_response(self) -> None:
        from src.control_reasoning.ollama_client import OllamaClient

        config = _create_test_config()
        client = OllamaClient(config)
        client._active_model = "qwen3:0.6b"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "The answer is 4.",
            "model": "qwen3:0.6b",
            "total_duration": 1_000_000_000,
            "prompt_eval_count": 5,
            "eval_count": 10,
        }

        with patch.object(client._session, "post", return_value=mock_response):
            response = client.generate("What is 2+2?")
            assert response.text == "The answer is 4."
            assert response.model == "qwen3:0.6b"

    @pytest.mark.unit
    def test_generate_uses_active_model(self) -> None:
        from src.control_reasoning.ollama_client import OllamaClient

        config = _create_test_config()
        client = OllamaClient(config)
        client._active_model = "tinyllama"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "test", "model": "tinyllama"}

        with patch.object(client._session, "post", return_value=mock_response) as mock_post:
            client.generate("test prompt")
            call_kwargs = mock_post.call_args.kwargs
            assert call_kwargs["json"]["model"] == "tinyllama"

    @pytest.mark.unit
    def test_generate_uses_explicit_model_override(self) -> None:
        from src.control_reasoning.ollama_client import OllamaClient

        config = _create_test_config()
        client = OllamaClient(config)
        client._active_model = "qwen3:0.6b"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "test", "model": "phi3"}

        with patch.object(client._session, "post", return_value=mock_response) as mock_post:
            client.generate("test prompt", model="phi3")
            call_kwargs = mock_post.call_args.kwargs
            assert call_kwargs["json"]["model"] == "phi3"

    @pytest.mark.unit
    def test_generate_uses_config_model_when_no_active_model(self) -> None:
        from src.control_reasoning.ollama_client import OllamaClient

        config = _create_test_config()
        client = OllamaClient(config)
        # active_model is None

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "test", "model": "qwen3:0.6b"}

        with patch.object(client._session, "post", return_value=mock_response) as mock_post:
            client.generate("test prompt")
            call_kwargs = mock_post.call_args.kwargs
            assert call_kwargs["json"]["model"] == "qwen3:0.6b"

    @pytest.mark.unit
    def test_generate_includes_system_prompt(self) -> None:
        from src.control_reasoning.ollama_client import OllamaClient

        config = _create_test_config()
        client = OllamaClient(config)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "test", "model": "qwen3:0.6b"}

        with patch.object(client._session, "post", return_value=mock_response) as mock_post:
            client.generate("test prompt", system_prompt="You are a helpful assistant.")
            call_kwargs = mock_post.call_args.kwargs
            assert call_kwargs["json"]["system"] == "You are a helpful assistant."

    @pytest.mark.unit
    def test_generate_excludes_system_when_none(self) -> None:
        from src.control_reasoning.ollama_client import OllamaClient

        config = _create_test_config()
        client = OllamaClient(config)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "test", "model": "qwen3:0.6b"}

        with patch.object(client._session, "post", return_value=mock_response) as mock_post:
            client.generate("test prompt")
            call_kwargs = mock_post.call_args.kwargs
            assert "system" not in call_kwargs["json"]

    @pytest.mark.unit
    def test_generate_includes_inference_options(self) -> None:
        from src.control_reasoning.ollama_client import OllamaClient

        config = _create_test_config()
        client = OllamaClient(config)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "test", "model": "qwen3:0.6b"}

        with patch.object(client._session, "post", return_value=mock_response) as mock_post:
            client.generate("test prompt")
            call_kwargs = mock_post.call_args.kwargs
            options = call_kwargs["json"]["options"]
            assert options["temperature"] == 0.3
            assert options["num_predict"] == 512
            assert options["top_p"] == 0.9
            assert options["top_k"] == 40
            assert options["repeat_penalty"] == 1.1

    @pytest.mark.unit
    def test_generate_sets_stream_false(self) -> None:
        from src.control_reasoning.ollama_client import OllamaClient

        config = _create_test_config()
        client = OllamaClient(config)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "test", "model": "qwen3:0.6b"}

        with patch.object(client._session, "post", return_value=mock_response) as mock_post:
            client.generate("test prompt")
            call_kwargs = mock_post.call_args.kwargs
            assert call_kwargs["json"]["stream"] is False

    @pytest.mark.unit
    def test_generate_raises_on_timeout(self) -> None:
        import requests

        from src.control_reasoning.ollama_client import OllamaClient, OllamaTimeoutError

        config = _create_test_config()
        client = OllamaClient(config)

        with patch.object(client._session, "post", side_effect=requests.Timeout()):
            with pytest.raises(OllamaTimeoutError) as exc_info:
                client.generate("test prompt")
            assert "timed out after 30.0s" in str(exc_info.value)

    @pytest.mark.unit
    def test_generate_raises_on_http_error(self) -> None:
        import requests

        from src.control_reasoning.ollama_client import (
            OllamaClient,
            OllamaGenerationError,
        )

        config = _create_test_config()
        client = OllamaClient(config)

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Model not found"
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            response=mock_response
        )

        with patch.object(client._session, "post", return_value=mock_response):
            with pytest.raises(OllamaGenerationError) as exc_info:
                client.generate("test prompt")
            assert "Generation failed" in str(exc_info.value)

    @pytest.mark.unit
    def test_generate_raises_on_connection_error(self) -> None:
        import requests

        from src.control_reasoning.ollama_client import (
            OllamaClient,
            OllamaConnectionError,
        )

        config = _create_test_config()
        client = OllamaClient(config)

        with patch.object(
            client._session, "post", side_effect=requests.ConnectionError()
        ):
            with pytest.raises(OllamaConnectionError) as exc_info:
                client.generate("test prompt")
            assert "Connection error" in str(exc_info.value)


class TestOllamaClientContextManager:
    @pytest.mark.unit
    def test_client_as_context_manager(self) -> None:
        from src.control_reasoning.ollama_client import OllamaClient

        config = _create_test_config()

        with OllamaClient(config) as client:
            assert client.config is config

    @pytest.mark.unit
    def test_close_closes_session(self) -> None:
        from src.control_reasoning.ollama_client import OllamaClient

        config = _create_test_config()
        client = OllamaClient(config)

        with patch.object(client._session, "close") as mock_close:
            client.close()
            mock_close.assert_called_once()


# =============================================================================
# Exception Hierarchy Tests
# =============================================================================


class TestOllamaExceptions:
    @pytest.mark.unit
    def test_ollama_error_is_base_exception(self) -> None:
        from src.control_reasoning.ollama_client import OllamaError

        error = OllamaError("base error")
        assert isinstance(error, Exception)
        assert str(error) == "base error"

    @pytest.mark.unit
    def test_ollama_connection_error_inherits_from_ollama_error(self) -> None:
        from src.control_reasoning.ollama_client import (
            OllamaConnectionError,
            OllamaError,
        )

        error = OllamaConnectionError("connection failed")
        assert isinstance(error, OllamaError)
        assert isinstance(error, Exception)

    @pytest.mark.unit
    def test_ollama_timeout_error_inherits_from_ollama_error(self) -> None:
        from src.control_reasoning.ollama_client import OllamaError, OllamaTimeoutError

        error = OllamaTimeoutError("timed out")
        assert isinstance(error, OllamaError)

    @pytest.mark.unit
    def test_ollama_model_not_found_error_inherits_from_ollama_error(self) -> None:
        from src.control_reasoning.ollama_client import (
            OllamaError,
            OllamaModelNotFoundError,
        )

        error = OllamaModelNotFoundError("model missing")
        assert isinstance(error, OllamaError)

    @pytest.mark.unit
    def test_ollama_generation_error_inherits_from_ollama_error(self) -> None:
        from src.control_reasoning.ollama_client import (
            OllamaError,
            OllamaGenerationError,
        )

        error = OllamaGenerationError("generation failed")
        assert isinstance(error, OllamaError)

    @pytest.mark.unit
    def test_can_catch_all_errors_with_base_class(self) -> None:
        from src.control_reasoning.ollama_client import (
            OllamaConnectionError,
            OllamaError,
            OllamaGenerationError,
            OllamaModelNotFoundError,
            OllamaTimeoutError,
        )

        errors = [
            OllamaConnectionError("conn"),
            OllamaTimeoutError("timeout"),
            OllamaModelNotFoundError("model"),
            OllamaGenerationError("gen"),
        ]

        for error in errors:
            try:
                raise error
            except OllamaError as e:
                assert e is error
