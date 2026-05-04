"""Tests for CLI module."""

import json
import tempfile
from pathlib import Path

import pytest

from nats_subscriber.cli import main


@pytest.fixture
def temp_message_dir():
    """Create a temporary message directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_json_file():
    """Create a sample JSON payload file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"message": "Test message"}, f)
        temp_path = f.name
    yield temp_path
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def sample_array_json_file():
    """Create a sample JSON array file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([
            {"message": "Message 1"},
            {"message": "Message 2"},
        ], f)
        temp_path = f.name
    yield temp_path
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


class TestCLI:
    """Test CLI module."""

    def test_cli_basic_send(self, sample_json_file, temp_message_dir):
        """Test basic message sending via CLI."""
        args = [
            sample_json_file,
            "--message-dir", str(temp_message_dir),
            "--wrap",
        ]
        result = main(args)
        assert result == 0

    def test_cli_multiple_files(self, sample_json_file, sample_array_json_file, temp_message_dir):
        """Test sending from multiple files."""
        args = [
            sample_json_file,
            sample_array_json_file,
            "--message-dir", str(temp_message_dir),
            "--wrap",
        ]
        result = main(args)
        assert result == 0

    def test_cli_custom_topic(self, sample_json_file, temp_message_dir):
        """Test sending to custom topic."""
        args = [
            sample_json_file,
            "--topic", "custom.topic.input",
            "--message-dir", str(temp_message_dir),
            "--wrap",
        ]
        result = main(args)
        assert result == 0
        # Verify message was sent to custom topic
        message_file = temp_message_dir / "custom.topic.input.txt"
        assert message_file.exists()

    def test_cli_with_custom_producer(self, sample_json_file, temp_message_dir):
        """Test sending with custom producer."""
        args = [
            sample_json_file,
            "--producer", "com.test.producer/1.0",
            "--message-dir", str(temp_message_dir),
            "--wrap",
        ]
        result = main(args)
        assert result == 0

    def test_cli_with_delay(self, sample_array_json_file, temp_message_dir):
        """Test sending with delay between messages."""
        args = [
            sample_array_json_file,
            "--delay", "0.1",
            "--message-dir", str(temp_message_dir),
            "--wrap",
        ]
        result = main(args)
        assert result == 0

    def test_cli_nonexistent_file(self, temp_message_dir):
        """Test handling of nonexistent file."""
        args = [
            "/nonexistent/file.json",
            "--message-dir", str(temp_message_dir),
        ]
        result = main(args)
        assert result == 1

    def test_cli_invalid_json(self, temp_message_dir):
        """Test handling of invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{invalid json")
            temp_path = f.name

        try:
            args = [
                temp_path,
                "--message-dir", str(temp_message_dir),
            ]
            result = main(args)
            assert result == 1
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_cli_with_help(self):
        """Test CLI help output."""
        args = ["--help"]
        with pytest.raises(SystemExit) as exc_info:
            main(args)
        # Help should exit with 0
        assert exc_info.value.code == 0

    def test_cli_complete_message_no_wrap(self, temp_message_dir):
        """Test sending complete message without wrap."""
        complete_msg = {
            "id": "msg-test-123",
            "producer": "com.test/1.0",
            "schema": "com.test/message/1.0",
            "payload": {"message": "Test"}
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(complete_msg, f)
            temp_path = f.name

        try:
            args = [
                temp_path,
                "--message-dir", str(temp_message_dir),
            ]
            result = main(args)
            assert result == 0
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_cli_log_level_debug(self, sample_json_file, temp_message_dir):
        """Test CLI with DEBUG log level."""
        args = [
            sample_json_file,
            "--log-level", "DEBUG",
            "--message-dir", str(temp_message_dir),
            "--wrap",
        ]
        result = main(args)
        assert result == 0

    def test_cli_custom_timeout(self, sample_json_file, temp_message_dir):
        """Test CLI with custom response timeout."""
        args = [
            sample_json_file,
            "--timeout", "5",
            "--message-dir", str(temp_message_dir),
            "--wrap",
        ]
        result = main(args)
        assert result == 0
