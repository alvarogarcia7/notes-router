#!/bin/bash

# Publisher Application
# Publishes a message to the NATS message bus and waits for confirmation

set -e

# Load configuration from YAML
CONFIG_FILE="${CONFIG_FILE:-../config.yaml}"
source "../config-loader.sh" 2>/dev/null || {
    # Fallback if config-loader.sh not found
    NATS_SERVER="localhost:4222"
    MESSAGE_DIR="/tmp/nats-poc-messages"
    SCHEMA_REGISTRY="file://./schemas"
}

# Load config values if config-loader was sourced
if [ -z "$NATS_SERVER" ]; then
    NATS_SERVER=$(get_nats_server "$CONFIG_FILE")
fi
if [ -z "$MESSAGE_DIR" ]; then
    MESSAGE_DIR=$(get_message_dir "$CONFIG_FILE")
fi
if [ -z "$SCHEMA_REGISTRY" ]; then
    SCHEMA_REGISTRY=$(get_schema_registry "$CONFIG_FILE")
fi

# Allow environment variables to override
NATS_SERVER="${NATS_SERVER:-localhost:4222}"
MESSAGE_DIR="${MESSAGE_DIR:-/tmp/nats-poc-messages}"
SCHEMA_REGISTRY="${SCHEMA_REGISTRY:-file://./schemas}"

MESSAGE_ID="msg_$(date +%s%N)"
INPUT_TOPIC="pipeline.message.input"
OUTPUT_TOPIC="pipeline.message.output"

# Create message directory if it doesn't exist
mkdir -p "$MESSAGE_DIR"

# Generate message payload
PAYLOAD="Hello from publisher at $(date '+%Y-%m-%d %H:%M:%S')"
PRODUCER="com.nats-poc.publisher/1.0"
MESSAGE_TYPE="greeting"
SCHEMA_URL="com.nats-poc.publisher/$MESSAGE_TYPE/1.0"

# Generate UUID (using date-based approach for compatibility)
UUID="$(uuidgen 2>/dev/null || python3 -c 'import uuid; print(uuid.uuid4())' 2>/dev/null || echo "msg_$(date +%s%N)")"

# Create JSON payload with nested structure
JSON_PAYLOAD=$(cat <<EOF
{
  "id": "$UUID",
  "payload": {
    "message": "$PAYLOAD"
  },
  "producer": "$PRODUCER",
  "schema": "$SCHEMA_URL"
}
EOF
)

echo "[PUBLISHER] Starting message publication..."
echo "[PUBLISHER] UUID: $UUID"
echo "[PUBLISHER] Payload: $PAYLOAD"
echo "[PUBLISHER] Producer: $PRODUCER"
echo "[PUBLISHER] Connecting to NATS at $NATS_SERVER"

# Publish message using nats CLI (would use this with real NATS)
# For PoC, we'll write to a file that the subscriber will read
PUBLISH_FILE="$MESSAGE_DIR/$INPUT_TOPIC.txt"
echo "$JSON_PAYLOAD" > "$PUBLISH_FILE"

echo "[PUBLISHER] Message published to $PUBLISH_FILE"
echo "[PUBLISHER] Waiting for response..."

# Wait for subscriber to process and return result
TIMEOUT=10
ELAPSED=0
RESULT_FILE="$MESSAGE_DIR/$OUTPUT_TOPIC.txt"

while [ ! -f "$RESULT_FILE" ] && [ $ELAPSED -lt $TIMEOUT ]; do
    sleep 0.5
    ELAPSED=$((ELAPSED + 1))
done

if [ -f "$RESULT_FILE" ]; then
    RESULT=$(cat "$RESULT_FILE")
    echo "[PUBLISHER] Received response:"
    echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "$RESULT"

    # Verify the message was processed (check for UUID in response)
    if [[ $RESULT == *"$UUID"* ]]; then
        echo "[PUBLISHER] ✓ Message confirmed and processed!"

        # Extract counter from response if available
        COUNTER=$(echo "$RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('payload', {}).get('counter', 'N/A'))" 2>/dev/null || echo "N/A")
        echo "[PUBLISHER] Counter: $COUNTER"

        # Clean up
        rm -f "$PUBLISH_FILE" "$RESULT_FILE"
        exit 0
    else
        echo "[PUBLISHER] ✗ Response doesn't match message ID"
        exit 1
    fi
else
    echo "[PUBLISHER] ✗ Timeout waiting for response"
    exit 1
fi
