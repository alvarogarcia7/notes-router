#!/usr/bin/env python3
"""
Message schema definitions and validation for NATS messages.
Defines structure for messages.10.raw topic with support for both
Google Keep and Apple Notes sources.
"""

from typing import Any, Dict, List, Optional, Tuple

# JSON Schema-like structure for messages.10.raw
MESSAGE_10_RAW_SCHEMA = {
    "title": "messages.10.raw",
    "description": "Raw note messages from publishers (Google Keep, Apple Notes)",
    "type": "object",
    "required": ["id", "note"],
    "properties": {
        "id": {
            "type": "string",
            "description": "Unique message ID (UUID)",
            "minLength": 1,
        },
        "source": {
            "type": "string",
            "description": "Source of the note (google-keep, apple-notes)",
            "enum": ["google-keep", "apple-notes"],
        },
        "note": {
            "type": "object",
            "description": "Note data object",
            "required": ["id", "title"],
            "properties": {
                "id": {
                    "type": ["string", "number"],
                    "description": "Note identifier from source",
                },
                "title": {
                    "type": "string",
                    "description": "Note title",
                },
                "text": {
                    "type": "string",
                    "description": "Note content",
                },
                "timestamps": {
                    "type": "object",
                    "description": "Timestamp information",
                    "properties": {
                        "created": {"type": "string"},
                        "edited": {"type": "string"},
                        "created_timestamp_ms": {"type": ["number", "string"]},
                    },
                },
            },
        },
        "date": {
            "type": ["string", "null"],
            "description": "Extracted date in YYYY-MM-DD format (optional)",
            "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
        },
        "filename": {
            "type": "string",
            "description": "Source filename (for Apple Notes)",
        },
    },
}


def validate_required_field(data: Dict[str, Any], field: str, field_type: type) -> Tuple[bool, Optional[str]]:
    """Validate a required field exists and has correct type."""
    if field not in data:
        return False, f"Missing required field: {field}"
    if not isinstance(data[field], field_type):
        actual_type = type(data[field]).__name__
        expected_type = field_type.__name__
        return False, f"Field '{field}' should be {expected_type}, got {actual_type}"
    return True, None


def validate_optional_field(
    data: Dict[str, Any], field: str, allowed_types: tuple
) -> Tuple[bool, Optional[str]]:
    """Validate an optional field (if present) has correct type."""
    if field not in data:
        return True, None
    if not isinstance(data[field], allowed_types):
        actual_type = type(data[field]).__name__
        type_names = ", ".join(t.__name__ for t in allowed_types)
        return False, f"Field '{field}' should be one of ({type_names}), got {actual_type}"
    return True, None


def validate_date_format(date_str: str) -> Tuple[bool, Optional[str]]:
    """Validate date is in YYYY-MM-DD format."""
    import re
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return False, f"Date '{date_str}' is not in YYYY-MM-DD format"
    return True, None


def validate_note_object(note: Any) -> Tuple[bool, Optional[str]]:
    """Validate the 'note' object structure."""
    if not isinstance(note, dict):
        return False, f"'note' should be an object, got {type(note).__name__}"

    # Check required fields
    if "id" not in note:
        return False, "Note is missing required field: id"
    if "title" not in note:
        return False, "Note is missing required field: title"

    # Check field types
    if not isinstance(note["title"], str):
        return False, f"Note 'title' should be string, got {type(note['title']).__name__}"

    return True, None


def validate_message_10_raw(message: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a message against the messages.10.raw schema.

    Args:
        message: Message data to validate

    Returns:
        Tuple of (is_valid, error_message)
        If valid, error_message is None
        If invalid, error_message explains the validation failure
    """
    if not isinstance(message, dict):
        return False, f"Message should be an object, got {type(message).__name__}"

    # Check required fields: id, note
    valid, error = validate_required_field(message, "id", str)
    if not valid:
        return False, error

    valid, error = validate_required_field(message, "note", dict)
    if not valid:
        return False, error

    # Validate note structure
    valid, error = validate_note_object(message["note"])
    if not valid:
        return False, error

    # Validate optional fields
    valid, error = validate_optional_field(message, "source", (str, type(None)))
    if not valid:
        return False, error
    if message.get("source") and message["source"] not in ("google-keep", "apple-notes"):
        return False, f"'source' should be 'google-keep' or 'apple-notes', got '{message['source']}'"

    valid, error = validate_optional_field(message, "filename", (str, type(None)))
    if not valid:
        return False, error

    valid, error = validate_optional_field(message, "date", (str, type(None)))
    if not valid:
        return False, error
    if message.get("date"):
        valid, error = validate_date_format(message["date"])
        if not valid:
            return False, error

    return True, None


def get_validation_errors(message: Dict[str, Any]) -> List[str]:
    """Get all validation errors for a message."""
    errors = []

    if not isinstance(message, dict):
        return [f"Message should be an object, got {type(message).__name__}"]

    # Check required fields
    if "id" not in message:
        errors.append("Missing required field: id")
    elif not isinstance(message["id"], str):
        errors.append(f"Field 'id' should be string, got {type(message['id']).__name__}")

    if "note" not in message:
        errors.append("Missing required field: note")
    elif not isinstance(message["note"], dict):
        errors.append(f"Field 'note' should be object, got {type(message['note']).__name__}")
    else:
        note = message["note"]
        if "id" not in note:
            errors.append("Note is missing required field: id")
        if "title" not in note:
            errors.append("Note is missing required field: title")
        elif not isinstance(note["title"], str):
            errors.append(f"Note 'title' should be string, got {type(note['title']).__name__}")

    # Check optional fields
    if "source" in message:
        if not isinstance(message["source"], str):
            errors.append(f"Field 'source' should be string, got {type(message['source']).__name__}")
        elif message["source"] not in ("google-keep", "apple-notes"):
            errors.append(f"Field 'source' should be 'google-keep' or 'apple-notes', got '{message['source']}'")

    if "filename" in message and not isinstance(message["filename"], str):
        errors.append(f"Field 'filename' should be string, got {type(message['filename']).__name__}")

    if "date" in message:
        if message["date"] is not None:
            if not isinstance(message["date"], str):
                errors.append(f"Field 'date' should be string or null, got {type(message['date']).__name__}")
            else:
                valid, error = validate_date_format(message["date"])
                if not valid:
                    errors.append(error)

    return errors
