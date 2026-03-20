# ruff: noqa: ARG002
from __future__ import annotations

import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest


class TestAppStatusClient:
    """Tests for AppStatusClient HTTP client."""

    @pytest.mark.unit
    def test_get_status_returns_dict_on_success(self) -> None:
        """get_status should return dict when endpoint responds with 200."""
        from src.interfaces.web.http_client import AppStatusClient

        status_response = {
            "state": "running",
            "uptime": 1234,
            "devices": 5,
            "sensors": 10,
        }

        # Mock the response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(status_response).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = AppStatusClient()
            result = client.get_status()

        assert result == status_response

    @pytest.mark.unit
    def test_get_status_returns_none_on_connection_error(self) -> None:
        """get_status should return None when connection fails."""
        from src.interfaces.web.http_client import AppStatusClient

        def raise_url_error(*_args: object, **_kwargs: object) -> None:
            raise urllib.error.URLError("connection failed")

        with patch("urllib.request.urlopen", side_effect=raise_url_error):
            client = AppStatusClient()
            result = client.get_status()

        assert result is None

    @pytest.mark.unit
    def test_get_status_returns_none_on_json_decode_error(self) -> None:
        """get_status should return None when response is invalid JSON."""
        from src.interfaces.web.http_client import AppStatusClient

        # Mock response with invalid JSON
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b"not valid json"
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = AppStatusClient()
            result = client.get_status()

        assert result is None

    @pytest.mark.unit
    def test_is_app_running_returns_true_when_status_succeeds(self) -> None:
        """is_app_running should return True when get_status succeeds."""
        from src.interfaces.web.http_client import AppStatusClient

        status_response = {"state": "running"}

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(status_response).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = AppStatusClient()
            result = client.is_app_running()

        assert result is True

    @pytest.mark.unit
    def test_is_app_running_returns_false_on_connection_error(self) -> None:
        """is_app_running should return False when connection fails."""
        from src.interfaces.web.http_client import AppStatusClient

        def raise_url_error(*_args: object, **_kwargs: object) -> None:
            raise urllib.error.URLError("connection failed")

        with patch("urllib.request.urlopen", side_effect=raise_url_error):
            client = AppStatusClient()
            result = client.is_app_running()

        assert result is False

    @pytest.mark.unit
    def test_is_app_running_returns_false_on_json_error(self) -> None:
        """is_app_running should return False when response is invalid JSON."""
        from src.interfaces.web.http_client import AppStatusClient

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b"not valid json"
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = AppStatusClient()
            result = client.is_app_running()

        assert result is False

    @pytest.mark.unit
    def test_shutdown_sends_post_request(self) -> None:
        """shutdown should send POST request to /shutdown endpoint."""
        from src.interfaces.web.http_client import AppStatusClient

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None

        with patch(
            "urllib.request.urlopen", return_value=mock_response
        ) as mock_urlopen:
            client = AppStatusClient()
            result = client.shutdown()

        assert result is True
        # Verify urlopen was called
        assert mock_urlopen.called

    @pytest.mark.unit
    def test_shutdown_returns_false_on_error(self) -> None:
        """shutdown should return False when connection fails."""
        from src.interfaces.web.http_client import AppStatusClient

        def raise_url_error(*_args: object, **_kwargs: object) -> None:
            raise urllib.error.URLError("connection failed")

        with patch("urllib.request.urlopen", side_effect=raise_url_error):
            client = AppStatusClient()
            result = client.shutdown()

        assert result is False

    @pytest.mark.unit
    def test_start_sends_post_request(self) -> None:
        """start should send POST request to /start endpoint."""
        from src.interfaces.web.http_client import AppStatusClient

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None

        with patch(
            "urllib.request.urlopen", return_value=mock_response
        ) as mock_urlopen:
            client = AppStatusClient()
            result = client.start()

        assert result is True
        assert mock_urlopen.called

    @pytest.mark.unit
    def test_start_returns_false_on_error(self) -> None:
        """start should return False when connection fails."""
        from src.interfaces.web.http_client import AppStatusClient

        def raise_url_error(*_args: object, **_kwargs: object) -> None:
            raise urllib.error.URLError("connection failed")

        with patch("urllib.request.urlopen", side_effect=raise_url_error):
            client = AppStatusClient()
            result = client.start()

        assert result is False

    @pytest.mark.unit
    def test_client_uses_default_base_url(self) -> None:
        """Client should use http://localhost:8080 as default base URL."""
        from src.interfaces.web.http_client import AppStatusClient

        client = AppStatusClient()
        assert client.base_url == "http://localhost:8080"

    @pytest.mark.unit
    def test_client_uses_custom_base_url(self) -> None:
        """Client should accept custom base URL."""
        from src.interfaces.web.http_client import AppStatusClient

        client = AppStatusClient(base_url="http://example.com:9000")
        assert client.base_url == "http://example.com:9000"

    @pytest.mark.unit
    def test_client_uses_default_timeout(self) -> None:
        """Client should use 5 second timeout by default."""
        from src.interfaces.web.http_client import AppStatusClient

        client = AppStatusClient()
        assert client.timeout == 5

    @pytest.mark.unit
    def test_client_uses_custom_timeout(self) -> None:
        """Client should accept custom timeout."""
        from src.interfaces.web.http_client import AppStatusClient

        client = AppStatusClient(timeout=10)
        assert client.timeout == 10
