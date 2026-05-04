# NATS Agents Setup Guide

This document describes how to set up and run the NATS messaging agents (publisher and subscriber applications).

## Overview

The NATS PoC consists of two independent agents that communicate through a message broker:

- **Publisher Agent** - Generates and sends messages, waits for responses
- **Subscriber Agent** - Consumes messages, processes them, and sends results

## Prerequisites

### System Requirements

- bash 4.0 or later
- Linux/Unix operating system
- 10MB free disk space for message queue
- Basic POSIX utilities (cat, date, mkdir, etc.)

### Optional: Real NATS Server

For production use with actual NATS server:

```bash
# Install NATS CLI
curl -sf https://raw.githubusercontent.com/nats-io/natscli/main/install.sh | sh

# Install NATS server
curl -sf https://raw.githubusercontent.com/nats-io/nats-server/main/install.sh | sh

# Start NATS server
nats-server
```

## Installation

### 1. Clone or Navigate to Project

```bash
cd /path/to/nats-poc
```

### 2. Verify Scripts

```bash
ls -l
# Output should show:
# publisher.sh (executable)
# subscriber.sh (executable)
# test-poc.sh (executable)
# README.md
# AGENTS.md
```

### 3. Make Scripts Executable (if needed)

```bash
chmod +x publisher.sh subscriber.sh test-poc.sh
```

## Running the Agents

### Option 1: Automated Test (Recommended)

Runs all agents in orchestrated sequence:

```bash
bash test-poc.sh
```

**What it does:**
1. Starts subscriber in background
2. Publishes 3 test messages
3. Verifies all messages are processed
4. Shows final counter value
5. Cleans up gracefully

**Expected output:**
```
==========================================
NATS Message Queue Proof of Concept
==========================================

Step 1: Starting subscriber in background...
[...test execution...]
Final message counter: 3
```

### Option 2: Manual Setup

**Terminal 1: Start Subscriber**

```bash
bash subscriber.sh
```

**Output:**
```
[SUBSCRIBER] Starting subscriber...
[SUBSCRIBER] Connecting to NATS at localhost:4222
[SUBSCRIBER] Listening on topic: pipeline.message.input
[SUBSCRIBER] Publishing results to: pipeline.message.output
[SUBSCRIBER] Waiting for messages...
```

The subscriber will run indefinitely, processing incoming messages.

**Terminal 2: Run Publisher**

```bash
bash publisher.sh
```

**Output:**
```
[PUBLISHER] Starting message publication...
[PUBLISHER] Message ID: msg_1770193079221933877
[PUBLISHER] Message: Hello from publisher at 2026-02-04 08:17:59
[PUBLISHER] Connecting to NATS at localhost:4222
[PUBLISHER] Message published...
[PUBLISHER] Waiting for response...
[PUBLISHER] ✓ Message confirmed and processed!
[PUBLISHER] Final result: msg_1770193079221933877|PROCESSED|Counter: 1|...
```

**Terminal 3: Publish More Messages (Optional)**

Run the publisher multiple times to test message queue:

```bash
bash publisher.sh
bash publisher.sh
bash publisher.sh
```

Each should show incrementing counter values.

**Terminal 1: Stop Subscriber**

```
Ctrl+C
```

## Configuration

### Environment Variables

Both agents respect these environment variables:

```bash
# Set custom NATS server address (default: localhost:4222)
export NATS_SERVER="192.168.1.100:4222"
bash publisher.sh
bash subscriber.sh
```

### Message Directory

Messages are stored in:
```
/tmp/nats-poc-messages/
```

To use a different directory:

**In publisher.sh and subscriber.sh, modify:**
```bash
MESSAGE_DIR="/custom/path/messages"
```

## Agent Behavior

### Publisher Agent

**Lifecycle:**
1. Generate unique message ID (nanosecond precision)
2. Create message with timestamp
3. Publish to input topic
4. Poll for response (10 second timeout)
5. Verify message ID in response
6. Output success/failure
7. Clean up message files

**Exit Codes:**
- `0` - Success (message processed)
- `1` - Failure (timeout or verification error)

**Key Features:**
- Unique message IDs prevent duplicates
- Timeout protection prevents hanging
- Response verification ensures correct matching
- Automatic cleanup of temporary files

### Subscriber Agent

**Lifecycle:**
1. Initialize message counter (persisted to file)
2. Enter listen loop
3. Poll for incoming messages
4. When message received:
   - Parse message content
   - Increment counter
   - Create result with counter info
   - Publish result
   - Clean up input
5. Continue listening

**State Persistence:**
- Counter stored in `/tmp/nats-poc-messages/.message_counter`
- Survives subscriber restarts
- Increments sequentially for each message

**Key Features:**
- Continuous message processing
- Persistent counter across restarts
- Graceful shutdown (Ctrl+C)
- Detailed logging

## Message Flow

### Standard Flow

