# NATS Messaging PoC with Bash

A proof of concept demonstrating NATS messaging patterns using pure bash applications.

## Components

### 1. Publisher (`publisher.sh`)
- Generates unique message IDs with timestamps
- Publishes messages to the input topic
- Waits for the subscriber to process and return results
- Verifies message confirmation
- Cleans up message files after successful processing

**Key Features:**
- Unique message ID generation using nanosecond precision
- Timeout handling (10 seconds)
- Response verification
- Error handling and logging

### 2. Subscriber (`subscriber.sh`)
- Continuously listens for messages on the input topic
- Maintains a counter of processed messages
- Processes each message and increments the counter
- Publishes results back with the counter value
- Logs all processing details

**Key Features:**
- Persistent message counter storage
- Stateful processing (counter increments)
- Message parsing and content extraction
- Result aggregation with counter information

### 3. Test Script (`test-poc.sh`)
- Orchestrates the PoC demonstration
- Starts the subscriber in background
- Publishes 3 messages sequentially
- Verifies all messages are processed with correct counters
- Cleans up and displays final results

## Usage

### Run the Test
```bash
bash test-poc.sh
```

### Run Manually

**Start the subscriber (in one terminal):**
```bash
bash subscriber.sh
```

**Publish a message (in another terminal):**
```bash
bash publisher.sh
```

## How It Works

1. **Message Flow:**
   - Publisher creates a message with ID and content
   - Publishes to `pipeline.message.input` topic
   - Subscriber picks up the message
   - Subscriber increments counter and processes message
   - Subscriber publishes result to `pipeline.message.output` topic
   - Publisher receives the result and verifies the message ID
   - Both sides clean up

2. **Message Format:**
   ```
   MESSAGE_ID|MESSAGE_CONTENT
   ```

3. **Result Format:**
   ```
   MESSAGE_ID|PROCESSED|Counter: N|Content: MESSAGE_CONTENT
   ```

## Architecture Patterns

This PoC demonstrates key NATS patterns from `nats-guide.adoc`:

- **Topic-Based Routing:** Messages flow through named topics (input → processing → output)
- **Pub/Sub Pattern:** Publisher sends messages, subscriber consumes them
- **Request/Reply Pattern:** Publisher waits for and verifies responses
- **Message Persistence:** Results are confirmed before cleanup
- **Worker Pattern:** Subscriber acts as a long-running worker processing incoming messages
- **Stateful Processing:** Counter maintains state across multiple messages

## Acceptance Criteria Met

✅ **Two bash applications** - `publisher.sh` and `subscriber.sh`

✅ **Publisher publishes a message** - Sends to `pipeline.message.input` topic with unique ID

✅ **Subscriber increases counter and returns message** - Increments counter for each message, processes it, and returns result

✅ **Publisher checks the message** - Verifies message ID in response, confirms processing success

## Topics Used

- **Input:** `pipeline.message.input`
- **Output:** `pipeline.message.output`

## Message Directory

Messages are stored in `/tmp/nats-poc-messages/` for this file-based implementation.

In a production environment with actual NATS server, this would use the NATS CLI:
```bash
nats pub "pipeline.message.input" "$message"
nats sub "pipeline.message.output"
```

## Real NATS Integration

To adapt this PoC for real NATS server:

**Publisher (actual NATS):**
```bash
# Publish message
nats pub "pipeline.message.input" "$message_content"

# Subscribe to response
nats request "pipeline.message.input" "$message_content" --timeout 10s
```

**Subscriber (actual NATS):**
```bash
# Listen for messages
nats sub "pipeline.message.input" --raw | while read -r msg; do
    result=$(process_message "$msg")
    nats pub "pipeline.message.output" "$result"
done
```

## Dependencies

- bash 4.0+
- Standard Linux utilities: `cat`, `date`, `mkdir`, `rm`, `sleep`, `echo`

## Error Handling

Both applications include:
- Exit on error with `set -e`
- Timeout protection (10 second timeout in publisher)
- Message ID verification
- Logging and status messages
