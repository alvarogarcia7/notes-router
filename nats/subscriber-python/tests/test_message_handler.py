"""Tests for message handler module."""

import json
import tempfile
from pathlib import Path

import pytest

from nats_subscriber.message_handler import MessageHandler, MAIN_SCHEMA_REF
from nats_subscriber.schema_loader import SchemaLoader


@pytest.fixture
def temp_counter_file():
    """Create a temporary counter file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        counter_path = Path(f.name)
    yield counter_path
    # Cleanup
    if counter_path.exists():
        counter_path.unlink()


@pytest.fixture
def sample_json_message():
    """Create a sample JSON message."""
    return json.dumps({
        "id": "msg-123-uuid",
        "payload": {
            "message": "Hello from test"
        },
        "producer": "com.test.producer/1.0",
        "schema": "com.test.producer/greeting/1.0"
    })


@pytest.fixture
def schema_loader():
    """Create a schema loader for testing."""
    return SchemaLoader("file://./schemas")


def test_counter_initialization(temp_counter_file):
    """Test counter initializes correctly."""
    handler = MessageHandler(temp_counter_file)
    assert handler.counter == 0


def test_counter_increment(temp_counter_file):
    """Test counter increments and persists."""
    handler = MessageHandler(temp_counter_file)

    # Increment counter
    result = handler.increment_counter()
    assert result == 1
    assert handler.counter == 1

    # Verify persistence
    handler2 = MessageHandler(temp_counter_file)
    assert handler2.counter == 1


def test_json_message_parsing(sample_json_message):
    """Test JSON message parsing."""
    handler = MessageHandler(Path("/tmp/dummy"))

    # Valid JSON message
    parsed = handler.parse_message(sample_json_message)
    assert parsed is not None
    assert parsed["id"] == "msg-123-uuid"
    assert parsed["payload"]["message"] == "Hello from test"
    assert parsed["producer"] == "com.test.producer/1.0"
    assert parsed["schema"] == "com.test.producer/greeting/1.0"

    # Invalid JSON
    parsed = handler.parse_message("invalid json")
    assert parsed is None


def test_missing_required_fields():
    """Test validation of required fields."""
    handler = MessageHandler(Path("/tmp/dummy"))

    # Missing 'id' field
    incomplete_msg = json.dumps({
        "payload": "test",
        "producer": "com.test/1.0",
        "schema": "com.test/type/1.0"
    })
    parsed = handler.parse_message(incomplete_msg)
    assert parsed is None


def test_result_creation(temp_counter_file, sample_json_message, schema_loader):
    """Test JSON result creation with counter."""
    handler = MessageHandler(temp_counter_file, schema_loader)
    handler.increment_counter()

    message = handler.parse_message(sample_json_message)
    result = handler.create_result(message)

    # Parse result to verify structure
    assert result is not None, "Result should not be None"
    result_data = json.loads(result)
    assert result_data["id"] == "msg-123-uuid"
    assert result_data["payload"]["status"] == "PROCESSED"
    assert result_data["payload"]["counter"] == 1
    assert result_data["producer"] == "com.nats-poc.subscriber/1.0"
    assert result_data["schema"] == "com.nats-poc.subscriber/response/1.0"
    assert result_data["payload"]["message"] == "Hello from test"


def test_full_message_processing(temp_counter_file, sample_json_message, schema_loader):
    """Test full message processing workflow."""
    handler = MessageHandler(temp_counter_file, schema_loader)

    # Process first message
    result1 = handler.process_message(sample_json_message)
    assert result1 is not None
    result1_data = json.loads(result1)
    assert result1_data["payload"]["counter"] == 1
    assert result1_data["payload"]["status"] == "PROCESSED"

    # Process second message with different ID
    sample_msg2 = json.dumps({
        "id": "msg-456-uuid",
        "payload": {
            "message": "Second message"
        },
        "producer": "com.test.producer/1.0",
        "schema": "com.test.producer/greeting/1.0"
    })
    result2 = handler.process_message(sample_msg2)
    assert result2 is not None
    result2_data = json.loads(result2)
    assert result2_data["payload"]["counter"] == 2
    assert result2_data["id"] == "msg-456-uuid"

    # Verify counter persisted
    handler2 = MessageHandler(temp_counter_file, schema_loader)
    assert handler2.counter == 2
