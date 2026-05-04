# Repository Structure & Organization

This document explains the organization of the notes processing pipeline across the notes-router repository and its dependencies.

## Repository Overview

**notes-router** is the central orchestration repository that coordinates:
- NATS infrastructure and configuration
- Message routing and type detection logic
- All parser submodules (training, HackerNews, time, next)
- Publisher/importer submodules (Google Keep, Apple Notes)
- Central documentation and Makefile

## Directory Structure

```
notes-router/
├── infra/                          # Infrastructure & deployment
│   └── nats/
│       ├── Makefile               # Docker NATS orchestration
│       ├── gen-certs.sh           # TLS certificate generation
│       ├── nats-server.conf       # NATS mTLS configuration
│       └── .gitignore
│
├── importers/                      # Source data importers (git submodules)
│   ├── google-keep/               # Google Keep exporter (keep-it-markdown)
│   │   ├── nats_publisher.py      # Publishes to messages.10.raw.type.googlenotes
│   │   └── ...
│   └── apple-notes/               # Apple Notes exporter (notes-exporter)
│       ├── nats_publisher.py      # Publishes to messages.10.raw.type.applenotes
│       └── ...
│
├── parsers/                        # Type-specific parsers (git submodules)
│   ├── time/
│   │   └── notes-parser-time-entry/
│   │       ├── src/nats_time_listener.py
│   │       ├── nats/nats_writer.py
│   │       └── ...
│   ├── hn/
│   │   └── google-keep-notes-parser/
│   │       ├── nats_hn_parser.py
│   │       ├── nats_hn_writer.py
│   │       └── ...
│   ├── training/
│   │   └── training-parser-antlr4/
│   │       ├── src/training_parser.py
│   │       ├── nats/nats_writer.py
│   │       └── ...
│   └── next/
│       └── notes-parser-next-entry/
│           ├── src/next_entry_parser.py
│           ├── nats/nats_writer.py
│           └── ...
│
├── routers/                        # Routing & type detection
│   ├── __init__.py
│   ├── google_notes_router.py     # Routes Google Keep notes
│   ├── apple_notes_router.py      # Routes Apple Notes
│   └── base_router.py             # Common routing logic
│
├── Makefile                        # Root orchestration (delegates to infra/)
├── .gitignore                      # Python build artifacts, egg-info
├── README.md                       # Repository overview with Mermaid diagram
├── NOTES_ROUTING_ARCHITECTURE.md  # Architecture design and message flow
├── REPOSITORY_STRUCTURE.md        # This file
├── PIPELINE_README.md             # End-to-end pipeline documentation
├── pyproject.toml                 # Python dependencies (uv)
├── uv.lock                        # Locked dependency versions
└── .env.example                   # Environment variables template
```

## Core Components

### 1. Infrastructure (`infra/nats/`)

**Purpose**: NATS server management and TLS configuration

**Key Files**:
- `Makefile` — Docker NATS orchestration (`nats-up`, `nats-down`, `nats-status`)
- `gen-certs.sh` — Automatic TLS certificate generation with ed25519
- `nats-server.conf` — NATS configuration with mutual TLS (mTLS) enforcement

**Usage**:
```bash
make nats-up      # Start NATS server in Docker
make nats-down    # Stop NATS server
make gen-certs    # Generate TLS certificates (auto-run on nats-up)
```

### 2. Importers (`importers/`)

**Purpose**: Extract notes from various sources and publish to raw message topics

**Submodules**:
- `google-keep/` (keep-it-markdown)
  - Extracts Google Keep notes
  - Publishes to `messages.10.raw.type.googlenotes`
  
- `apple-notes/` (notes-exporter)
  - Exports Apple Notes
  - Publishes to `messages.10.raw.type.applenotes`

**Design**: Publishers are in their source repositories. notes-router imports them as submodules for unified orchestration.

### 3. Routers (`routers/`)

**Purpose**: Detect message type and route to type-specific topics

