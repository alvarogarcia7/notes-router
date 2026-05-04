"""Payload loading utilities for NATS messages."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PayloadLoader:
    """Load message payloads from JSON files."""

    @staticmethod
    def load_file(file_path: str) -> Optional[List[Dict[str, Any]]]:
        """Load payloads from a JSON file.

        Supports two formats:
        1. Single payload object: {...}
        2. Array of payloads: [{...}, {...}]

        Args:
            file_path: Path to JSON file

        Returns:
            List of payload dicts or None if failed
        """
        try:
            path = Path(file_path)

            if not path.exists():
                logger.error(f"File not found: {file_path}")
                return None

            if not path.is_file():
                logger.error(f"Not a file: {file_path}")
                return None

            with open(path) as f:
                data = json.load(f)

            # Handle both single object and array of objects
            if isinstance(data, list):
                payloads = data
            elif isinstance(data, dict):
                payloads = [data]
            else:
                logger.error(f"Invalid JSON format: expected object or array, got {type(data).__name__}")
                return None

            logger.info(f"Loaded {len(payloads)} payload(s) from {file_path}")
            return payloads

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {file_path}: {e}")
            return None
        except IOError as e:
            logger.error(f"IO error reading {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None

    @staticmethod
    def load_files(file_paths: List[str]) -> List[Dict[str, Any]]:
        """Load payloads from multiple JSON files.

        Args:
            file_paths: List of file paths to load

        Returns:
            Combined list of all payloads
        """
        all_payloads = []

        for file_path in file_paths:
            payloads = PayloadLoader.load_file(file_path)
            if payloads:
                all_payloads.extend(payloads)
            else:
                logger.warning(f"Skipped {file_path}")

        logger.info(f"Total payloads loaded: {len(all_payloads)}")
        return all_payloads

    @staticmethod
    def validate_payload(payload: Dict[str, Any]) -> bool:
        """Validate payload structure.

        Args:
            payload: Payload to validate

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(payload, dict):
            logger.error(f"Payload must be a dict, got {type(payload).__name__}")
            return False

        # Check if it's a complete NATS message or just content
        if "id" in payload and "producer" in payload and "schema" in payload:
            # Complete message, validate message structure
            if "payload" not in payload:
                logger.error("Complete message missing 'payload' field")
                return False
            if not isinstance(payload.get("payload"), dict):
                logger.error("Message 'payload' field must be a dict")
                return False
            if "message" not in payload["payload"]:
                logger.error("Message payload missing 'message' field")
                return False
        else:
            # Just content, will be wrapped in message envelope
            if "message" not in payload and "text" not in payload and "content" not in payload:
                logger.warning("Payload has no message/text/content field - will be treated as message content")

        return True

    @staticmethod
    def wrap_payload(
        content: Dict[str, Any],
        producer: str = "com.nats-poc.cli/1.0",
        message_type: str = "cli-message",
        message_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Wrap content in NATS message envelope.

        Args:
            content: Content to wrap
            producer: Producer identifier
            message_type: Message type for schema reference
            message_id: Optional message ID (generated if not provided)

        Returns:
            Complete NATS message
        """
        import uuid as uuid_module

        if message_id is None:
            message_id = str(uuid_module.uuid4())

        # Extract message text if available
        if isinstance(content, dict):
            message_text = content.get(
                "message",
                content.get("text", content.get("content", json.dumps(content)))
            )
        else:
            message_text = str(content)

        return {
            "id": message_id,
            "producer": producer,
            "schema": f"com.nats-poc.cli/{message_type}/1.0",
            "payload": {
                "message": message_text,
            }
        }
