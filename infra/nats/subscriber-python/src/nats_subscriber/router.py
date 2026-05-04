#!/usr/bin/env python3
"""
NATS Router - routes messages from google-keep-notes-parser to type-specific topics.
Requires google-keep-notes-parser parsers to be available.
"""

import asyncio
import json
import os
import ssl
import sys
import uuid
from pathlib import Path

from nats_subscriber.nats_client import NATSClient
from nats_subscriber.message_schema import validate_message_10_raw, get_validation_errors

# Add parser paths for imports
# Path: router.py is at src/nats_subscriber/, need to go to repo root
_repo_root = Path(__file__).parent.parent.parent.parent.parent.parent
_google_keep_path = _repo_root / "google-keep-notes-parser"
_time_entry_path = _repo_root / "time-entry-notes-parser" / "src"
_next_path = _repo_root / "notes-parser-next-entry" / "src"
if str(_google_keep_path) not in sys.path:
    sys.path.insert(0, str(_google_keep_path))
# Add time-entry-notes-parser/src for the shim to use
if str(_time_entry_path) not in sys.path:
    sys.path.insert(0, str(_time_entry_path))
# Add notes-parser-next-entry/src for the shim to use
if str(_next_path) not in sys.path:
    sys.path.insert(0, str(_next_path))

try:
    from parsers.base import ParserRegistry
    from parsers.hackernews_parser import HackerNewsParser
    from parsers.training_parser import TrainingParser
    from parsers.next_parser import NextParser
    from parsers.generic_notes_parser import GenericNotesParser
    from parsers.time_entry_parser import TimeEntryParser
except ImportError as e:
    print(f"Error: Could not import parsers: {e}")
    print(f"Expected google-keep-notes-parser at: {_google_keep_path}")
    print(f"Expected time-entry-notes-parser/src at: {_time_entry_path}")
    print(f"Expected notes-parser-next-entry/src at: {_next_path}")
    sys.exit(1)

NATS_URL = os.environ.get("NATS_URL")
if not NATS_URL:
    print("Error: NATS_URL environment variable not set")
    sys.exit(1)
CERTS_DIR = os.environ.get("CERTS_DIR", "/tmp/nats-certs")
INPUT_TOPIC = "messages.10.raw"


def _make_ssl_ctx() -> ssl.SSLContext:
    """Create SSL context with client certificate for mTLS."""
    ctx = ssl.create_default_context()
    ctx.load_verify_locations(cafile=f"{CERTS_DIR}/rootCA.pem")
    ctx.load_cert_chain(
        certfile=f"{CERTS_DIR}/client.pem",
        keyfile=f"{CERTS_DIR}/client.key"
    )
    return ctx

TYPE_TO_TOPIC = {
    "training": "messages.20.type.training",
    "time": "messages.20.type.time",
    "next": "messages.20.type.next",
    "hackernews": "messages.20.type.hn",
}

PARSER_TO_TYPE = {
    TrainingParser: "training",
    TimeEntryParser: "time",
    NextParser: "next",
    HackerNewsParser: "hackernews",
}

# Abbreviation to full name mappings for training parser
EXERCISE_ABBREVIATIONS = {
    'Bp': 'Bench press',
    'Mr': 'Machine Row',
    'Ms': 'Machine Squat',
    'Sq': 'Squat',
    'Dl': 'Deadlift',
    'Pu': 'Pull-up',
    'Dip': 'Dip',
    'Row': 'Row',
    'Curl': 'Curl',
    'Press': 'Press',
    'Ribp': 'Ribbed Pull',
    'M pec fly': 'Machine Pec Fly',
}


