#!/bin/bash

# Test script for NATS PoC
# Runs the subscriber in background and publishes messages

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MESSAGE_DIR="/tmp/nats-poc-messages"

echo "=========================================="
echo "NATS Message Queue Proof of Concept"
echo "=========================================="
echo ""

# Clean up any previous test files
rm -rf "$MESSAGE_DIR"
mkdir -p "$MESSAGE_DIR"

echo "Step 1: Starting subscriber in background..."
"$SCRIPT_DIR/subscriber/subscriber.sh" &
SUBSCRIBER_PID=$!
echo "Subscriber PID: $SUBSCRIBER_PID"
sleep 1

echo ""
echo "Step 2: Publishing first message..."
"$SCRIPT_DIR/publisher/publisher.sh"

echo ""
echo "Step 3: Publishing second message..."
"$SCRIPT_DIR/publisher/publisher.sh"

echo ""
echo "Step 4: Publishing third message..."
"$SCRIPT_DIR/publisher/publisher.sh"

# Clean up
echo ""
echo "=========================================="
echo "Terminating subscriber..."
kill $SUBSCRIBER_PID 2>/dev/null || true
sleep 1

echo "Test completed successfully!"
echo "=========================================="

# Show final counter
COUNTER_FILE="$MESSAGE_DIR/.message_counter"
if [ -f "$COUNTER_FILE" ]; then
    FINAL_COUNT=$(cat "$COUNTER_FILE")
    echo "Final message counter: $FINAL_COUNT"
fi
