"""Command-line interface for sending messages to NATS topics."""

import argparse
import json
import logging
import sys
from pathlib import Path

from nats_subscriber.config import get_config
from nats_subscriber.message_sender import MessageSender
from nats_subscriber.payload_loader import PayloadLoader


def setup_logging(log_level: str) -> None:
    """Configure logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=log_level,
        format="[%(levelname)s] %(message)s",
    )


def main(args: list = None) -> int:
    """Main CLI entry point.

    Args:
        args: Command-line arguments (for testing)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="Send JSON payloads to NATS topics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Send single payload from file
  nats-sender payloads.json

  # Send with response waiting
  nats-sender payloads.json --wait-response

  # Send to custom topic
  nats-sender payloads.json --topic custom.topic.input

  # Send multiple files
  nats-sender file1.json file2.json file3.json

  # Send with delay between messages
  nats-sender payloads.json --delay 1.0
        """
    )

    parser.add_argument(
        "files",
        nargs="+",
        help="JSON file(s) containing payload(s)",
    )

    parser.add_argument(
        "-t", "--topic",
        default="pipeline.message.input",
        help="Topic to send to (default: pipeline.message.input)",
    )

    parser.add_argument(
        "-w", "--wait-response",
        action="store_true",
        help="Wait for responses from subscriber",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Response timeout in seconds (default: 10)",
    )

    parser.add_argument(
        "-d", "--delay",
        type=float,
        default=0.0,
        help="Delay between sends in seconds (default: 0)",
    )

    parser.add_argument(
        "-p", "--producer",
        default="com.nats-poc.cli/1.0",
        help="Producer identifier (default: com.nats-poc.cli/1.0)",
    )

    parser.add_argument(
        "-l", "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    parser.add_argument(
        "-m", "--message-dir",
        help="Message directory (overrides config)",
    )

    parser.add_argument(
        "--wrap",
        action="store_true",
        help="Wrap payloads in NATS message envelope",
    )

    try:
        parsed_args = parser.parse_args(args)
        setup_logging(parsed_args.log_level)

        # Load configuration
        config = get_config()

        # Override message directory if provided
        message_dir = parsed_args.message_dir or config.MESSAGE_DIR

        logger = logging.getLogger(__name__)
        logger.info(f"NATS Message Sender (v1.0)")
        logger.info(f"Message directory: {message_dir}")
        logger.info(f"Target topic: {parsed_args.topic}")

        # Load payloads
        logger.info(f"Loading payloads from {len(parsed_args.files)} file(s)...")
        payloads = PayloadLoader.load_files(parsed_args.files)

        if not payloads:
            logger.error("No payloads loaded")
            return 1

        logger.info(f"Loaded {len(payloads)} payload(s)")

        # Validate and optionally wrap payloads
        messages = []
        for i, payload in enumerate(payloads):
            if not PayloadLoader.validate_payload(payload):
                logger.warning(f"Skipping invalid payload {i + 1}")
                continue

            if parsed_args.wrap:
                # Check if already a complete message
                if "id" not in payload:
                    message = PayloadLoader.wrap_payload(
                        payload,
                        producer=parsed_args.producer,
                    )
                else:
                    message = payload
            else:
                # Assume it's already a complete message
                message = payload

            messages.append(message)

        if not messages:
            logger.error("No valid messages to send")
            return 1

        logger.info(f"Prepared {len(messages)} message(s) for sending")

        # Send messages
        sender = MessageSender(Path(message_dir))
        responses = sender.send_messages(
            messages=messages,
            topic=parsed_args.topic,
            wait_response=parsed_args.wait_response,
            response_timeout=parsed_args.timeout,
            delay_between=parsed_args.delay,
        )

        logger.info(f"Sent {len(messages)} message(s)")
        if parsed_args.wait_response:
            logger.info(f"Received {len(responses)} response(s)")

        return 0

    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