```
1. Publisher creates message
   ID: msg_1770193079221933877
   Content: "Hello from publisher..."

2. Publisher publishes to pipeline.message.input
   File: /tmp/nats-poc-messages/pipeline.message.input.txt

3. Subscriber detects message
   Reads: msg_1770193079221933877|Hello from publisher...

4. Subscriber processes
   Increments counter: 1
   Creates result with counter info

5. Subscriber publishes to pipeline.message.output
   File: /tmp/nats-poc-messages/pipeline.message.output.txt
   Result: msg_1770193079221933877|PROCESSED|Counter: 1|...

6. Publisher receives response
   Verifies message ID matches
   Confirms processing success

7. Cleanup
   Both sides delete temporary message files
```

### Message Format

**Input Message:**
```
MESSAGE_ID|MESSAGE_CONTENT
msg_1770193079221933877|Hello from publisher at 2026-02-04 08:17:59
```

**Output Result:**
```
MESSAGE_ID|PROCESSED|Counter: N|Content: MESSAGE_CONTENT
msg_1770193079221933877|PROCESSED|Counter: 1|Content: Hello from publisher at 2026-02-04 08:17:59
```

## Monitoring

### View Message Counter

```bash
cat /tmp/nats-poc-messages/.message_counter
# Output: 5 (number of messages processed)
```

### Check Subscriber Status

While subscriber is running:

```bash
# In another terminal
ps aux | grep subscriber.sh
# Shows active subscriber process
```

### Monitor Message Processing

Watch subscriber logs in real-time:

```bash
# Terminal 1
bash subscriber.sh 2>&1 | tee subscriber.log

# Terminal 2 (in another window)
tail -f subscriber.log
```

## Troubleshooting

### Publisher Timeout

**Error:** `Timeout waiting for response`

**Causes:**
- Subscriber not running
- Message directory not writable
- System clock issues

**Solution:**
```bash
# Verify subscriber is running
ps aux | grep subscriber.sh

# Check directory permissions
ls -ld /tmp/nats-poc-messages/

# Restart subscriber
bash subscriber.sh
```

### Message Verification Failure

**Error:** `Response doesn't match message ID`

**Causes:**
- Multiple publishers/subscribers interfering
- Message directory corruption

**Solution:**
```bash
# Clean up old messages
rm -rf /tmp/nats-poc-messages/
mkdir -p /tmp/nats-poc-messages/

# Restart agents
bash subscriber.sh &
bash publisher.sh
```

### Permission Denied

**Error:** `Permission denied`

**Solution:**
```bash
# Make scripts executable
chmod +x publisher.sh subscriber.sh test-poc.sh
```

## Performance

### Metrics

- **Message latency:** ~500ms (file-based PoC)
- **Messages/second:** ~2 (file-based PoC)
- **Memory usage:** <5MB per agent
- **CPU usage:** Minimal (polling every 500ms)

### Scalability

**File-based PoC limits:**
- Suitable for testing and development
- Not recommended for high-volume production use
- Sequential message processing

**Real NATS improvements:**
- Latency: <10ms
- Throughput: 1000s messages/second
- Memory efficient broker
- Concurrent message handling

## Production Deployment

### With Real NATS Server

1. **Install NATS:**
```bash
# Install nats-server
curl -sf https://raw.githubusercontent.com/nats-io/nats-server/main/install.sh | sh

# Start server
nats-server
```

2. **Update publisher.sh:**
```bash
# Replace file-based publish with:
nats pub "pipeline.message.input" "$MESSAGE"

# Replace file-based subscribe with:
nats request "pipeline.message.input" "$MESSAGE" --timeout 10s
```

3. **Update subscriber.sh:**
```bash
# Replace file-based listen with:
nats sub "pipeline.message.input" --raw | while read -r msg; do
    process_message "$msg"
    nats pub "pipeline.message.output" "$result"
done
```

### Supervisor Integration

**supervisord.conf example:**
```ini
[supervisord]
nodaemon=true

[program:nats]
command=/usr/bin/nats-server
autostart=true
autorestart=true

[program:subscriber]
command=/path/to/subscriber.sh
autostart=true
autorestart=true
depends_on=nats

[program:publisher]
command=/path/to/publisher.sh
autostart=true
autorestart=true
depends_on=nats
```

## Cleanup

### Remove Temporary Files

```bash
rm -rf /tmp/nats-poc-messages/
```

### Stop All Agents

```bash
pkill -f "publisher.sh"
pkill -f "subscriber.sh"
```

## Next Steps

1. **Test the setup:** Run `bash test-poc.sh`
2. **Understand the flow:** Read README.md
3. **Explore the code:** Review publisher.sh and subscriber.sh
4. **Customize:** Modify message format or processing logic
5. **Integrate NATS:** Adapt for real NATS server deployment

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review README.md for architecture details
3. Examine script logs with debug output
4. Check NATS documentation: https://docs.nats.io/

## References

- NATS Guide: nats-guide.adoc
- README: README.md
- NATS Documentation: https://docs.nats.io/
- NATS CLI: https://github.com/nats-io/natscli
