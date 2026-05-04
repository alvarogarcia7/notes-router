#!/bin/bash
# Start all colocated parsers using their bin/start.sh scripts
# Command decorator pattern: discovers parser subdirectories and invokes their bin/start.sh
set -e

PARSERS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$PARSERS_DIR/.." && pwd)"

# Load environment from nats/ directory
if [ -f "$REPO_ROOT/nats/.env" ]; then
    export $(grep -v '^#' "$REPO_ROOT/nats/.env" | xargs)
fi

# Also check for .env in repo root (for backward compatibility)
if [ -f "$REPO_ROOT/.env" ]; then
    export $(grep -v '^#' "$REPO_ROOT/.env" | xargs)
fi

# Set defaults if not already set
export NATS_URL="${NATS_URL:-tls://docker:4222}"
export CERTS_DIR="${CERTS_DIR:-$REPO_ROOT/nats/certs}"

echo "════════════════════════════════════════════════════════════"
echo "                 Starting All Colocated Parsers               "
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Environment:"
echo "  NATS_URL:   $NATS_URL"
echo "  CERTS_DIR:  $CERTS_DIR"
echo ""

# Track PIDs for cleanup
PID_FILE="$PARSERS_DIR/.pids"
> "$PID_FILE"  # Clear previous PIDs

# Discover parser directories and invoke their bin/start.sh
parser_count=0
for parser_dir in "$PARSERS_DIR"/*; do
    if [ ! -d "$parser_dir" ]; then
        continue
    fi

    parser_name=$(basename "$parser_dir")

    # Skip non-parser directories
    if [ ! -f "$parser_dir/bin/start.sh" ]; then
        continue
    fi

    echo "▶ Starting $parser_name..."

    # Start parser in background
    bash "$parser_dir/bin/start.sh" &
    local_pid=$!

    # Track PID
    echo $local_pid >> "$PID_FILE"

    ((parser_count++))
done

echo ""
if [ $parser_count -eq 0 ]; then
    echo "⚠ No parsers found with bin/start.sh in $PARSERS_DIR"
    echo ""
    echo "To use this script, clone parser repositories into this directory:"
    echo "  git clone <parser-repo> $PARSERS_DIR/<parser-name>"
    echo ""
    exit 1
fi

echo "════════════════════════════════════════════════════════════"
echo "✓ Started $parser_count parser(s)"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "To stop all parsers, press Ctrl+C or run:"
echo "  kill \$(cat $PID_FILE)"
echo ""

# Wait for all background processes
wait
