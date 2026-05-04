#!/usr/bin/env python3
"""
Tests for message schema validation.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nats_subscriber.message_schema import (
    validate_message_10_raw,
    get_validation_errors,
)


class TestValidation:
    """Test message schema validation."""

    def test_valid_google_keep_message(self):
        """Test valid Google Keep message."""
        message = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "note": {
                "id": "123",
                "title": "Sample Note",
                "text": "Note content",
            },
            "date": "2026-05-01",
        }
        is_valid, error = validate_message_10_raw(message)
        assert is_valid, f"Expected valid, got error: {error}"
        assert error is None

    def test_valid_apple_notes_message(self):
        """Test valid Apple Notes message."""
        message = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "source": "apple-notes",
            "note": {
                "id": "98",
                "title": "Apple Note",
                "text": "Apple note content",
            },
            "filename": "Todo-23-3-98.json",
            "date": "2026-03-21",
        }
        is_valid, error = validate_message_10_raw(message)
        assert is_valid, f"Expected valid, got error: {error}"
        assert error is None

    def test_valid_message_without_optional_fields(self):
        """Test valid message without optional fields."""
        message = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "note": {
                "id": "123",
                "title": "Minimal Note",
            },
        }
        is_valid, error = validate_message_10_raw(message)
        assert is_valid, f"Expected valid, got error: {error}"
        assert error is None

    def test_missing_id(self):
        """Test message missing required id field."""
        message = {
            "note": {
                "id": "123",
                "title": "Note",
            },
        }
        is_valid, error = validate_message_10_raw(message)
        assert not is_valid
        assert "id" in error.lower()

    def test_missing_note(self):
        """Test message missing required note field."""
        message = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
        }
        is_valid, error = validate_message_10_raw(message)
        assert not is_valid
        assert "note" in error.lower()

    def test_note_missing_id(self):
        """Test note object missing required id field."""
        message = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "note": {
                "title": "Note",
            },
        }
        is_valid, error = validate_message_10_raw(message)
        assert not is_valid
        assert "id" in error.lower()

    def test_note_missing_title(self):
        """Test note object missing required title field."""
        message = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "note": {
                "id": "123",
            },
        }
        is_valid, error = validate_message_10_raw(message)
        assert not is_valid
        assert "title" in error.lower()

    def test_invalid_id_type(self):
        """Test id with wrong type."""
        message = {
            "id": 12345,  # Should be string
            "note": {
                "id": "123",
                "title": "Note",
            },
        }
        is_valid, error = validate_message_10_raw(message)
        assert not is_valid
        assert "id" in error.lower()

    def test_invalid_note_type(self):
        """Test note with wrong type."""
        message = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "note": "should be dict",  # Should be dict
        }
        is_valid, error = validate_message_10_raw(message)
        assert not is_valid
        assert "note" in error.lower()

    def test_invalid_source_value(self):
        """Test source with invalid enum value."""
        message = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "source": "unknown-source",
            "note": {
                "id": "123",
                "title": "Note",
            },
        }
        is_valid, error = validate_message_10_raw(message)
        assert not is_valid
        assert "source" in error.lower()

    def test_invalid_date_format(self):
        """Test date with invalid format."""
        message = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "note": {
                "id": "123",
                "title": "Note",
            },
            "date": "2026-05-01T10:00:00",  # Should be YYYY-MM-DD only
        }
        is_valid, error = validate_message_10_raw(message)
        assert not is_valid
        assert "date" in error.lower()

    def test_date_null_value(self):
        """Test date with null value (allowed)."""
        message = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "note": {
                "id": "123",
                "title": "Note",
            },
            "date": None,
        }
        is_valid, error = validate_message_10_raw(message)
        assert is_valid, f"Expected valid, got error: {error}"

    def test_source_null_value(self):
        """Test source with null value (allowed)."""
        message = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "source": None,
            "note": {
                "id": "123",
                "title": "Note",
            },
        }
        is_valid, error = validate_message_10_raw(message)
        assert is_valid, f"Expected valid, got error: {error}"

    def test_get_validation_errors_multiple(self):
        """Test getting multiple validation errors."""
        message = {
            # Missing id
            "note": "invalid",  # Wrong type
            "date": "invalid-date",
            "source": "invalid-source",
        }
        errors = get_validation_errors(message)
        assert len(errors) >= 3
        error_str = " ".join(errors).lower()
        assert "id" in error_str
        assert "note" in error_str
        assert "date" in error_str

    def test_complex_valid_message(self):
        """Test complex valid message with all fields."""
        message = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "source": "apple-notes",
            "note": {
                "id": "98",
                "title": "Complex Note",
                "text": "Note content with special chars: !@#$%",
                "timestamps": {
                    "created": "2026-03-21 16:05:27",
                    "edited": "2026-03-27 14:39:28",
                    "created_timestamp_ms": "1711033527000",
                },
            },
            "filename": "ComplexNote-26-3-98.json",
            "date": "2026-03-21",
        }
        is_valid, error = validate_message_10_raw(message)
        assert is_valid, f"Expected valid, got error: {error}"


def run_tests():
    """Run all tests."""
    test_class = TestValidation()
    test_methods = [method for method in dir(test_class) if method.startswith("test_")]

    passed = 0
    failed = 0

    for test_method in test_methods:
        try:
            getattr(test_class, test_method)()
            print(f"✓ {test_method}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_method}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_method}: Unexpected error: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed out of {passed + failed} tests")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    import sys

    sys.exit(run_tests())
