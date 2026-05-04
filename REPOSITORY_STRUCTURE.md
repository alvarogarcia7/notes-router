# Repository Structure & Organization

This document explains how the notes processing pipeline is organized across multiple repositories and what belongs in each one.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ notes-router (TOP-LEVEL ORCHESTRATION)                          │
│ - Central coordinator and routing logic                         │
│ - Type detection and message routing                            │
│ - NATS infrastructure and configuration                         │
│ - Documentation and guides                                      │
│ - Makefile and dependency management                            │
└────────────┬──────────────┬──────────────┬──────────────────────┘
             │              │              │
      ┌──────┴──────┐ ┌─────┴─────┐ ┌────┴────────┐
      │   Publishers│ │ Routers   │ │  Parsers    │
      └──────┬──────┘ └─────┬─────┘ └────┬────────┘
             │              │              │
    ┌────────┴────────┐     │        ┌─────┴──────────┬─────────────┬──────────┐
    │                 │     │        │                │             │          │
 [Google Keep]   [Apple   │    [google_notes_   [training-  [time-entry  [notes-parser
  (messages.10   Notes]   │     router.py]     parser-     notes-parser  next-entry]
  raw.type.*)            │                    antlr4]      time-entry]
                         │
                    [Type Detection]
                         │
         ┌───────────────┼───────────────┐
         ↓               ↓               ↓
    messages.20.* (routed by type)
         ├── messages.20.hn
         ├── messages.20.time
         ├── messages.20.training
         ├── messages.20.next
         └── messages.20.other.*
