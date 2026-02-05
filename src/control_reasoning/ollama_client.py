"""Ollama Client for LLM inference.

This module provides the OllamaClient class for communicating with
the Ollama REST API for local LLM inference.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests

from src.common.logging import get_logger
from src.common.utils import load_json

logger = get_logger(__name__)


@dataclass(frozen=True)
class OllamaConnectionConfig:
    """Configuration for Ollama service connection."""

    host: str = "localhost"
    port: int = 11434
    timeout_seconds: float = 30.0

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OllamaConnectionConfig:
        return cls(
            host=data.get("host", "localhost"),
            port=data.get("port", 11434),
            timeout_seconds=data.get("timeout_seconds", 30.0),
        )


@dataclass(frozen=True)
class OllamaModelConfig:
    """Configuration for LLM model selection."""

    name: str
    fallback_models: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OllamaModelConfig:
        fallbacks = data.get("fallback_models", [])
        return cls(
            name=data["name"],
            fallback_models=tuple(fallbacks),
        )


@dataclass(frozen=True)
class OllamaInferenceConfig:
    """Configuration for LLM inference parameters."""

    temperature: float = 0.3
    max_tokens: int = 512
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> OllamaInferenceConfig:
        if data is None:
            return cls()
        return cls(
            temperature=data.get("temperature", 0.3),
            max_tokens=data.get("max_tokens", 512),
            top_p=data.get("top_p", 0.9),
            top_k=data.get("top_k", 40),
            repeat_penalty=data.get("repeat_penalty", 1.1),
        )

    def to_ollama_options(self) -> dict[str, Any]:
        """Convert to Ollama API options format."""
        return {
            "temperature": self.temperature,
            "num_predict": self.max_tokens,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "repeat_penalty": self.repeat_penalty,
        }


@dataclass(frozen=True)
class OllamaConfig:
    """Complete Ollama configuration."""

    connection: OllamaConnectionConfig
    model: OllamaModelConfig
    inference: OllamaInferenceConfig = field(default_factory=OllamaInferenceConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OllamaConfig:
        llm_data = data.get("llm", data)
        return cls(
            connection=OllamaConnectionConfig.from_dict(llm_data["connection"]),
            model=OllamaModelConfig.from_dict(llm_data["model"]),
            inference=OllamaInferenceConfig.from_dict(llm_data.get("inference")),
        )

    @classmethod
    def from_json_file(cls, path: Path) -> OllamaConfig:
        data = load_json(path)
        return cls.from_dict(data)


@dataclass
class OllamaResponse:
    """Response from Ollama generate API."""

    text: str
    model: str
    total_duration_ns: int
    prompt_eval_count: int
    eval_count: int

    @property
    def total_duration_seconds(self) -> float:
        return self.total_duration_ns / 1_000_000_000

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> OllamaResponse:
        return cls(
            text=data.get("response", ""),
            model=data.get("model", ""),
            total_duration_ns=data.get("total_duration", 0),
            prompt_eval_count=data.get("prompt_eval_count", 0),
            eval_count=data.get("eval_count", 0),
        )


class OllamaClient:
    """Client for communicating with Ollama REST API.

    Provides methods for:
    - Health checking the Ollama service
    - Verifying model availability
    - Generating text completions

    Example:
        >>> config = OllamaConfig.from_json_file(Path("config/llm_config.json"))
        >>> client = OllamaClient(config)
        >>> if client.is_healthy():
        ...     response = client.generate("What is 2+2?")
        ...     print(response.text)
    """

    def __init__(self, config: OllamaConfig) -> None:
        self._config = config
        self._active_model: str | None = None
        self._session = requests.Session()

    @property
    def config(self) -> OllamaConfig:
        return self._config

    @property
    def active_model(self) -> str | None:
        """The currently active model (set after verify_model())."""
        return self._active_model

    @property
    def base_url(self) -> str:
        return self._config.connection.base_url

    @property
    def timeout(self) -> float:
        return self._config.connection.timeout_seconds

    def is_healthy(self) -> bool:
        """Check if Ollama service is running and accessible.

        Returns:
            True if service responds, False otherwise
        """
        try:
            response = self._session.get(
                self.base_url,
                timeout=min(5.0, self.timeout),
            )
            return bool(response.status_code == 200)
        except requests.RequestException:
            return False

    def get_available_models(self) -> list[str]:
        """Get list of locally available models.

        Returns:
            List of model names

        Raises:
            OllamaConnectionError: If cannot connect to service
        """
        try:
            response = self._session.get(
                f"{self.base_url}/api/tags",
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except requests.Timeout as e:
            raise OllamaTimeoutError("Timeout getting model list") from e
        except requests.RequestException as e:
            raise OllamaConnectionError(f"Failed to get models: {e}") from e

    def verify_model(self) -> str:
        """Verify configured model is available, trying fallbacks if needed.

        Returns:
            The name of the verified available model

        Raises:
            OllamaModelNotFoundError: If no configured models are available
            OllamaConnectionError: If cannot connect to service
        """
        available = self.get_available_models()
        models_to_try = [self._config.model.name, *self._config.model.fallback_models]

        for model in models_to_try:
            if model in available:
                self._active_model = model
                logger.info(
                    "Verified Ollama model",
                    extra={
                        "model": model,
                        "is_fallback": model != self._config.model.name,
                    },
                )
                return model

        raise OllamaModelNotFoundError(
            f"No configured models available. Tried: {models_to_try}. "
            f"Available: {available}"
        )

    def generate(
        self,
        prompt: str,
        model: str | None = None,
        system_prompt: str | None = None,
    ) -> OllamaResponse:
        """Generate a text completion.

        Args:
            prompt: The prompt text
            model: Model to use (defaults to active_model or config.model.name)
            system_prompt: Optional system prompt for context

        Returns:
            OllamaResponse with generated text

        Raises:
            OllamaTimeoutError: If request times out
            OllamaConnectionError: If cannot connect to service
            OllamaGenerationError: If generation fails
        """
        model_to_use = model or self._active_model or self._config.model.name

        payload: dict[str, Any] = {
            "model": model_to_use,
            "prompt": prompt,
            "stream": False,
            "options": self._config.inference.to_ollama_options(),
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = self._session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            result = OllamaResponse.from_api_response(data)
            logger.debug(
                "Ollama generation complete",
                extra={
                    "model": model_to_use,
                    "prompt_tokens": result.prompt_eval_count,
                    "generated_tokens": result.eval_count,
                    "duration_s": result.total_duration_seconds,
                },
            )
            return result

        except requests.Timeout as e:
            raise OllamaTimeoutError(
                f"Generation timed out after {self.timeout}s"
            ) from e
        except requests.HTTPError as e:
            raise OllamaGenerationError(
                f"Generation failed: {e.response.status_code} - {e.response.text}"
            ) from e
        except requests.RequestException as e:
            raise OllamaConnectionError(f"Connection error: {e}") from e

    def close(self) -> None:
        """Close the HTTP session."""
        self._session.close()

    def __enter__(self) -> OllamaClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class OllamaError(Exception):
    """Base exception for Ollama client errors."""

    pass


class OllamaConnectionError(OllamaError):
    """Raised when cannot connect to Ollama service."""

    pass


class OllamaTimeoutError(OllamaError):
    """Raised when Ollama request times out."""

    pass


class OllamaModelNotFoundError(OllamaError):
    """Raised when configured model is not available."""

    pass


class OllamaGenerationError(OllamaError):
    """Raised when text generation fails."""

    pass
