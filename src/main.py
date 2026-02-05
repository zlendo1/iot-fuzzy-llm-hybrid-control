"""IoT Fuzzy-LLM Hybrid Control System - Main Entry Point."""

import sys

from src.application import create_application
from src.common.logging import get_logger

logger = get_logger(__name__)


def main() -> None:
    logger.info("IoT Fuzzy-LLM Hybrid Control System starting...")

    try:
        app = create_application()
        app.run_forever()
    except KeyboardInterrupt:
        logger.info("Shutdown requested via keyboard interrupt")
    except Exception:
        logger.exception("Fatal error during application startup")
        sys.exit(1)


if __name__ == "__main__":
    main()