```

## Repository Breakdown

### 1. **notes-router** (Central Orchestration)
**Repository**: https://github.com/alvarogarcia7/notes-router

**Purpose**: Top-level coordinator and routing orchestration

**What goes here**:
- ✅ Router implementations (`routers/google_notes_router.py`, `routers/apple_notes_router.py`)
- ✅ NATS infrastructure (configuration, schemas)
- ✅ Type detection logic and routing rules
- ✅ Makefile and build automation
- ✅ pyproject.toml and uv.lock (dependency management)
- ✅ Central documentation (architecture, pipeline, system status)
- ✅ Git submodules for all parsers
- ✅ Guides for working with the pipeline (UPDATE-PARSERS.md, README_TESTING.md)

**Structure**:
```
notes-router/
├── routers/
│   ├── __init__.py
│   ├── google_notes_router.py     # Subscribes to messages.10.raw.type.googlenotes
│   └── apple_notes_router.py      # Subscribes to messages.10.raw.type.applenotes
├── parsers/                        # Git submodules
│   ├── training/
│   ├── hn/
│   ├── time/
│   └── next/
├── nats/                           # NATS configuration
│   ├── config.yaml
│   ├── schemas/
│   └── subscriber-python/
├── README.md                       # Repository overview
├── NOTES_ROUTING_ARCHITECTURE.md  # Routing design
├── PIPELINE_README.md             # End-to-end documentation
├── README_TESTING.md              # Testing guidelines
├── SYSTEM_STATUS.md               # Implementation tracking
├── UPDATE-PARSERS.md              # How to add/update parsers
├── Makefile                       # uv sync, test, clean
├── pyproject.toml                 # Python dependencies
└── uv.lock                        # Locked dependencies
```

**What does NOT go here**:
- ❌ Parser implementations (they have their own repos)
- ❌ Publisher logic (handled by source repos)
- ❌ Parser-specific documentation (goes in parser repos)

**How to work with it**:
```bash
cd notes-router
uv sync              # Install dependencies
make help            # See available targets
make test            # Run tests
python routers/google_notes_router.py  # Run router
```

---

### 2. **google-keep-notes-parser**
**Repository**: https://github.com/alvarogarcia7/google-keep-notes-parser

**Purpose**: Google Keep publisher + HackerNews parser

**What goes here**:
- ✅ Google Keep publisher (`nats_publisher.py`)
  - Reads JSON notes from files
  - Publishes to `messages.10.raw.type.googlenotes`
- ✅ HackerNews parser (`parsers/hackernews_parser.py`)
  - Detects HackerNews items via URL or label
  - Parses metadata (item ID, URL, etc.)
- ✅ HackerNews writer (`nats_hn_writer.py`)
  - Subscribes to `messages.30.type.hn.10.parsed`
  - Writes to `/tmp/nats/messages.30.type.hn.10.parsed/`
- ✅ Sample data (`sample/hn/`, `sample/googlenotes/`)
- ✅ Parser-specific tests and documentation

**Structure**:
```
google-keep-notes-parser/
├── nats_publisher.py              # Google Keep raw publisher
├── nats_hn_parser.py              # HackerNews parser
├── nats_hn_writer.py              # HackerNews writer
├── parsers/
│   ├── base.py
│   ├── hackernews_parser.py       # Can detect HN items
│   └── generic_notes_parser.py
├── sample/
│   ├── hn/                        # HN test data
│   ├── googlenotes/               # Generic Google notes
│   └── ...
├── PIPELINE_README.md             # Publisher/parser docs
└── ...
```

**What does NOT go here**:
- ❌ Routing logic (in notes-router)
- ❌ Type detection for other types (only HN)
- ❌ Other source publishers (Apple, etc.)

**How to work with it**:
```bash
cd google-keep-notes-parser
export NATS_URL=nats://localhost:4222
python nats_publisher.py --input-dir sample/hn  # Publish HN samples
python nats_hn_parser.py                         # Run parser
python nats_hn_writer.py                         # Run writer
```

---

### 3. **notes-exporter** (Apple Notes Publisher)
**Repository**: https://github.com/alvarogarcia7/notes-exporter

**Purpose**: Apple Notes exporter and publisher

**What goes here**:
- ✅ Apple Notes publisher (`nats_publisher.py`)
  - Exports notes from Apple Notes app
  - Publishes to `messages.10.raw.type.applenotes`
- ✅ Apple Notes routing handler (basic routing, no type-specific logic)
- ✅ Apple-specific metadata handling

**Structure**:
```
notes-exporter/
├── nats_publisher.py              # Apple Notes publisher
├── nats_router.py                 # Apple Notes router (if separate)
└── ...
```

**What does NOT go here**:
- ❌ Type detection (that's in notes-router)
- ❌ Routing logic (handled by notes-router's apple_notes_router.py)
- ❌ Parser implementations

**How to work with it**:
```bash
cd notes-exporter
export NATS_URL=nats://localhost:4222
python nats_publisher.py          # Export and publish Apple Notes
```

---

### 4. **training-parser-antlr4** (Training Parser)
**Repository**: https://github.com/alvarogarcia7/training-parser-antlr4

**Purpose**: Parse workout/training sessions using ANTLR4 grammar

**What goes here**:
- ✅ Training parser with ANTLR4 grammar (`src/training_parser.py`)
  - Detects training notes via format/exercises
  - Parses workout sessions and exercises
- ✅ Training parser writer (`nats_writer.py`)
  - Subscribes to `messages.30.type.training.10.parsed`
  - Writes to `/tmp/nats/messages.30.type.training.10.parsed/`
- ✅ ANTLR4 grammar files
- ✅ Sample workout data (`sample/training/`)
- ✅ Training-specific tests

**Structure**:
```
training-parser-antlr4/
├── src/
│   ├── training_parser.py         # Parser with can_parse()
│   ├── grammar/                   # ANTLR4 grammar
│   ├── data_access.py
│   └── ...
├── nats_training_listener.py      # NATS listener
├── nats_writer.py                 # Training writer
├── sample/training/               # Sample data
├── tests/
└── ...
```

**What does NOT go here**:
- ❌ Routing logic (in notes-router)
- ❌ Publisher (Google Keep/Apple Notes handle that)
- ❌ Type detection for other types

**How to work with it**:
```bash
cd training-parser-antlr4
export NATS_URL=nats://localhost:4222
python nats_training_listener.py  # Run parser
python nats_writer.py             # Run writer
```

---

### 5. **time-entry-notes-parser** (Time Entry Parser)
**Repository**: https://github.com/alvarogarcia7/notes-parser-time-entry

**Purpose**: Parse time entries from notes

**What goes here**:
- ✅ Time entry parser (`src/time_entry_parser.py`)
  - Detects time entries via format
  - Parses time entries with dates
- ✅ Time entry listener (`nats/nats_time_listener.py`)
  - Subscribes to `messages.20.time`
  - Publishes to `messages.30.type.time.10.parsed`
- ✅ Time entry writer (`nats/nats_writer.py`)
  - Subscribes to `messages.30.type.time.10.parsed`
  - Writes to `/tmp/nats/messages.30.type.time.10.parsed/`
- ✅ Time-specific tests and documentation

**Structure**:
```
time-entry-notes-parser/
├── src/
│   └── time_entry_parser.py       # Parser with can_parse()
├── nats/
│   ├── nats_time_listener.py      # NATS listener
│   ├── nats_writer.py             # Time writer
│   └── __init__.py
├── PIPELINE_README.md             # Time-entry specific docs
└── ...
```

**What does NOT go here**:
- ❌ Routing logic (in notes-router)
- ❌ Publisher (Google Keep/Apple Notes)
- ❌ Type detection for other types

**How to work with it**:
```bash
cd time-entry-notes-parser
export NATS_URL=nats://localhost:4222
python nats/nats_time_listener.py  # Run parser
python nats/nats_writer.py         # Run writer
```

---

### 6. **notes-parser-next-entry** (Next Entry Parser)
**Repository**: https://github.com/alvarogarcia7/notes-parser-next-entry

**Purpose**: Parse next/todo entries from notes

**What goes here**:
- ✅ Next entry parser (`src/next_entry_parser.py`)
  - Detects next/todo entries via format
  - Parses next action items
- ✅ Next entry listener (`nats/nats_next_listener.py`)
  - Subscribes to `messages.20.next`
  - Publishes to `messages.30.type.next.10.parsed`
- ✅ Next entry writer (`nats/nats_writer.py`)
  - Subscribes to `messages.30.type.next.10.parsed`
  - Writes to `/tmp/nats/messages.30.type.next.10.parsed/`
- ✅ Next-specific tests and documentation

**Structure**:
```
notes-parser-next-entry/
├── src/
│   └── next_entry_parser.py       # Parser with can_parse()
├── nats/
│   ├── nats_next_listener.py      # NATS listener
│   ├── nats_writer.py             # Next writer
│   └── __init__.py
├── PIPELINE_README.md             # Next-entry specific docs
└── ...
```

**What does NOT go here**:
- ❌ Routing logic (in notes-router)
- ❌ Publisher (Google Keep/Apple Notes)
- ❌ Type detection for other types

**How to work with it**:
```bash
cd notes-parser-next-entry
export NATS_URL=nats://localhost:4222
python nats/nats_next_listener.py  # Run parser
python nats/nats_writer.py         # Run writer
```

---

### 7. **link-collection-rust** (StrictDoc Requirements)
**Repository**: https://github.com/alvarogarcia7/link-collection-rust

**Purpose**: Requirements specification and documentation

**What goes here**:
- ✅ StrictDoc requirements (`requirements.sdoc`)
  - System requirements (SYSREQ)
  - High-level requirements (HLR)
  - Low-level requirements (LLR)
- ✅ Requirement hierarchy and traceability
- ✅ Makefile goals for StrictDoc validation
- ✅ GitHub Actions CI/CD pipeline configuration
- ✅ Documentation about requirements process

**What does NOT go here**:
- ❌ Implementation code (in respective parser repos)
- ❌ Routing logic (in notes-router)
- ❌ NATS configuration (in notes-router)

**How to work with it**:
```bash
cd link-collection-rust
make strictdoc-validate   # Validate requirements format
make strictdoc-build      # Build HTML documentation
make strictdoc-view       # Open docs in browser
```

---

## Message Flow Across Repositories

```
1. PUBLISHER STAGE (Source Repositories)
   ┌──────────────────────┬──────────────────┐
   │                      │                  │
   v                      v                  v
   google-keep-notes     notes-exporter     (other sources)
   nats_publisher.py     nats_publisher.py
   
   ↓ Publishes to ↓
   messages.10.raw.type.googlenotes (Google Keep)
   messages.10.raw.type.applenotes   (Apple Notes)
   
