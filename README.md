# Notes Router

Central routing and orchestration repository for the NATS-based notes processing pipeline.

This repository coordinates:
- **NATS infrastructure** — Configuration and schemas for message passing
- **Parsers** — Git submodules for specialized parsers (training, HackerNews, time, next)
- **Routers** — Python applications that route Google Keep and Apple Notes to appropriate parsers

## Architecture

```
Publishers (Google Keep, Apple Notes)
         ↓
    [Routers]
    ├── Detects message type (training, HN, time, next)
    ├── Routes to appropriate messages.20.* topic
    └── Publishes standardized message format
         ↓
    [Parsers]
    ├── messages.30.type.training.10.parsed
    ├── messages.30.type.hn.10.parsed
    ├── messages.30.type.time.10.parsed
    └── messages.30.type.next.10.parsed
         ↓
    [Writers]
    └── /tmp/nats/$TOPIC/
```

## Folder Structure

```
notes-router/
├── nats/                          # NATS configuration and schemas
│   ├── config.yaml               # NATS configuration
│   ├── Makefile                  # NATS-related targets
│   └── schemas/                  # Message schemas
│
├── parsers/                       # Parser submodules
│   ├── training/                 # training-parser-antlr4 submodule
│   ├── hn/                        # google-keep-notes-parser (HN parser) submodule
│   ├── time/                      # time-entry-notes-parser submodule
│   └── next/                      # notes-parser-next-entry submodule
│
├── routers/                       # Routing logic
│   ├── __init__.py
│   ├── google_notes_router.py    # Routes Google Keep notes
│   └── apple_notes_router.py     # Routes Apple Notes
│
└── README.md
```

## Setup

### Prerequisites
- Python 3.9+
- Git with submodule support
- NATS server running

### Initialize

```bash
git clone --recurse-submodules https://github.com/alvarogarcia7/notes-router.git
cd notes-router
pip install -r requirements.txt
```

### Update submodules

```bash
git submodule update --remote
```

## Running

### Start NATS
```bash
docker run -p 4222:4222 nats:latest
```

### Start Routers
```bash
python routers/google_notes_router.py
python routers/apple_notes_router.py
```

### Start Parsers
See individual parser repositories for instructions.

## NATS Topics

### Stage 1: Publishers
- `messages.10.raw.type.googlenotes` — Google Keep notes
- `messages.10.raw.type.applenotes` — Apple Notes

### Stage 2: Routers
- `messages.20.time` — Time entries
- `messages.20.hn` — HackerNews items
- `messages.20.training` — Training sessions
- `messages.20.next` — Next entries
- `messages.20.other.*` — Generic content (source-specific)

### Stage 3: Parsers & Writers
- `messages.30.type.time.10.parsed`
- `messages.30.type.hn.10.parsed`
- `messages.30.type.training.10.parsed`
- `messages.30.type.next.10.parsed`

## Related Repositories

- [google-keep-notes-parser](https://github.com/alvarogarcia7/google-keep-notes-parser) — Publisher & HN parser
- [notes-exporter](https://github.com/alvarogarcia7/notes-exporter) — Apple Notes publisher
- [training-parser-antlr4](https://github.com/alvarogarcia7/training-parser-antlr4) — Training parser
- [time-entry-notes-parser](https://github.com/alvarogarcia7/notes-parser-time-entry) — Time parser
- [notes-parser-next-entry](https://github.com/alvarogarcia7/notes-parser-next-entry) — Next entry parser
