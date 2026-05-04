# Message Schemas

This directory contains JSON Schema definitions for all NATS message topics in the notes processing pipeline.

## Directory Structure

### Stage 1: Raw Messages (`stage1/`)

Raw messages from publishers before type detection.

- `messages.10.raw.type.googlenotes.json` — Google Keep raw messages
- `messages.10.raw.type.applenotes.json` — Apple Notes raw messages

**Topic Pattern**: `messages.10.raw.type.{source}`

### Stage 2: Routed Messages (`stage2/`)

Messages after router type detection, organized by detected type.

- `messages.20.time.json` — Time entries (meetings, time tracking)
- `messages.20.hn.json` — HackerNews items (links, articles)
- `messages.20.training.json` — Training sessions (workouts, courses)
- `messages.20.next.json` — Next entries (goals, TODOs, actions)

**Topic Pattern**: `messages.20.{type}`

### Stage 3: Parsed Results (`stage3/`)

Fully parsed and enriched messages from specialized parsers.

- `messages.30.type.time.10.parsed.json` — Parsed time entries
- `messages.30.type.hn.10.parsed.json` — Parsed HackerNews items
- `messages.30.type.training.10.parsed.json` — Parsed training sessions
- `messages.30.type.next.10.parsed.json` — Parsed next entries

**Topic Pattern**: `messages.30.type.{type}.10.parsed`

## Using These Schemas

### Validation

Use JSON Schema validators to validate messages:

```bash
# Using ajv-cli
ajv validate -s schemas/stage2/messages.20.time.json -d message.json

# Using jsonschema (Python)
jsonschema -i message.json schemas/stage2/messages.20.time.json
```

### Integration

Include schema validation in:
- Publishers (before publishing to stage1 topics)
- Routers (before routing to stage2 topics)
- Parsers (before publishing parsed results to stage3 topics)
- Writers (before persisting to files)

### Extension

To add a new message type:

1. Create stage2 schema: `schemas/stage2/messages.20.{type}.json`
2. Create stage3 schema: `schemas/stage3/messages.30.type.{type}.10.parsed.json`
3. Update parsers/routers to validate against new schemas
4. Update this README

## Schema Validation in Code

### Python Example

```python
import json
import jsonschema

def validate_message(message: dict, schema_path: str) -> bool:
    with open(schema_path) as f:
        schema = json.load(f)
    
    try:
        jsonschema.validate(message, schema)
        return True
    except jsonschema.ValidationError as e:
        print(f"Validation error: {e.message}")
        return False
```

### Node.js Example

```javascript
const Ajv = require('ajv');
const ajv = new Ajv();

function validateMessage(message, schemaPath) {
  const schema = require(schemaPath);
  const validate = ajv.compile(schema);
  
  if (!validate(message)) {
    console.log('Validation errors:', validate.errors);
    return false;
  }
  return true;
}
```

## Common Fields

All messages share these base fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique message identifier (UUID) |
| `title` | string | Message title or subject |
| `content` | string | Message content body |
| `source` | string | Original source (googlenotes/applenotes) |
| `type` | string | Message type (time/hn/training/next) |
| `timestamp` | string | ISO 8601 original message timestamp |

Stage 3 messages additionally include:

| Field | Type | Description |
|-------|------|-------------|
| `parsed_at` | string | ISO 8601 parse timestamp |

## Future Extensions

Planned schema additions:

- `messages.20.other.*` — Generic/untyped messages
- Custom type schemas for new parsers
- Schema versioning for backward compatibility
- OpenAPI/Swagger definitions for REST APIs
