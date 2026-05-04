"""Message handling logic."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from nats_subscriber.schema_loader import SchemaLoader

logger = logging.getLogger(__name__)

# Main NATS message schema that all messages must comply with
MAIN_SCHEMA_REF = "nats.router/message/1.0"


class MessageHandler:
    """Handles JSON message processing and counter management."""

    def __init__(self, counter_file: Path, schema_loader: Optional[SchemaLoader] = None):
        """Initialize message handler.

        Args:
            counter_file: Path to file storing message counter
            schema_loader: Optional SchemaLoader for validation
        """
        self.counter_file = counter_file
        self._counter = self._load_counter()
        self.schema_loader = schema_loader

    def _load_counter(self) -> int:
        """Load counter from file.

        Returns:
            Current counter value
        """
        if self.counter_file.exists():
            try:
                return int(self.counter_file.read_text().strip())
            except (ValueError, IOError) as e:
                logger.warning(f"Failed to load counter: {e}. Starting at 0.")
                return 0
        return 0

    def _save_counter(self) -> None:
        """Save counter to file."""
        self.counter_file.parent.mkdir(parents=True, exist_ok=True)
        self.counter_file.write_text(str(self._counter))

    @property
    def counter(self) -> int:
        """Get current counter value."""
        return self._counter

    def increment_counter(self) -> int:
        """Increment and save counter.

        Returns:
            New counter value
        """
        self._counter += 1
        self._save_counter()
        return self._counter

    def parse_message(self, raw_message: str) -> Optional[Dict[str, Any]]:
        """Parse incoming JSON message.

        Args:
            raw_message: Raw JSON message string

        Returns:
            Parsed message dict or None if invalid
        """
        try:
            message_data = json.loads(raw_message)

            # Validate required fields
            required_fields = ["id", "payload", "producer", "schema"]
            for field in required_fields:
                if field not in message_data:
                    logger.error(f"Missing required field: {field}")
                    return None

            # Validate against main NATS message schema
            if self.schema_loader:
                if not self.schema_loader.validate_message(message_data, MAIN_SCHEMA_REF):
                    logger.error(f"Message failed validation against {MAIN_SCHEMA_REF}")
                    return None

            return message_data
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON message: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return None

    def create_result(self, message: Dict[str, Any]) -> Optional[str]:
        """Create JSON result message with counter.

        Args:
            message: Original parsed message

        Returns:
            JSON result string or None if validation fails
        """
        counter = self.counter
        original_payload = message.get("payload", {})

        result = {
            "id": message.get("id"),
            "producer": "com.nats-poc.subscriber/1.0",
            "schema": "com.nats-poc.subscriber/response/1.0",
            "payload": {
                "message": original_payload.get("message") if isinstance(original_payload, dict) else original_payload,
                "status": "PROCESSED",
                "counter": counter,
            }
        }

        # Validate result against main NATS message schema
        if self.schema_loader:
            if not self.schema_loader.validate_message(result, MAIN_SCHEMA_REF):
                logger.error(f"Result message failed validation against {MAIN_SCHEMA_REF}")
                return None

        return json.dumps(result, indent=2)

    def process_message(self, raw_message: str) -> Optional[str]:
        """Process incoming JSON message and create result.

        Args:
            raw_message: Raw JSON message to process

        Returns:
            JSON result string or None if processing failed
        """
        message = self.parse_message(raw_message)
        if not message:
            return None

        counter = self.increment_counter()
        logger.info(f"Processing message #{counter}")
        logger.info(f"Message ID: {message.get('id')}")
        logger.info(f"Producer: {message.get('producer')}")
        payload = message.get('payload', {})
        if isinstance(payload, dict):
            logger.info(f"Message: {payload.get('message')}")
        else:
            logger.info(f"Payload: {payload}")

        result = self.create_result(message)
        return result