2. ROUTER STAGE (notes-router)
   ┌────────────────────────────────────────┐
   │ google_notes_router.py                 │
   │ apple_notes_router.py                  │
   │ - Detect type (HN, Time, Training, Next)
   │ - Route to messages.20.*               │
   └────────────────────────────────────────┘
   
   ↓ Routes to ↓
   messages.20.hn         (HackerNews)
   messages.20.time       (Time Entries)
   messages.20.training   (Training/Workouts)
   messages.20.next       (Next Items)
   messages.20.other.*    (Generic content)
   
3. PARSER STAGE (Type-Specific Repositories)
   ┌──────────────┬──────────────┬──────────────┬──────────────┐
   │              │              │              │              │
   v              v              v              v              v
   google-keep    time-entry     training      notes-parser   (others)
   nats_hn_       nats_time_     nats_training  nats_next_
   parser.py      listener.py    listener.py    listener.py
   
   ↓ Publishes to ↓
   messages.30.type.hn.10.parsed
   messages.30.type.time.10.parsed
   messages.30.type.training.10.parsed
   messages.30.type.next.10.parsed
   
4. WRITER STAGE (Type-Specific Repositories)
   ┌──────────────┬──────────────┬──────────────┬──────────────┐
   │              │              │              │              │
   v              v              v              v              v
   google-keep    time-entry     training      notes-parser   (others)
   nats_hn_       nats_writer.py nats_writer.py nats_writer.py
   writer.py
   
   ↓ Writes to ↓
   /tmp/nats/messages.30.type.hn.10.parsed/
   /tmp/nats/messages.30.type.time.10.parsed/
   /tmp/nats/messages.30.type.training.10.parsed/
   /tmp/nats/messages.30.type.next.10.parsed/