**Components**:
- `google_notes_router.py`
  - Subscribes to `messages.10.raw.type.googlenotes`
  - Detects content type (time, HN, training, next, other)
  - Routes to `messages.20.*` topics

- `apple_notes_router.py`
  - Subscribes to `messages.10.raw.type.applenotes`
  - Detects content type
  - Routes to `messages.20.*` topics

**Type Detection**: Uses `can_parse()` method from parser modules to identify content type.

### 4. Parsers (`parsers/`)

**Purpose**: Type-specific parsing and result persistence

**Submodules**:

#### Time Parser (`parsers/time/`)
- Repository: `notes-parser-time-entry`
- Input: `messages.20.time`
- Output: `messages.30.type.time.10.parsed`
- Components:
  - `src/nats_time_listener.py` — Parser listener
  - `nats/nats_writer.py` — File writer

#### HackerNews Parser (`parsers/hn/`)
- Repository: `google-keep-notes-parser`
- Input: `messages.20.hn`
- Output: `messages.30.type.hn.10.parsed`
- Components:
  - `nats_hn_parser.py` — Parser
  - `nats_hn_writer.py` — File writer

#### Training Parser (`parsers/training/`)
- Repository: `training-parser-antlr4`
- Input: `messages.20.training`
- Output: `messages.30.type.training.10.parsed`
- Components:
  - `src/training_parser.py` — ANTLR4-based parser
  - `nats/nats_writer.py` — File writer

#### Next Parser (`parsers/next/`)
- Repository: `notes-parser-next-entry`
- Input: `messages.20.next`
- Output: `messages.30.type.next.10.parsed`
- Components:
  - `src/next_entry_parser.py` — Parser
  - `nats/nats_writer.py` — File writer

## Message Flow

### Stage 1: Publishers (Extract)
```
Google Keep Notes  →  messages.10.raw.type.googlenotes
Apple Notes        →  messages.10.raw.type.applenotes
```

### Stage 2: Routers (Type Detection)
```
messages.10.raw.type.*  →  Router  →  Detects Type  →  messages.20.*
                                     ├── time
                                     ├── hn
                                     ├── training
                                     ├── next
                                     └── other
```

### Stage 3: Parsers (Type-Specific Processing)
```
messages.20.time       →  Time Parser       →  messages.30.type.time.10.parsed
messages.20.hn         →  HN Parser         →  messages.30.type.hn.10.parsed
messages.20.training   →  Training Parser   →  messages.30.type.training.10.parsed
messages.20.next       →  Next Parser       →  messages.30.type.next.10.parsed
```

### Stage 4: Writers (Persist)
```
messages.30.type.*.10.parsed  →  Writer  →  /tmp/nats/$TOPIC/$ID.json
```

## Git Submodule Organization

### Parser Submodules
Each parser is a separate repository imported as a submodule:

```bash
# Time parser
git submodule add https://github.com/alvarogarcia7/notes-parser-time-entry.git \
                   parsers/time/notes-parser-time-entry

# HackerNews parser
git submodule add https://github.com/alvarogarcia7/google-keep-notes-parser.git \
                   parsers/hn/google-keep-notes-parser

# Training parser
git submodule add https://github.com/alvarogarcia7/training-parser-antlr4.git \
                   parsers/training/training-parser-antlr4

# Next parser
git submodule add https://github.com/alvarogarcia7/notes-parser-next-entry.git \
                   parsers/next/notes-parser-next-entry
```

### Importer Submodules
```bash
# Google Keep
git submodule add https://github.com/alvarogarcia7/keep-it-markdown.git \
                   importers/google-keep

# Apple Notes
git submodule add https://github.com/alvarogarcia7/notes-exporter.git \
                   importers/apple-notes
```

## Makefile Targets

### Root Makefile (`Makefile`)
```bash
make help          # Show available targets
make sync          # Install dependencies using uv
make test          # Run pytest tests
make install       # Install dependencies
make clean         # Clean up Python artifacts
make nats-up       # Start NATS server (delegates to infra/nats)
make nats-down     # Stop NATS server
make nats-status   # Check NATS server status
make gen-certs     # Generate TLS certificates
```

