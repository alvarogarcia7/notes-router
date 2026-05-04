"""Message sending utilities for NATS."""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class MessageSender:
    """Send messages to NATS topics."""

    def __init__(self, message_dir: Path):
        """Initialize message sender.

        Args:
            message_dir: Directory for file-based message passing
        """
        self.message_dir = Path(message_dir)
        self.message_dir.mkdir(parents=True, exist_ok=True)

    def send_message(
        self,
        message: Dict[str, Any],
        topic: str = "pipeline.message.input",
        wait_response: bool = False,
        response_timeout: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """Send a message to a topic.

        For file-based PoC, writes to topic file.
        Optionally waits for response.

        Args:
            message: Message to send
            topic: Topic to send to
            wait_response: Whether to wait for response
            response_timeout: Timeout in seconds

        Returns:
            Response message if wait_response=True, else None
        """
        try:
            # Write message to input file
            input_file = self.message_dir / f"{topic}.txt"
            message_json = json.dumps(message)
            input_file.write_text(message_json)

            logger.info(f"Sent message to {topic}")
            logger.debug(f"Message: {message_json}")

            if not wait_response:
                return None

            # Wait for response
            output_topic = topic.replace("input", "output")
            output_file = self.message_dir / f"{output_topic}.txt"
            message_id = message.get("id")

            logger.info(f"Waiting for response (timeout: {response_timeout}s)...")

            start_time = time.time()
            while time.time() - start_time < response_timeout:
                if output_file.exists():
                    response_text = output_file.read_text().strip()
                    try:
                        response = json.loads(response_text)

                        # Verify it's the response to our message
                        if response.get("id") == message_id:
                            logger.info("Received response")
                            logger.debug(f"Response: {response_text}")
                            return response
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse response JSON")
                        return None

                time.sleep(0.5)

            logger.warning(f"Timeout waiting for response after {response_timeout}s")
            return None

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return None

    def send_messages(
        self,
        messages: list,
        topic: str = "pipeline.message.input",
        wait_response: bool = False,
        response_timeout: int = 10,
        delay_between: float = 0.0,
    ) -> list:
        """Send multiple messages to a topic.

        Args:
            messages: List of messages to send
            topic: Topic to send to
            wait_response: Whether to wait for response for each message
            response_timeout: Timeout in seconds
            delay_between: Delay between sends in seconds

        Returns:
            List of responses (if wait_response=True) or empty list
        """
        responses = []

        for i, message in enumerate(messages):
            logger.info(f"Sending message {i + 1}/{len(messages)}")

            response = self.send_message(
                message=message,
                topic=topic,
                wait_response=wait_response,
                response_timeout=response_timeout,
            )

            if wait_response and response:
                responses.append(response)

            if delay_between > 0 and i < len(messages) - 1:
                time.sleep(delay_between)

        return responses
