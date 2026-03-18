"""IoT Fuzzy-LLM Hybrid Control System - Main Entry Point."""

import os
import sys

from src.application import create_application
from src.common.logging import get_logger

logger = get_logger(__name__)


def main() -> None:
    logger.info("IoT Fuzzy-LLM Hybrid Control System starting...")

    try:
        auto_start_str = os.getenv("IOT_AUTO_START", "true").lower()
        auto_start = auto_start_str in ("true", "1", "yes")

        app = create_application()
        app.run_forever(auto_start=auto_start)
    except KeyboardInterrupt:
        logger.info("Shutdown requested via keyboard interrupt")
    except Exception:
        logger.exception("Fatal error during application startup")
        sys.exit(1)


if __name__ == "__main__":
    main()