### Infrastructure Makefile (`infra/nats/Makefile`)
```bash
make up            # Start NATS + generate certs
make down          # Stop NATS
make status        # Show NATS status
make gen-certs     # Generate TLS certificates
make env-check     # Verify TLS configuration
make logs          # Show NATS logs
```

## Running the Pipeline

### 1. Start Infrastructure
```bash
cd notes-router
make nats-up
```

### 2. Start Routers
```bash
python3 routers/google_notes_router.py &
python3 routers/apple_notes_router.py &
```

### 3. Start Parsers (in separate terminals)
```bash
cd parsers/time && python3 -m nats.nats_time_listener
cd parsers/hn && python3 nats_hn_parser.py
cd parsers/training && python3 -m nats.nats_training_listener
cd parsers/next && python3 -m nats.nats_next_listener
```

### 4. Start Writers
```bash
cd parsers/time && python3 nats/nats_writer.py &
cd parsers/hn && python3 nats_hn_writer.py &
cd parsers/training && python3 nats/nats_writer.py &
cd parsers/next && python3 nats/nats_writer.py &
```

### 5. Publish Notes
```bash
cd importers/google-keep && python3 nats_publisher.py --input-dir ./sample
cd importers/apple-notes && python3 nats_publisher.py
```

## Architecture Principles

1. **Separation of Concerns**
   - Parsers focus on type-specific logic
   - Routers focus on type detection and routing
   - Infrastructure (infra/) is isolated from application logic

2. **Modularity**
   - Each parser is independent and testable
   - New parser types can be added without modifying routers
   - Publishers remain in source repositories

3. **Observability**
   - Raw messages preserved in Stage 1 (messages.10.raw.*)
   - Type-routed messages in Stage 2 (messages.20.*)
   - Parsed results in Stage 3 (messages.30.type.*.*)
   - Clear topic naming for easy debugging

4. **Extensibility**
   - New parser types: create new submodule in `parsers/[type]/`
   - New sources: add to `importers/` as submodule
   - No changes needed to routers when adding parsers (via can_parse())

## Adding a New Parser Type

To add a parser for a new content type (e.g., "podcast" entries):

1. **Create repository**: `notes-parser-podcast`
   ```
   notes-parser-podcast/
   ├── src/podcast_parser.py (with can_parse() method)
   ├── nats/nats_podcast_listener.py
   ├── nats/nats_writer.py
   └── ...
   ```

2. **Add submodule**: 
   ```bash
   git submodule add https://github.com/alvarogarcia7/notes-parser-podcast.git \
                      parsers/podcast/notes-parser-podcast
   ```

3. **Router detects automatically** via can_parse() method

4. **Update documentation**: Add to NOTES_ROUTING_ARCHITECTURE.md

## Dependencies

**notes-router**: Uses `uv` for dependency management
- `pyproject.toml` — Declares dependencies
- `uv.lock` — Locks exact versions

**Each parser**: Manages own dependencies
- Most use `uv` with `pyproject.toml`
- Some may use `pip` with `requirements.txt`

## Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Repository overview with Mermaid diagram |
| `NOTES_ROUTING_ARCHITECTURE.md` | Architecture design, stages, and message flow |
| `REPOSITORY_STRUCTURE.md` | This file — directory structure and organization |
| `PIPELINE_README.md` | End-to-end pipeline documentation |
| `Makefile` | Root orchestration targets |

## Summary

**notes-router** provides:
- ✅ Central NATS infrastructure (`infra/nats/`)
- ✅ Type detection and routing logic (`routers/`)
- ✅ Git submodules for all parsers and importers
- ✅ Unified Makefile for orchestration
- ✅ Central documentation

**Each parser repository** provides:
- ✅ Type-specific parsing logic
- ✅ NATS listener component
- ✅ File writer component
- ✅ Type-specific tests and documentation

This separation enables independent development while maintaining a coordinated pipeline.
