#!/usr/bin/env python3
"""
NATS Router for Apple Notes
Routes messages.10.raw.type.applenotes to appropriate messages.20.* topics based on type detection.
"""

import asyncio
import json
import os
import ssl
import sys
import uuid
from pathlib import Path

import nats

# Add parser paths for type detection
_repo_root = Path(__file__).parent.parent
_hn_parser_path = _repo_root / "parsers" / "hn"
_training_parser_path = _repo_root / "parsers" / "training"
_time_parser_path = _repo_root / "parsers" / "time"
_next_parser_path = _repo_root / "parsers" / "next"

for parser_path in [_hn_parser_path, _training_parser_path, _time_parser_path, _next_parser_path]:
    src_path = parser_path / "src"
    if src_path.exists() and str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

try:
    from hackernews_parser import HackerNewsParser
except ImportError:
    HackerNewsParser = None

try:
    from time_entry_parser import TimeEntryParser
except ImportError:
    TimeEntryParser = None

try:
    from training_parser import TrainingParser
except ImportError:
    TrainingParser = None

# Note: Next entry parser may have different import path
try:
    from next_entry_parser import NextEntryParser
except ImportError:
    NextEntryParser = None

NATS_URL = os.environ.get("NATS_URL")
if not NATS_URL:
    print("Error: NATS_URL environment variable not set")
    sys.exit(1)

CERTS_DIR = os.environ.get("CERTS_DIR", "/tmp/nats-certs")
INPUT_TOPIC = "messages.10.raw.type.applenotes"

# Topic mapping: parser type → output topic
TYPE_TO_TOPIC = {
    "hackernews": "messages.20.hn",
    "time": "messages.20.time",
    "training": "messages.20.training",
    "next": "messages.20.next",
}


def _make_ssl_ctx() -> ssl.SSLContext:
    """Create SSL context with client certificate for mTLS."""
    ctx = ssl.create_default_context()
    ctx.load_verify_locations(cafile=f"{CERTS_DIR}/rootCA.pem")
    ctx.load_cert_chain(
        certfile=f"{CERTS_DIR}/client.pem",
        keyfile=f"{CERTS_DIR}/client.key"
    )
    return ctx


def _detect_message_type(note: dict) -> str:
    """Detect message type using available parsers."""
    # Try HackerNews
    if HackerNewsParser:
        try:
            parser = HackerNewsParser()
            if parser.can_parse(note):
                return "hackernews"
        except Exception:
            pass

    # Try Training
    if TrainingParser:
        try:
            parser = TrainingParser()
            if parser.can_parse(note):
                return "training"
        except Exception:
            pass

    # Try Time Entry
    if TimeEntryParser:
        try:
            parser = TimeEntryParser()
            if parser.can_parse(note):
                return "time"
        except Exception:
            pass

    # Try Next Entry
    if NextEntryParser:
        try:
            parser = NextEntryParser()
            if parser.can_parse(note):
                return "next"
        except Exception:
            pass

    # Default to generic Apple Notes
    return "applenotes"


async def _connect_with_retry(url: str) -> nats.aio.client.Client:
    """Connect to NATS with retry logic and TLS."""
    ssl_ctx = _make_ssl_ctx()
    for attempt in range(5):
        try:
            return await nats.connect(url, tls=ssl_ctx, connect_timeout=2)
        except Exception as e:
            if attempt < 4:
                print(f"Connection attempt {attempt + 1}/5 failed, retrying in 1s...")
                await asyncio.sleep(1)
            else:
                print(f"Error: Could not connect to NATS at {url} after 5 attempts")
                print(f"Make sure NATS server is running: {e}")
                sys.exit(1)


async def route_apple_notes(input_msg: dict, client: nats.aio.client.Client) -> None:
    """Route Apple Notes to appropriate topic based on type detection."""
    original_note = input_msg.get("note", {})
    title = original_note.get("title", "Untitled")

    # Detect message type
    msg_type = _detect_message_type(original_note)

    # Get output topic
    output_topic = TYPE_TO_TOPIC.get(msg_type, "messages.20.other.applenotes")

    # Create routed message
    routed_message = {
        "id": input_msg.get("id", str(uuid.uuid4())),
        "message_type": msg_type,
        "note": {
            "id": original_note.get("id", str(uuid.uuid4())),
            "title": title,
            "text": original_note.get("text"),
            "url": original_note.get("url"),
            "date": input_msg.get("date"),
        },
        "source": "apple-notes"
    }

    await client.publish(output_topic, json.dumps(routed_message).encode())
    print(f"✓ Routed to '{msg_type}' ({output_topic}): {title}")


async def main() -> None:
    """Subscribe to messages.10.raw.type.applenotes and route appropriately."""
    nc = await _connect_with_retry(NATS_URL)

    print(f"🔄 Apple Notes Router started")
    print(f"  Input topic:  {INPUT_TOPIC}")
    print(f"  Output topics:")
    for msg_type, topic in TYPE_TO_TOPIC.items():
        print(f"    - {msg_type}: {topic}")
    print(f"    - default: messages.20.other.applenotes")

    try:
        async def handler(msg):
            try:
                message_data = json.loads(msg.data.decode())
                await route_apple_notes(message_data, nc)
            except json.JSONDecodeError as e:
                print(f"✗ Failed to decode message: {e}")
            except Exception as e:
                print(f"✗ Error processing message: {e}")

        await nc.subscribe(INPUT_TOPIC, cb=handler)
        await asyncio.Future()  # run forever

    except KeyboardInterrupt:
        print("\n✓ Router stopped")
    finally:
        await nc.close()


if __name__ == "__main__":
    asyncio.run(main())
