"""Tests for payload loader module."""

import json
import tempfile
from pathlib import Path

import pytest

from nats_subscriber.payload_loader import PayloadLoader


@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestPayloadLoader:
    """Test PayloadLoader class."""

    def test_load_single_object(self, temp_dir):
        """Test loading single object from JSON file."""
        payload = {"id": "msg-1", "message": "Hello"}
        file_path = temp_dir / "single.json"
        file_path.write_text(json.dumps(payload))

        result = PayloadLoader.load_file(str(file_path))
        assert result is not None
        assert len(result) == 1
        assert result[0] == payload

    def test_load_array(self, temp_dir):
        """Test loading array of objects from JSON file."""
        payloads = [
            {"id": "msg-1", "message": "Hello"},
            {"id": "msg-2", "message": "World"},
        ]
        file_path = temp_dir / "array.json"
        file_path.write_text(json.dumps(payloads))

        result = PayloadLoader.load_file(str(file_path))
        assert result is not None
        assert len(result) == 2
        assert result == payloads

    def test_load_file_not_found(self):
        """Test loading non-existent file."""
        result = PayloadLoader.load_file("/nonexistent/file.json")
        assert result is None

    def test_load_invalid_json(self, temp_dir):
        """Test loading invalid JSON file."""
        file_path = temp_dir / "invalid.json"
        file_path.write_text("{ invalid json }")

        result = PayloadLoader.load_file(str(file_path))
        assert result is None

    def test_load_invalid_type(self, temp_dir):
        """Test loading JSON file with invalid root type."""
        file_path = temp_dir / "invalid_type.json"
        file_path.write_text('"string"')

        result = PayloadLoader.load_file(str(file_path))
        assert result is None

    def test_load_multiple_files(self, temp_dir):
        """Test loading from multiple files."""
        file1 = temp_dir / "file1.json"
        file1.write_text(json.dumps([{"id": "msg-1"}]))

        file2 = temp_dir / "file2.json"
        file2.write_text(json.dumps({"id": "msg-2"}))

        result = PayloadLoader.load_files([str(file1), str(file2)])
        assert len(result) == 2

    def test_validate_complete_message(self):
        """Test validation of complete NATS message."""
        message = {
            "id": "uuid",
            "producer": "com.test/1.0",
            "schema": "com.test/test/1.0",
            "payload": {
                "message": "Hello"
            }
        }
        assert PayloadLoader.validate_payload(message)

    def test_validate_incomplete_message(self):
        """Test validation of incomplete message."""
        message = {
            "id": "uuid",
            "producer": "com.test/1.0",
            # Missing schema and payload
        }
        # Should not validate as complete, but wrap_payload will handle it
        result = PayloadLoader.validate_payload(message)
        assert result  # Still returns True (will be wrapped)

    def test_validate_content_only(self):
        """Test validation of content-only payload."""
        payload = {
            "message": "Hello"
        }
        assert PayloadLoader.validate_payload(payload)

    def test_wrap_payload_simple(self):
        """Test wrapping simple content in message envelope."""
        content = {"message": "Hello World"}

        result = PayloadLoader.wrap_payload(content)

        assert "id" in result
        assert result["producer"] == "com.nats-poc.cli/1.0"
        assert "schema" in result
        assert result["payload"]["message"] == "Hello World"

    def test_wrap_payload_with_custom_producer(self):
        """Test wrapping with custom producer."""
        content = {"message": "Hello"}
        producer = "com.custom.app/2.0"

        result = PayloadLoader.wrap_payload(content, producer=producer)

        assert result["producer"] == producer

    def test_wrap_payload_extract_text(self):
        """Test wrapping extracts text field."""
        content = {"text": "Hello from text field"}

        result = PayloadLoader.wrap_payload(content)

        assert result["payload"]["message"] == "Hello from text field"

    def test_wrap_payload_extract_content(self):
        """Test wrapping extracts content field."""
        content = {"content": "Hello from content field"}

        result = PayloadLoader.wrap_payload(content)

        assert result["payload"]["message"] == "Hello from content field"

    def test_wrap_payload_custom_message_id(self):
        """Test wrapping with custom message ID."""
        content = {"message": "Hello"}
        custom_id = "custom-id-123"

        result = PayloadLoader.wrap_payload(content, message_id=custom_id)

        assert result["id"] == custom_id

    def test_wrap_payload_message_type(self):
        """Test wrapping with custom message type."""
        content = {"message": "Hello"}
        message_type = "custom-type"

        result = PayloadLoader.wrap_payload(content, message_type=message_type)

        assert f"/{message_type}/" in result["schema"]
