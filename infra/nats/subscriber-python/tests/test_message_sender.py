"""Tests for message sender module."""

import json
import tempfile
from pathlib import Path

import pytest

from nats_subscriber.message_sender import MessageSender


@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sender(temp_dir):
    """Create a MessageSender instance."""
    return MessageSender(temp_dir)


@pytest.fixture
def sample_message():
    """Create a sample NATS message."""
    return {
        "id": "msg-123",
        "producer": "com.test/1.0",
        "schema": "com.test/test/1.0",
        "payload": {
            "message": "Hello World"
        }
    }


class TestMessageSender:
    """Test MessageSender class."""

    def test_send_message_creates_file(self, sender, sample_message):
        """Test that send_message creates message file."""
        topic = "test.topic.input"

        sender.send_message(sample_message, topic=topic, wait_response=False)

        message_file = sender.message_dir / f"{topic}.txt"
        assert message_file.exists()

        stored_message = json.loads(message_file.read_text())
        assert stored_message == sample_message

    def test_send_message_returns_none_without_response(self, sender, sample_message):
        """Test send_message returns None when not waiting for response."""
        result = sender.send_message(sample_message, wait_response=False)
        assert result is None

    def test_send_message_with_response(self, sender, temp_dir, sample_message):
        """Test send_message with response waiting."""
        topic = "test.topic.input"

        # Create a response file
        response = {
            "id": "msg-123",
            "producer": "com.subscriber/1.0",
            "schema": "com.subscriber/response/1.0",
            "payload": {
                "message": "Processed",
                "status": "PROCESSED",
                "counter": 1
            }
        }
        response_file = temp_dir / f"{topic.replace('input', 'output')}.txt"
        response_file.write_text(json.dumps(response))

        result = sender.send_message(sample_message, topic=topic, wait_response=True, response_timeout=2)

        assert result is not None
        assert result["id"] == "msg-123"
        assert result["payload"]["status"] == "PROCESSED"

    def test_send_message_timeout(self, sender, sample_message):
        """Test send_message timeout when no response."""
        result = sender.send_message(sample_message, wait_response=True, response_timeout=1)
        assert result is None

    def test_send_message_wrong_response_id(self, sender, temp_dir, sample_message):
        """Test handling of response with wrong message ID."""
        topic = "test.topic.input"

        # Create response with different ID
        response = {
            "id": "different-id",
            "payload": {"message": "Response"}
        }
        response_file = temp_dir / f"{topic.replace('input', 'output')}.txt"
        response_file.write_text(json.dumps(response))

        result = sender.send_message(sample_message, topic=topic, wait_response=True, response_timeout=1)

        assert result is None

    def test_send_messages_multiple(self, sender):
        """Test sending multiple messages."""
        messages = [
            {"id": f"msg-{i}", "payload": {"message": f"Message {i}"}}
            for i in range(3)
        ]

        responses = sender.send_messages(messages, wait_response=False)

        assert len(responses) == 0  # No responses expected
        message_file = sender.message_dir / "pipeline.message.input.txt"
        assert message_file.exists()

    def test_send_messages_with_delay(self, sender):
        """Test sending messages with delay."""
        messages = [
            {"id": "msg-1", "payload": {"message": "Message 1"}},
            {"id": "msg-2", "payload": {"message": "Message 2"}},
        ]

        # Should not raise error with delay
        responses = sender.send_messages(messages, delay_between=0.1)

        assert isinstance(responses, list)

    def test_message_dir_created(self):
        """Test that message directory is created if not exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            message_dir = Path(tmpdir) / "nonexistent" / "nested" / "dir"

            sender = MessageSender(message_dir)

            assert message_dir.exists()

    def test_send_message_error_handling(self, sender):
        """Test error handling when message is invalid."""
        # This should not raise an exception
        result = sender.send_message(None)
        # Error is logged, None is returned
        assert result is None
