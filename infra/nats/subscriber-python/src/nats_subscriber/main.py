"""Main entry point for NATS Subscriber."""

import logging
import sys

from nats_subscriber.config import get_config
from nats_subscriber.subscriber import Subscriber


def setup_logging(log_level: str) -> None:
    """Configure logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=log_level,
        format="[%(levelname)s] %(message)s",
    )


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        config = get_config()
        setup_logging(config.LOG_LEVEL)

        subscriber = Subscriber(config)
        subscriber.run()

        return 0
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
