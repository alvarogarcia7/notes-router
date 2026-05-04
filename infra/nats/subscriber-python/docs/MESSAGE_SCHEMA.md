# Message Schema for NATS Pipeline

## messages.10.raw — Raw Note Messages

Topic for raw note content from publishers (Google Keep, Apple Notes).

### Structure

```json
{
  "id": "uuid",
  "source": "google-keep|apple-notes",
  "note": {
    "id": "string|number",
    "title": "string",
    "text": "string",
    "timestamps": {
      "created": "string",
      "edited": "string",
      "created_timestamp_ms": "string|number"
    }
  },
  "filename": "string",
  "date": "YYYY-MM-DD|null"
}
```

### Field Definitions

#### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | string | Unique message identifier (UUID) | `"550e8400-e29b-41d4-a716-446655440000"` |
| `note` | object | Note data from source | See Note Object below |

#### Optional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `source` | string or null | Source of the note (`google-keep` or `apple-notes`) | `"apple-notes"` |
| `filename` | string | Source filename (typically for Apple Notes) | `"Todo-23-3-98.json"` |
| `date` | string or null | Extracted date in YYYY-MM-DD format (null if not found) | `"2026-05-01"` |

### Note Object

The `note` object contains the actual note data.

#### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | string or number | Note identifier from source | `"123"` or `98` |
| `title` | string | Note title | `"Training Session"` |

#### Optional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `text` | string | Note content/body | `"Bench press 2x30x13.6"` |
| `timestamps` | object | Timing information | See below |

### Timestamps Object

Optional metadata about note timing.

| Field | Type | Description |
|-------|------|-------------|
| `created` | string | Creation timestamp (format may vary by source) |
| `edited` | string | Last edit timestamp |
| `created_timestamp_ms` | string or number | Creation time in milliseconds since epoch |

## Examples

### Google Keep Note

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "note": {
    "id": "note-id-123",
    "title": "Training Session",
    "text": "☐ Bench press\n  ☐ 2x30x13.6\n  ☐ 2x15x22.1",
    "timestamps": {
      "created": "Monday, 1 January 2024 at 10:00:00",
      "created_timestamp_ms": "1704110400000"
    }
  },
  "date": "2024-01-01"
}
```

### Apple Notes

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "source": "apple-notes",
  "note": {
    "id": "98",
    "title": "Todo List",
    "text": "- Buy milk\n- Finish project\n- Schedule meeting",
    "timestamps": {
      "created": "Tuesday, 21 March 2023 at 16:05:27",
      "edited": "Monday, 27 March 2023 at 14:39:28"
    }
  },
  "filename": "Todo-23-3-98.json",
  "date": "2023-03-21"
}
```

### Minimal Valid Message

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "note": {
    "id": "note-456",
    "title": "Simple Note"
  }
}
```

## Validation Rules

### Type Validation
- `id` must be a non-empty string (UUID format recommended)
- `note` must be an object with required fields
- `source` if present must be "google-keep" or "apple-notes"
- `filename` if present must be a string
- `date` if present must be a string in YYYY-MM-DD format OR null

### Note Validation
- `note.id` is required (string or number)
- `note.title` is required (non-empty string)
- `note.text` optional (string)
- `note.timestamps` optional (object with optional fields)

### Date Format
Dates must be in ISO 8601 format: `YYYY-MM-DD`

Examples of valid dates:
- ✓ `"2026-05-01"`
- ✓ `"2023-03-21"`
- ✗ `"2026-5-1"` (missing leading zeros)
- ✗ `"05/01/2026"` (wrong format)
- ✗ `"2026-05-01T10:00:00"` (includes time)

## Router Processing

When messages arrive on `messages.10.raw`, the router:

1. **Validates** the message against this schema
2. **Rejects** messages that fail validation (logs error)
3. **Routes** valid messages to type-specific topics:
   - Training notes → `messages.20.type.training`
   - Time entry notes → `messages.20.type.time`
   - Next entry notes → `messages.20.type.next`
   - HackerNews notes → `messages.20.type.hn`

## Adding New Source Types

To support a new note source (e.g., `notion-notes`):

1. **Update schema**: Add enum value to `source` field
   ```
   "source": { "enum": ["google-keep", "apple-notes", "notion-notes"] }
   ```

2. **Update publisher**: Include `"source": "notion-notes"` in messages

3. **Update router**: Add parser for new type in `PARSER_TO_TYPE` mapping

4. **Update message_schema.py**: Modify validation for new source if needed

## Validation Implementation

### Python

```python
from nats_subscriber.message_schema import validate_message_10_raw, get_validation_errors

# Single error check
is_valid, error = validate_message_10_raw(message)
if not is_valid:
    print(f"Validation failed: {error}")

# Get all errors
errors = get_validation_errors(message)
for error in errors:
    print(f"Error: {error}")
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-05-02 | Initial schema with Google Keep and Apple Notes support |

## See Also

- Router Implementation: `project-router/nats-poc/subscriber-python/src/nats_subscriber/router.py`
- Tests: `project-router/nats-poc/subscriber-python/tests/test_message_schema.py`
- Google Keep Publisher: `google-keep-notes-parser/nats_publisher.py`
- Apple Notes Publisher: `notes-exporter/nats_publisher.py`
