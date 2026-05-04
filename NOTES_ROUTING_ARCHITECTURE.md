# Notes Routing Architecture

## Overview

The system now implements a two-stage routing architecture for Google Keep and Apple Notes, separating raw message ingestion from parsing and type-specific routing.

## Message Flow

### Google Keep Notes

```
Google Keep Notes (JSON files)
         ↓
google-keep-notes-parser/nats_publisher.py
         ↓
messages.10.raw.type.googlenotes (raw notes)
         ↓
google-keep-notes-parser/nats_router.py
         ↓
messages.20.googlenotes (standardized format)
```

### Apple Notes

```
Apple Notes (exported via notes-exporter)
         ↓
notes-exporter/nats_publisher.py
         ↓
messages.10.raw.type.applenotes (raw notes)
         ↓
notes-exporter/nats_router.py
         ↓
messages.20.applenotes (standardized format)
```

### HackerNews (for reference)

```
HackerNews RSS/API
         ↓
link-collection-rust/nats-listener (Rust binary)
         ↓
messages.20.hn (standardized format)
```

## Message Format - messages.20.* (Standard Output Format)

All messages routed to `messages.20.*` topics follow the same schema:

```json
{
  "id": "uuid-unique-identifier",
  "message_type": "googlenotes|applenotes|hn",
  "note": {
    "id": "note-specific-id",
    "title": "Note Title",
    "text": "Note content (optional)",
    "url": "URL if applicable (optional)",
    "date": "YYYY-MM-DD (optional, extracted or provided)"
  },
  "source": "google-keep|apple-notes|hn"
}
```

## Components

### 1. Google Keep Notes Publisher
- **File:** `google-keep-notes-parser/nats_publisher.py`
- **Input:** JSON files from Google Keep export
- **Output Topic:** `messages.10.raw.type.googlenotes`
- **Format:** Raw note data with date extraction
- **Command:** `python3 nats_publisher.py --input-dir ./sample`

### 2. Google Keep Notes Router
- **File:** `google-keep-notes-parser/nats_router.py`
- **Input Topic:** `messages.10.raw.type.googlenotes`
- **Output Topic:** `messages.20.googlenotes`
- **Transformation:** Standardizes to messages.20.* format
- **Command:** `python3 nats_router.py`

### 3. Apple Notes Publisher
- **File:** `notes-exporter/nats_publisher.py`
- **Input:** JSON files from notes-exporter export
- **Output Topic:** `messages.10.raw.type.applenotes`
- **Format:** Raw note data with date extraction
- **Command:** `python3 nats_publisher.py --data-dir ./data`

### 4. Apple Notes Router
- **File:** `notes-exporter/nats_router.py`
- **Input Topic:** `messages.10.raw.type.applenotes`
- **Output Topic:** `messages.20.applenotes`
- **Transformation:** Standardizes to messages.20.* format
- **Command:** `python3 nats_router.py`

### 5. HackerNews NATS Listener (Rust)
- **File:** `link-collection-rust/nats-listener/src/main.rs`
- **Input Topic:** None (subscribes directly to NATS)
- **Output Topic:** `messages.20.hn`
- **Format:** Pre-standardized HackerNews messages
- **Command:** `cargo run -p nats-listener`

## Benefits of This Architecture

1. **Separation of Concerns**
   - Publishers handle source-specific extraction and formatting
   - Routers handle transformation to standardized format

2. **Source Identification**
   - `messages.10.raw.type.*` clearly identifies the source type
   - `messages.20.*` provides type-specific access to standardized data

3. **Unified Schema**
   - All messages in `messages.20.*` follow the same format
   - Enables consistent downstream processing

4. **Scalability**
   - Easy to add new note sources (e.g., OneNote, Notion)
   - Router pattern is reusable for any new source

5. **Debugging**
   - Raw messages preserved in messages.10.raw.type.* for inspection
   - Transformation errors can be isolated to routers

## Configuration

All components use:
- **NATS_URL:** Environment variable (e.g., `tls://localhost:4222`)
- **CERTS_DIR:** Directory containing TLS certificates (default: `/tmp/nats-certs`)
  - Required files: `client.pem`, `client.key`, `rootCA.pem`

## Running the Pipeline

1. **Start NATS Server** (with TLS)
   ```bash
   nats-server -c nats-server.conf
   ```

2. **Start Routers** (in separate terminals)
   ```bash
   cd google-keep-notes-parser && python3 nats_router.py
   cd notes-exporter && python3 nats_router.py
   ```

3. **Publish Notes**
   ```bash
   cd google-keep-notes-parser && python3 nats_publisher.py --input-dir ./sample
   cd notes-exporter && python3 nats_publisher.py --data-dir ./data
   ```

4. **Monitor Messages** (optional)
   ```bash
   nats sub "messages.20.*"
   ```

## Future Enhancements

- Add additional note sources (OneNote, Notion, etc.)
- Implement message persistence/storage from messages.20.*
- Add metadata enrichment in routers (e.g., NLP tags, categorization)
- Create unified message validator for messages.20.*
