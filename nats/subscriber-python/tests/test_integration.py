"""Integration tests for the full message pipeline."""

import json
import tempfile
from pathlib import Path

import pytest

from nats_subscriber.payload_loader import PayloadLoader
from nats_subscriber.message_handler import MessageHandler
from nats_subscriber.message_sender import MessageSender
from nats_subscriber.schema_loader import SchemaLoader


@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def schema_loader():
    """Create a schema loader."""
    return SchemaLoader("file://./schemas")


@pytest.fixture
def sample_payload():
    """Create a sample payload."""
    return {"message": "Integration test message"}


class TestEndToEndPipeline:
    """Test complete message pipeline: load → send → process → respond."""

    def test_load_and_send_single_payload(self, temp_dir, sample_payload):
        """Test loading payload and sending it."""
        # Create payload file
        payload_file = temp_dir / "payload.json"
        payload_file.write_text(json.dumps(sample_payload))

        # Load payload
        payloads = PayloadLoader.load_file(str(payload_file))
        assert payloads is not None
        assert len(payloads) == 1
        assert payloads[0]["message"] == "Integration test message"

        # Wrap payload
        message = PayloadLoader.wrap_payload(payloads[0])
        assert "id" in message
        assert "producer" in message
        assert "schema" in message
        assert "payload" in message
        assert message["payload"]["message"] == "Integration test message"

        # Send message
        sender = MessageSender(temp_dir)
        sender.send_message(message, topic="test.integration.input", wait_response=False)

        # Verify file was created
        message_file = temp_dir / "test.integration.input.txt"
        assert message_file.exists()

    def test_load_and_send_multiple_payloads(self, temp_dir):
        """Test loading multiple payloads from array."""
        # Create payload file
        payloads = [
            {"message": "Message 1"},
            {"message": "Message 2"},
            {"message": "Message 3"},
        ]
        payload_file = temp_dir / "payloads.json"
        payload_file.write_text(json.dumps(payloads))

        # Load payloads
        loaded = PayloadLoader.load_file(str(payload_file))
        assert loaded is not None
        assert len(loaded) == 3

        # Wrap and send
        messages = [PayloadLoader.wrap_payload(p) for p in loaded]
        sender = MessageSender(temp_dir)

        responses = sender.send_messages(
            messages,
            topic="test.batch.input",
            wait_response=False,
        )

        assert len(responses) == 0  # No responses expected
        message_file = temp_dir / "test.batch.input.txt"
        assert message_file.exists()

    def test_message_processing_workflow(self, temp_dir, schema_loader):
        """Test processing message through handler."""
        # Create a message
        message = {
            "id": "msg-integration-001",
            "producer": "com.nats-poc.cli/1.0",
            "schema": "com.nats-poc.cli/test/1.0",
            "payload": {"message": "Processing test"}
        }

        # Create counter file
        counter_file = temp_dir / ".message_counter"
        handler = MessageHandler(counter_file, schema_loader)

        # Process message
        result = handler.process_message(json.dumps(message))
        assert result is not None

        result_data = json.loads(result)
        assert result_data["id"] == "msg-integration-001"
        assert result_data["payload"]["status"] == "PROCESSED"
        assert result_data["payload"]["counter"] == 1
        assert "payload" in result_data["payload"]  # Has nested payload from processing

    def test_full_send_and_receive_cycle(self, temp_dir, schema_loader):
        """Test sending message and receiving response."""
        message_content = {"message": "Full cycle test"}

        # Step 1: Load and wrap payload
        payloads = [message_content]
        messages = [PayloadLoader.wrap_payload(p) for p in payloads]

        assert len(messages) == 1
        sent_message = messages[0]
        message_id = sent_message["id"]

        # Step 2: Send message
        sender = MessageSender(temp_dir)
        sender.send_message(sent_message, topic="test.cycle.input", wait_response=False)

        # Step 3: Create response (simulating subscriber)
        counter_file = temp_dir / ".message_counter"
        handler = MessageHandler(counter_file, schema_loader)
        response = handler.process_message(json.dumps(sent_message))

        # Step 4: Write response to output file
        response_file = temp_dir / "test.cycle.output.txt"
        response_file.write_text(response)

        # Step 5: Verify response
        response_data = json.loads(response)
        assert response_data["id"] == message_id
        assert response_data["payload"]["status"] == "PROCESSED"
        assert response_data["payload"]["counter"] == 1

    def test_multi_file_loading_and_batch_send(self, temp_dir, schema_loader):
        """Test loading from multiple files and batch sending."""
        # Create multiple payload files
        file1_path = temp_dir / "batch1.json"
        file1_path.write_text(json.dumps([
            {"message": "Batch 1 - Message 1"},
            {"message": "Batch 1 - Message 2"},
        ]))

        file2_path = temp_dir / "batch2.json"
        file2_path.write_text(json.dumps({"message": "Batch 2 - Single message"}))

        # Load from multiple files
        all_payloads = PayloadLoader.load_files([str(file1_path), str(file2_path)])
        assert len(all_payloads) == 3

        # Wrap all
        messages = [PayloadLoader.wrap_payload(p) for p in all_payloads]

        # Send as batch with delay
        sender = MessageSender(temp_dir)
        responses = sender.send_messages(
            messages,
            topic="test.multi.input",
            wait_response=False,
            delay_between=0.05,
        )

        message_file = temp_dir / "test.multi.input.txt"
        assert message_file.exists()

    def test_validation_across_pipeline(self, temp_dir):
        """Test validation at each pipeline stage."""
        payload = {"message": "Validation test"}

        # Validate payload
        assert PayloadLoader.validate_payload(payload)

        # Wrap payload
        message = PayloadLoader.wrap_payload(payload)

        # Validate wrapped message
        assert PayloadLoader.validate_payload(message)

        # Verify all required fields
        assert "id" in message
        assert "producer" in message
        assert "schema" in message
        assert "payload" in message
        assert isinstance(message["payload"], dict)
        assert "message" in message["payload"]

    def test_error_recovery_in_pipeline(self, temp_dir):
        """Test error handling and recovery in pipeline."""
        sender = MessageSender(temp_dir)

        # Test with invalid message structure
        result = sender.send_message(
            None,
            topic="test.error.input",
            wait_response=False,
        )
        # Should handle gracefully
        assert result is None

        # Verify invalid message didn't create file
        message_file = temp_dir / "test.error.input.txt"
        assert not message_file.exists()

    def test_complete_message_passthrough(self, temp_dir, schema_loader):
        """Test passing complete message through pipeline."""
        complete_message = {
            "id": "msg-complete-123",
            "producer": "com.test.app/1.0",
            "schema": "com.test.app/message/1.0",
            "payload": {
                "message": "Complete message test"
            }
        }

        # Validate complete message
        assert PayloadLoader.validate_payload(complete_message)

        # Send it
        sender = MessageSender(temp_dir)
        sender.send_message(complete_message, topic="test.complete.input")

        message_file = temp_dir / "test.complete.input.txt"
        assert message_file.exists()

        # Read back and verify
        stored = json.loads(message_file.read_text())
        assert stored == complete_message
