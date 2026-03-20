from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


class AppStatusClient:
    """HTTP client for querying application status via REST API.

    DEPRECATED: This class uses the legacy HTTP status endpoint. The system
    now uses gRPC (port 50051) for all communication. This client is retained
    for backwards compatibility with legacy deployments.
    """

    def __init__(self, base_url: str | None = None, timeout: int = 5) -> None:
        """Initialize the status client.

        Args:
            base_url: Base URL for the status endpoint (default: from IOT_APP_URL env or localhost:50051 via gRPC)
            timeout: Request timeout in seconds (default: 5)

        Note:
            For new implementations, use gRPC client instead (localhost:50051).
        """
        if base_url is None:
            base_url = os.environ.get("IOT_APP_URL", "http://localhost:8080")
        self.base_url = base_url
        self.timeout = timeout

    def get_status(self) -> dict[str, Any] | None:
        """Get system status from the running application.

        Returns:
            Dict with status data if successful, None if connection fails or JSON is invalid.
        """
        status_url = f"{self.base_url}/status"

        try:
            with urllib.request.urlopen(status_url, timeout=self.timeout) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    return data
        except (OSError, urllib.error.URLError, json.JSONDecodeError):
            pass

        return None

    def is_app_running(self) -> bool:
        """Check if the application is running and responding.

        Returns:
            True if app responds with valid status, False otherwise.
        """
        return self.get_status() is not None

    def start(self) -> bool:
        """Send start request to the application.

        Returns:
            True if start request was successful, False otherwise.
        """
        start_url = f"{self.base_url}/start"

        try:
            request = urllib.request.Request(start_url, method="POST", data=b"")
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return response.status == 200
        except (OSError, urllib.error.URLError):
            pass

        return False

    def shutdown(self) -> bool:
        """Send shutdown request to the application.

        Returns:
            True if shutdown request was sent successfully, False otherwise.
        """
        shutdown_url = f"{self.base_url}/shutdown"

        try:
            request = urllib.request.Request(shutdown_url, method="POST", data=b"")
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return response.status == 200
        except (OSError, urllib.error.URLError):
            pass

        return False