```

## When to Create a New Repository

Create a new repository when:

✅ **DO CREATE NEW REPO** for:
- New **parser type** (detect, parse, write a new content type)
- New **publisher** (new note source)
- New **framework/infrastructure** (like link-collection-rust for requirements)

❌ **DON'T CREATE NEW REPO** for:
- Router logic (goes in notes-router)
- Type detection helper functions (goes in notes-router)
- NATS configuration (goes in notes-router)
- General documentation (goes in notes-router)
- Central guides/processes (goes in notes-router)

## Adding a New Parser Type

To add a new parser type (e.g., "podcast" entries):

1. **Create repository** `notes-parser-podcast`
   - `src/podcast_parser.py` with `can_parse(note)` method
   - `nats/nats_podcast_listener.py`
   - `nats/nats_writer.py`

2. **Add to notes-router**
   - Add submodule: `git submodule add https://github.com/alvarogarcia7/notes-parser-podcast.git parsers/podcast`
   - Import parser in `routers/google_notes_router.py`
   - Add to `TYPE_TO_TOPIC` mapping: `"podcast": "messages.20.podcast"`

3. **Update documentation**
   - Update PIPELINE_README.md in notes-router
   - Add to architecture diagram
   - Document the new topic and parser

## Dependency Management

- **notes-router**: Uses `uv` (pyproject.toml + uv.lock)
- **Each parser**: Uses their preferred package manager
  - Google Keep: `pip` (requirements.txt) or `uv`
  - Training: `uv` (pyproject.toml + uv.lock)
  - Time Entry: `pip` (pyproject.toml + uv.lock)
  - Next Entry: `uv` (pyproject.toml + uv.lock)

## Documentation Organization

| Document | Location | Purpose |
|----------|----------|---------|
| Architecture overview | notes-router/NOTES_ROUTING_ARCHITECTURE.md | Design and routing logic |
| Full pipeline guide | notes-router/PIPELINE_README.md | End-to-end documentation |
| Testing guidelines | notes-router/README_TESTING.md | How to test the system |
| System status | notes-router/SYSTEM_STATUS.md | Implementation tracking |
| Parser updates | notes-router/UPDATE-PARSERS.md | How to add/modify parsers |
| Parser-specific docs | Each parser repo/PIPELINE_README.md | Parser-specific details |
| Requirements | link-collection-rust/requirements.sdoc | System requirements |

## Quick Reference: Where Things Go

| Item | Location |
|------|----------|
| Router implementation | notes-router/routers/ |
| Type detection | notes-router/routers/ (via parser can_parse) |
| Parser implementation | [type]-parser-[name]/ |
| Publisher | Publisher repo (Google Keep, Apple Notes, etc.) |
| Writer | Parser repo |
| NATS config | notes-router/nats/ |
| Type-to-topic mapping | notes-router/routers/ |
| Parser submodule | notes-router/parsers/[type]/ |
| Makefile | notes-router/ + each parser repo |
| Tests | Each repo (unit tests) + notes-router (integration) |
| Documentation | notes-router/ (central) + each repo (specific) |
| Requirements spec | link-collection-rust/ |

---

## Summary

The **notes-router** is the **TOP-LEVEL ORCHESTRATION REPOSITORY** that:
- Defines routing rules and type detection
- Hosts NATS infrastructure
- Coordinates all parsers via git submodules
- Provides central documentation and guides
- Manages dependencies and builds

Each **PARSER REPOSITORY** is independent and:
- Focuses on one content type
- Implements detection via `can_parse(note)`
- Provides listener and writer components
- Contains type-specific tests and docs
- Can be developed and tested independently

**Publishers** remain in their source repositories (Google Keep exporter, Apple Notes exporter) and simply publish raw messages to `messages.10.raw.type.*` topics.
