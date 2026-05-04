# Notes Routing Architecture

## Overview

The notes-router implements a multi-stage NATS-based pipeline that processes notes from various sources (Google Keep, Apple Notes, and others) through type detection, specialized parsing, and persistent storage.

## Architecture Stages

### Stage 1: Publishers
Extract notes from various sources and publish to raw message topics.

**Sources:**
- **Google Keep** → `keep-it-markdown` (importers/google-keep)
- **Apple Notes** → `notes-exporter` (importers/apple-notes)
- **Any other source** → Can be added to importers/

**Output Topics:**
- `messages.10.raw.type.googlenotes`
- `messages.10.raw.type.applenotes`

### Stage 2: Router
Detects message type and routes to appropriate type-specific topic.

**Router Components:**
- `routers/google_notes_router.py` - Processes Google Keep notes
- `routers/apple_notes_router.py` - Processes Apple Notes

**Type Detection:**
- Time entries (meeting notes, time tracking)
- HackerNews items (link collections, tech news)
- Training sessions (learning resources, workshops)
- Next entries (upcoming items, goals, TODOs)

**Output Topics:**
- `messages.20.time`
- `messages.20.hn`
- `messages.20.training`
- `messages.20.next`
- `messages.20.other.*` (for unmatched content)

### Stage 3: Parsers
Specialized parsers process each message type.

**Parser Repositories (git submodules):**
- **Time Parser** → `parsers/time/notes-parser-time-entry`
- **HackerNews Parser** → `parsers/hn/google-keep-notes-parser`
- **Training Parser** → `parsers/training/training-parser-antlr4`
- **Next Parser** → `parsers/next/notes-parser-next-entry`

**Input Topics:**
- `messages.20.time`
- `messages.20.hn`
- `messages.20.training`
- `messages.20.next`

**Output Topics:**
- `messages.30.type.time.10.parsed`
- `messages.30.type.hn.10.parsed`
- `messages.30.type.training.10.parsed`
- `messages.30.type.next.10.parsed`

### Stage 4: Writers
Persist parsed messages to the filesystem.

**Output Location:**
```
/tmp/nats/$TOPIC_ID/$MESSAGE_ID.json
```

Example:
```
/tmp/nats/messages.30.type.time.10/uuid-123456.json
/tmp/nats/messages.30.type.hn.10/uuid-789012.json
```

## Complete Message Flow

```
Publishers
│
├─ Google Keep (keep-it-markdown)
├─ Apple Notes (notes-exporter)
└─ Any Other Source
│
↓ (NATS Stage 1)
│
messages.10.raw.type.{source}
│
↓ (Router Type Detection)
│
Router
├─ Detects content type (time, HN, training, next)
└─ Routes to type-specific topic
│
↓ (NATS Stage 2)
│
messages.20.{type}
│
↓ (Parser)
│
├─ Time Parser
├─ HackerNews Parser
├─ Training Parser
└─ Next Parser
│
↓ (NATS Stage 3)
│
messages.30.type.{type}.10.parsed
│
↓ (Writer)
│
/tmp/nats/messages.30.type.{type}.10/$ID.json
```

## Infrastructure

### NATS Server
**Location:** `infra/nats/`

**Features:**
- Mutual TLS (mTLS) security with certificate verification
- Automatic certificate generation via `gen-certs.sh`
- Configuration in `nats-server.conf`

**Management:**
```bash
make nats-up      # Start NATS server
make nats-down    # Stop NATS server
make nats-status  # Check NATS status
make gen-certs    # Generate TLS certificates
```

### Configuration

All components use:
- **NATS_URL:** Environment variable (default: `tls://localhost:4222`)
- **CERTS_DIR:** Directory containing TLS certificates
  - Required files: `client.pem`, `client.key`, `rootCA.pem`

## Benefits

1. **Modular Architecture**
   - Each parser is independent and self-contained
   - Easy to add new sources and parser types

2. **Type-Specific Processing**
   - Each message type handled by specialized parser
   - Optimized algorithms per content type

3. **Source Agnostic**
   - Router detects type regardless of source
   - Same time entry logic for Google Keep or Apple Notes

4. **Persistent Storage**
   - All parsed messages stored as JSON files
   - Organized by type for easy querying

5. **Observable Pipeline**
   - Raw messages preserved in Stage 1 for inspection
   - Each stage has clear NATS topics for monitoring

## Running the Pipeline

### Start Infrastructure
```bash
# From notes-router root
make nats-up
```

### Start Routers
```bash
# From routers/ directory
python3 google_notes_router.py
python3 apple_notes_router.py
```

### Start Parsers
```bash
# From parsers/ subdirectories
cd parsers/time && make listener-time
cd parsers/hn && make listener-hn
cd parsers/training && make listener-training
cd parsers/next && make listener-next
```

### Publish Notes
Publish notes from Google Keep or Apple Notes importers to trigger pipeline processing.

### Monitor Messages
```bash
# View raw messages
nats sub "messages.10.raw.*"

# View routed messages by type
nats sub "messages.20.*"

# View parsed results
nats sub "messages.30.type.*"
```

## Future Enhancements

- Add additional note sources (OneNote, Notion, Evernote)
- Implement cross-type message correlation
- Add metadata enrichment in routers (NLP, categorization)
- Create message indexing service for parsed results
- Add real-time dashboard for pipeline monitoring
