#!/usr/bin/env python3
"""Quick test script for Python subscriber message handler."""

import json
import sys
import tempfile
from pathlib import Path

# Add subscriber-python to path
sys.path.insert(0, "subscriber-python/src")

from nats_subscriber.message_handler import MessageHandler
from nats_subscriber.schema_loader import SchemaLoader


def main():
    """Run quick tests."""
    try:
        # Create temporary counter file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            counter_path = Path(f.name)

        # Initialize schema loader for validation
        schema_loader = SchemaLoader("file://./schemas")

        # Initialize handler with schema validation
        handler = MessageHandler(counter_path, schema_loader)

        # Create test messages in JSON format
        test_msg1 = json.dumps({
            "id": "msg-001-test",
            "payload": {
                "message": "Test message 1"
            },
            "producer": "com.test.producer/1.0",
            "schema": "com.test.producer/test/1.0"
        })

        test_msg2 = json.dumps({
            "id": "msg-002-test",
            "payload": {
                "message": "Test message 2"
            },
            "producer": "com.test.producer/1.0",
            "schema": "com.test.producer/test/1.0"
        })

        # Test message 1
        result1 = handler.process_message(test_msg1)
        assert result1 is not None, "Message 1 processing failed"
        result1_data = json.loads(result1)
        assert result1_data["payload"]["counter"] == 1, f"Counter mismatch in result1: {result1}"
        assert result1_data["payload"]["status"] == "PROCESSED", "Status should be PROCESSED"
        print("✓ Message 1 processed correctly: Counter=1")

        # Test message 2
        result2 = handler.process_message(test_msg2)
        assert result2 is not None, "Message 2 processing failed"
        result2_data = json.loads(result2)
        assert result2_data["payload"]["counter"] == 2, f"Counter mismatch in result2: {result2}"
        assert result2_data["payload"]["status"] == "PROCESSED", "Status should be PROCESSED"
        print("✓ Message 2 processed correctly: Counter=2")

        # Verify persistence
        handler2 = MessageHandler(counter_path)
        assert handler2.counter == 2, f"Counter persistence failed: {handler2.counter}"
        print("✓ Counter persistence verified")

        # Test invalid JSON
        invalid_msg = json.dumps({"payload": "missing required fields"})
        result_invalid = handler.process_message(invalid_msg)
        assert result_invalid is None, "Should reject message with missing fields"
        print("✓ Invalid message validation working")

        # Cleanup
        counter_path.unlink()

        print("\n✓ All Python tests passed!")
        return 0

    except Exception as e:
        print(f"✗ Test failed: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