def preprocess_training_note(text: str, note: dict = None) -> str:
    """Convert Google Keep checkbox format to ANTLR4 format.

    Transforms:
        ☐ Bp
          ☐ 2x30x13.6
          ☐ 2x15x22.1
        ☐ Mr
          ☐ 2x20x26

    Into:
        2026-01-23
        Bench press: 2x30x13.6, 2x15x22.1
        Machine Row: 2x20x26
    """
    # Extract date from note timestamps if available
    date_str = ""
    if note and "timestamps" in note and "edited" in note["timestamps"]:
        # Extract just the date part (YYYY-MM-DD)
        timestamp = note["timestamps"]["edited"]
        date_str = timestamp.split()[0]  # "2026-01-23 02:00:49..." -> "2026-01-23"

    lines = text.split('\n')
    result = []
    if date_str:
        result.append(date_str)

    current_exercise = None
    current_sets = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Remove checkbox symbol
        stripped = stripped.replace('☐', '').strip()
        if not stripped:
            continue

        # Check if this is an exercise name (abbreviation)
        is_exercise = False
        for abbr, full_name in EXERCISE_ABBREVIATIONS.items():
            if stripped == abbr or stripped.startswith(abbr + ' '):
                is_exercise = True
                if current_exercise and current_sets:
                    result.append(f"{current_exercise}: {', '.join(current_sets)}")
                current_exercise = full_name
                current_sets = []
                break

        # If not an exercise, treat as a set (e.g., "2x30x13.6")
        if not is_exercise and current_exercise is not None:
            if 'x' in stripped:  # Looks like a set format
                current_sets.append(stripped)

    # Append last exercise
    if current_exercise and current_sets:
        result.append(f"{current_exercise}: {', '.join(current_sets)}")

    return '\n'.join(result)


def setup_registry() -> ParserRegistry:
    """Create and setup parser registry."""
    registry = ParserRegistry()
    registry.register(HackerNewsParser)
    registry.register(TimeEntryParser)
    registry.register(TrainingParser)
    registry.register(NextParser)
    registry.register(GenericNotesParser)
    return registry


async def route_message(message_data: dict, client: NATSClient, registry: ParserRegistry) -> None:
    """Route a message to the appropriate topic based on type."""
    note = message_data.get("note", {})

    for parser_class in registry.get_all_parsers():
        parser = parser_class()
        if parser.can_parse(note):
            note_type = PARSER_TO_TYPE.get(parser_class)
            if not note_type:
                print(f"⚠ No topic mapping for {parser_class.__name__}")
                return

            topic = TYPE_TO_TOPIC.get(note_type)
            if not topic:
                print(f"⚠ No topic configured for type '{note_type}'")
                return

            # Preprocess training notes to convert Google Keep format to ANTLR4 format
            note_to_send = note.copy()
            if note_type == "training":
                note_to_send["text"] = preprocess_training_note(note.get("text", ""), note)

            routed_message = {
                "id": message_data.get("id", str(uuid.uuid4())),
                "type": note_type,
                "note": note_to_send,
            }

            await client.publish(topic, json.dumps(routed_message).encode())
            print(f"✓ Routed to '{note_type}' ({topic}): {note.get('title', 'Untitled')}")
            return

    print(f"⚠ No parser found for note: {note.get('title', 'Untitled')}")


async def main() -> None:
    """Subscribe to messages.10.raw and route to type-specific topics."""
    registry = setup_registry()

    async with NATSClient(url=NATS_URL, tls=_make_ssl_ctx()) as client:
        print(f"🔄 Router started, listening on '{INPUT_TOPIC}'...")

        async def handler(msg):
            try:
                message_data = json.loads(msg.data.decode())

                # Validate message against schema
                is_valid, error = validate_message_10_raw(message_data)
                if not is_valid:
                    print(f"✗ Message validation failed: {error}")
                    print(f"  Message structure: {json.dumps(message_data, indent=2)[:200]}...")
                    return

                await route_message(message_data, client, registry)
            except json.JSONDecodeError as e:
                print(f"✗ Failed to decode message: {e}")
            except Exception as e:
                print(f"✗ Error processing message: {e}")

        await client.subscribe(INPUT_TOPIC, cb=handler)
        await asyncio.Future()  # run forever


def main_sync() -> None:
    """Entry point for script execution."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✓ Router stopped")


if __name__ == "__main__":
    main_sync()
