"""NATS Subscriber implementation."""

import logging
import time
from pathlib import Path
from typing import Optional

from nats_subscriber.config import Config
from nats_subscriber.message_handler import MessageHandler
from nats_subscriber.schema_loader import SchemaLoader


logger = logging.getLogger(__name__)


class Subscriber:
    """NATS message subscriber."""

    def __init__(self, config: Config):
        """Initialize subscriber.

        Args:
            config: Application configuration
        """
        self.config = config
        self.input_path = config.MESSAGE_DIR / f"{config.INPUT_TOPIC}.txt"
        self.output_path = config.MESSAGE_DIR / f"{config.OUTPUT_TOPIC}.txt"

        # Initialize schema loader for validation
        schema_loader = SchemaLoader(
            config.SCHEMA_REGISTRY,
            config.SCHEMA_CACHE_DIR if config.SCHEMA_VALIDATION else None
        )

        self.handler = MessageHandler(config.COUNTER_FILE, schema_loader)

        # Ensure message directory exists
        config.MESSAGE_DIR.mkdir(parents=True, exist_ok=True)

    def _read_message(self) -> Optional[str]:
        """Read message from input file.

        Returns:
            Message content or None if no message available
        """
        try:
            if self.input_path.exists():
                content = self.input_path.read_text().strip()
                return content if content else None
        except IOError as e:
            logger.error(f"Error reading message: {e}")
        return None

    def _write_result(self, result: str) -> bool:
        """Write result to output file.

        Args:
            result: Result to write

        Returns:
            True if successful, False otherwise
        """
        try:
            self.output_path.write_text(result)
            return True
        except IOError as e:
            logger.error(f"Error writing result: {e}")
            return False

    def _cleanup_input(self) -> None:
        """Clean up input message file."""
        try:
            if self.input_path.exists():
                self.input_path.unlink()
        except IOError as e:
            logger.warning(f"Error cleaning up input: {e}")

    def process_pending_messages(self) -> bool:
        """Process any pending messages.

        Returns:
            True if a message was processed, False otherwise
        """
        message = self._read_message()
        if not message:
            return False

        logger.info(f"Received message: {message}")

        # Process message
        result = self.handler.process_message(message)
        if not result:
            return False

        # Write result
        if self._write_result(result):
            logger.info(f"Result published to {self.output_path}")
            self._cleanup_input()
            logger.info(f"Message #{self.handler.counter} processed successfully")
            return True

        return False

    def run(self) -> None:
        """Run subscriber loop.

        Continuously listen for and process messages.
        """
        logger.info("Starting subscriber...")
        logger.info(f"Connecting to NATS at {self.config.NATS_SERVER}")
        logger.info(f"Listening on topic: {self.config.INPUT_TOPIC}")
        logger.info(f"Publishing results to: {self.config.OUTPUT_TOPIC}")

        try:
            while True:
                # Check for messages
                self.process_pending_messages()

                # Wait before checking again
                time.sleep(self.config.POLL_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Shutting down subscriber...")
        except Exception as e:
            logger.error(f"Subscriber error: {e}", exc_info=True)
            raise
