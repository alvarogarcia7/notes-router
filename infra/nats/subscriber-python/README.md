# NATS Subscriber - Python Implementation

A professional Python implementation of the NATS message subscriber application with message counter and processing.

## Overview

This is a Python port of the bash subscriber, demonstrating best practices for Python project structure and development workflows. It follows the boilerplate patterns for organization, testing, and tooling.

## Project Structure

```
subscriber-python/
├── src/
│   └── nats_subscriber/
│       ├── __init__.py              # Package initialization
│       ├── config.py                # Configuration management
│       ├── main.py                  # Entry point
│       ├── message_handler.py       # Message processing logic
│       ├── subscriber.py            # Subscriber implementation
│       ├── payload_loader.py        # JSON payload loading & wrapping
│       ├── message_sender.py        # Message sending to topics
│       ├── schema_loader.py         # Schema loading & validation
│       ├── config_loader.py         # YAML configuration loading
│       └── cli.py                   # Command-line interface
├── tests/
│   ├── __init__.py
│   ├── fixtures/                    # Test fixture files
│   ├── test_message_handler.py      # Unit tests
│   ├── test_payload_loader.py       # Payload loading tests
│   ├── test_message_sender.py       # Message sending tests
│   ├── test_cli.py                  # CLI interface tests
│   └── test_integration.py          # End-to-end pipeline tests
├── .github/
│   └── workflows/                   # CI/CD configuration
├── Makefile                         # Development tasks
├── README.md                        # This file
├── pyproject.toml                   # Project metadata
└── requirements.txt                 # Minimal dependencies
```

## Installation

### Prerequisites

- Python 3.8+
- pip

### Setup

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Or install minimal dependencies
pip install -r requirements.txt
```

## Usage

### Run Subscriber

```bash
# Using Python module
python -m nats_subscriber.main

# Using installed command (after pip install -e)
nats-subscriber

# Using Makefile
make run
```

### Load and Send JSON Payloads

The new payload loading and message sending tool allows you to load JSON payloads from files and send them as NATS messages:

```bash
# Send single payload
python -m nats_subscriber.cli payloads.json --wrap

# Send multiple files
python -m nats_subscriber.cli file1.json file2.json file3.json --wrap

# Send to custom topic
python -m nats_subscriber.cli payloads.json --topic custom.topic.input --wrap

# Send with response waiting
python -m nats_subscriber.cli payloads.json --wait-response --timeout 10 --wrap

# Send with delay between messages
python -m nats_subscriber.cli payloads.json --delay 0.5 --wrap

# Send with custom producer
python -m nats_subscriber.cli payloads.json --producer com.myapp/1.0 --wrap

# Send with debug logging
python -m nats_subscriber.cli payloads.json --log-level DEBUG --wrap

# Use custom message directory
python -m nats_subscriber.cli payloads.json --message-dir /custom/path --wrap

# Help
python -m nats_subscriber.cli --help
```

#### Payload Formats

The tool supports multiple payload formats:

**Single JSON Object:**
```json
{
  "message": "Hello World"
}
```

**Array of Objects:**
```json
[
  {"message": "First message"},
  {"message": "Second message"},
  {"message": "Third message"}
]
```

**Complete NATS Message (no wrapping needed):**
```json
{
  "id": "msg-123",
  "producer": "com.app/1.0",
  "schema": "com.app/message/1.0",
  "payload": {
    "message": "Already formatted"
  }
}
```

#### Output

When sending, the tool:
1. Loads payloads from JSON files (single objects or arrays)
2. Validates payload structure
3. Wraps plain payloads in NATS message envelopes with UUID, producer, and schema
4. Sends messages to the specified topic
5. Optionally waits for subscriber responses
6. Logs detailed information about each step

### Configuration

Control behavior with environment variables:

```bash
# Custom NATS server
export NATS_SERVER="192.168.1.100:4222"

# Custom message directory
export MESSAGE_DIR="/custom/path/messages"

# Polling interval (seconds)
export POLL_INTERVAL="0.5"

# Logging level
export LOG_LEVEL="DEBUG"

# Then run
python -m nats_subscriber.main
```

## Development

### Run Tests

```bash
# Using pytest directly
pytest

# Using Makefile
make test

# With coverage
pytest --cov=src tests
```

### Code Quality

```bash
# Lint code
make lint

# Format code (black + isort)
make format

# Type checking
make type-check

# Run all checks
make lint format type-check
```

### Clean Up

```bash
# Remove temporary files
make clean
```

## Message Format

### Input Message

```
MESSAGE_ID|MESSAGE_CONTENT
msg_1770193079221933877|Hello from publisher at 2026-02-04 08:17:59
```

### Output Result

```
MESSAGE_ID|PROCESSED|Counter: N|Content: MESSAGE_CONTENT
msg_1770193079221933877|PROCESSED|Counter: 1|Content: Hello from publisher at 2026-02-04 08:17:59
```

## Architecture

### Main Components

**MessageHandler (`message_handler.py`)**
- Parses incoming messages
- Manages persistent message counter
- Creates result messages with counter info
- Validates messages against schemas
- Type-safe with structured data classes

**Subscriber (`subscriber.py`)**
- Polls for incoming messages
- Delegates processing to MessageHandler
- Handles file I/O (input/output)
- Manages subscriber lifecycle

**Config (`config.py`)**
- Centralized configuration management
- Environment variable support
- Type hints for configuration values

**Main (`main.py`)**
- Application entry point
- Logging setup
- Error handling

**PayloadLoader (`payload_loader.py`)**
- Loads JSON payloads from single or multiple files
- Supports both single objects and arrays
- Validates payload structure
- Wraps payloads in NATS message envelopes
- Generates UUIDs for message IDs
- Supports custom producers and message types

**MessageSender (`message_sender.py`)**
- Sends messages to NATS topics (file-based in PoC)
- Supports single message or batch sending
- Optional delay between sends
- Response waiting with configurable timeout
- Validates response message IDs

**SchemaLoader (`schema_loader.py`)**
- Loads JSON schemas from file:// or HTTP/S locations
- Caches schemas locally for performance
- Validates messages against schemas
- Supports schema references like "com.app/message/1.0"

**CLI (`cli.py`)**
- Command-line interface for the payload sender
- Argument parsing with sensible defaults
- Logging configuration
- Comprehensive error handling and reporting
- Supports all PayloadLoader and MessageSender features

### Message Processing Flow

```
1. Read message from input file
   └─> nats_subscriber/subscriber.py:_read_message()

