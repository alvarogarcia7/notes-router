#!/bin/bash

# Subscriber Application
# Subscribes to incoming messages, increments counter, and publishes result

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

INPUT_TOPIC="pipeline.message.input"
OUTPUT_TOPIC="pipeline.message.output"
COUNTER_FILE="$MESSAGE_DIR/.message_counter"

# Create message directory if it doesn't exist
mkdir -p "$MESSAGE_DIR"

# Initialize counter if it doesn't exist
if [ ! -f "$COUNTER_FILE" ]; then
    echo "0" > "$COUNTER_FILE"
fi

echo "[SUBSCRIBER] Starting subscriber..."
echo "[SUBSCRIBER] Connecting to NATS at $NATS_SERVER"
echo "[SUBSCRIBER] Listening on topic: $INPUT_TOPIC"
echo "[SUBSCRIBER] Publishing results to: $OUTPUT_TOPIC"
echo "[SUBSCRIBER] Schema Registry: $SCHEMA_REGISTRY"

# In a real NATS environment, this would be:
# nats sub "$INPUT_TOPIC" --raw | while read -r msg; do
#     process_message "$msg"
# done

# For PoC, we'll poll for messages
PUBLISH_FILE="$MESSAGE_DIR/$INPUT_TOPIC.txt"

while true; do
    if [ -f "$PUBLISH_FILE" ]; then
        # Read the message
        MESSAGE=$(cat "$PUBLISH_FILE")
        echo "[SUBSCRIBER] Received message:"
        echo "$MESSAGE" | python3 -m json.tool 2>/dev/null || echo "$MESSAGE"

        # Parse JSON message
        MESSAGE_ID=$(echo "$MESSAGE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('id', 'unknown'))" 2>/dev/null || echo "unknown")
        PAYLOAD_MESSAGE=$(echo "$MESSAGE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('payload', {}).get('message', ''))" 2>/dev/null || echo "")
        PRODUCER=$(echo "$MESSAGE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('producer', 'unknown'))" 2>/dev/null || echo "")

        # Increment counter
        COUNTER=$(cat "$COUNTER_FILE")
        COUNTER=$((COUNTER + 1))
        echo "$COUNTER" > "$COUNTER_FILE"

        echo "[SUBSCRIBER] Processing message #$COUNTER"
        echo "[SUBSCRIBER] Message ID: $MESSAGE_ID"
        echo "[SUBSCRIBER] Producer: $PRODUCER"
        echo "[SUBSCRIBER] Payload: $PAYLOAD_MESSAGE"

        # Create JSON result with counter information nested in payload
        RESULT=$(cat <<EOF
{
  "id": "$MESSAGE_ID",
  "producer": "com.nats-poc.subscriber/1.0",
  "schema": "com.nats-poc.subscriber/response/1.0",
  "payload": {
    "message": "$PAYLOAD_MESSAGE",
    "status": "PROCESSED",
    "counter": $COUNTER
  }
}
EOF
)

        # Publish result
        RESULT_FILE="$MESSAGE_DIR/$OUTPUT_TOPIC.txt"
        echo "$RESULT" > "$RESULT_FILE"
        echo "[SUBSCRIBER] Result published to $RESULT_FILE"

        # Clean up input file
        rm -f "$PUBLISH_FILE"

        echo "[SUBSCRIBER] Message #$COUNTER processed successfully"
        echo "---"
    fi

    sleep 0.5
done