2. Parse message (ID|Content)
   └─> nats_subscriber/message_handler.py:parse_message()

3. Increment counter
   └─> nats_subscriber/message_handler.py:increment_counter()

4. Create result with counter info
   └─> nats_subscriber/message_handler.py:create_result()

5. Write result to output file
   └─> nats_subscriber/subscriber.py:_write_result()

6. Cleanup input file
   └─> nats_subscriber/subscriber.py:_cleanup_input()
```

## Testing

The project includes unit tests for core functionality:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_message_handler.py

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=src tests --cov-report=html
```

### Test Coverage

**Unit Tests:**
- Message parsing (valid, invalid, edge cases)
- Counter persistence across restarts
- Result message creation
- Payload loading from files (single objects, arrays)
- Payload validation (required fields, structure)
- Message wrapping in NATS envelopes
- Message sending to topics
- Response waiting and timeout behavior
- CLI argument parsing and execution

**Integration Tests:**
- End-to-end payload loading and sending
- Batch processing with multiple files
- Message processing and response generation
- Full send → process → respond cycle
- Validation at each pipeline stage
- Error recovery and handling

**Test Files:**
- `test_message_handler.py` - Message processing
- `test_payload_loader.py` - Payload loading and wrapping
- `test_message_sender.py` - Message sending
- `test_cli.py` - Command-line interface
- `test_integration.py` - End-to-end pipelines

## Comparing with Bash Implementation

| Feature | Bash | Python |
|---------|------|--------|
| Type Safety | None | Type hints throughout |
| Testing | Manual | Automated unit tests |
| Configuration | Env vars | Structured config class |
| Error Handling | Basic | Comprehensive |
| Code Organization | Single file | Modular packages |
| Development Tools | Minimal | Make, pytest, mypy, black |
| Maintainability | Moderate | High |
| Performance | Very fast | Fast (small overhead) |

## Complete Message Flow Examples

### Using Bash Publisher with Python Subscriber

```bash
# Terminal 1: Start Python subscriber
python -m nats_subscriber.main

# Terminal 2: Run bash publisher (from parent directory)
../publisher/publisher.sh

# Terminal 3 (optional): Publish more messages
../publisher/publisher.sh
```

### Using Python Payload Loader and Sender

**1. Create a payload file:**
```json
{
  "message": "Hello from Python payload loader"
}
```

**2. Send it:**
```bash
python -m nats_subscriber.cli payloads.json --wrap
```

**3. In another terminal, run subscriber to process:**
```bash
python -m nats_subscriber.main
```

### Batch Processing Multiple Payloads

**1. Create multiple payload files:**

`batch1.json`:
```json
[
  {"message": "Batch 1 - Message 1"},
  {"message": "Batch 1 - Message 2"}
]
```

`batch2.json`:
```json
{
  "message": "Batch 2 - Single message"
}
```

**2. Send all files with delay:**
```bash
python -m nats_subscriber.cli batch1.json batch2.json --delay 0.5 --wrap
```

The tool will:
1. Load 3 total payloads (2 from batch1, 1 from batch2)
2. Wrap each in a NATS message envelope
3. Send them to the topic with 0.5 second delay between sends
4. Log progress for each step

**3. Monitor subscriber processing:**
```bash
# Terminal: Run subscriber
python -m nats_subscriber.main
# Will process all 3 messages with incrementing counter
```

## Logging Output

The Python subscriber provides detailed logging:

```
[INFO] Starting subscriber...
[INFO] Connecting to NATS at localhost:4222
[INFO] Listening on topic: pipeline.message.input
[INFO] Publishing results to: pipeline.message.output
[INFO] Received message: msg_1770193079221933877|Hello from publisher...
[INFO] Processing message #1
[INFO] Message ID: msg_1770193079221933877
[INFO] Message Content: Hello from publisher...
[INFO] Result published to /tmp/nats-poc-messages/pipeline.message.output.txt
[INFO] Message #1 processed successfully
```

## Dependencies

### Production
- `nats-py>=2.6.0` - Official NATS Python client

### Development
- `pytest>=7.0` - Testing framework
- `pytest-cov>=4.0` - Coverage reporting
- `black>=23.0` - Code formatter
- `isort>=5.0` - Import sorter
- `flake8>=6.0` - Linter
- `mypy>=1.0` - Type checker

## Future Enhancements

- [ ] Real NATS server integration (replace file-based I/O)
- [ ] Async implementation with asyncio
- [ ] Distributed counter using Redis/NATS
- [ ] Message batching
- [ ] Dead letter queue handling
- [ ] Metrics and monitoring
- [ ] Docker support
- [ ] CI/CD pipeline integration

## References

- NATS Documentation: https://docs.nats.io/
- nats-py: https://github.com/nats-io/nats.py
- Python Boilerplate: https://github.com/alvarogarcia7/python-boilerplate
- PEP 8: https://www.python.org/dev/peps/pep-0008/
- Type Hints: https://www.python.org/dev/peps/pep-0484/
