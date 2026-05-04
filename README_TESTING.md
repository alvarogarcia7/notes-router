# NATS Pipeline - Complete Testing Guide

## Quick Start: Run Everything with One Command

```bash
cd /var/tmp/vibe-kanban/worktrees/08e4-implement-this-f
./run_pipeline_test.sh
```

This single script will:
- ✅ Check all prerequisites
- ✅ Start NATS server
- ✅ Start all 4 pipeline components
- ✅ Publish sample data
- ✅ Verify output
- ✅ Validate JSON
- ✅ Clean up

**Expected result**: `NATS Pipeline Test PASSED ✓` with output files in `/tmp/training/`

---

## What Gets Tested

### Step 1: Publisher ✓
- **File**: `google-keep-notes-parser/nats_publisher.py`
- **Tests**: Reads JSON files, wraps with UUID, publishes to `messages.10.raw`
- **Verified by**: Message count in logs

### Step 2: Router ✓
- **File**: `google-keep-notes-parser/nats_router.py`
- **Tests**: Subscribes to `messages.10.raw`, detects type, routes to `messages.20.type.training`
- **Verified by**: Router log messages showing "Routed to 'training'"

### Step 3: Training Listener ✓
- **File**: `training-parser-antlr4/nats_training_listener.py`
- **Tests**: Parses with ANTLR4, publishes sessions to `messages.30.type.training.10.parsed`
- **Verified by**: Session count in logs, no parse errors

### Step 4: Writer ✓
- **File**: `training-parser-antlr4/nats_writer.py`
- **Tests**: Writes parsed sessions to `/tmp/training/<counter>.json`
- **Verified by**: File count, file sizes, JSON validity

---

## Files Provided

### Test Script
- **`run_pipeline_test.sh`** (9.7 KB) — Automated end-to-end test
  - Runs all components
  - Validates output
  - Reports detailed results
  - Automatic cleanup

### Documentation
- **`QUICK_TEST.md`** — Quick reference with examples
- **`PIPELINE_README.md`** — Complete architecture and API docs
- **`README_TESTING.md`** — This file

### Implementation Files (Already Committed)
- **`google-keep-notes-parser/nats_publisher.py`** — Enhanced publisher
- **`google-keep-notes-parser/nats_router.py`** — Type-based router
- **`training-parser-antlr4/nats_training_listener.py`** — ANTLR4 parser listener
- **`training-parser-antlr4/nats_writer.py`** — Output writer

---

## Running the Test

### Prerequisites
- Docker (for NATS)
- Python 3.9+
- Sample data (included in `google-keep-notes-parser/sample/`)

### Option 1: Automated Test (Recommended)

```bash
./run_pipeline_test.sh
```

**What happens**:
1. Checks prerequisites
2. Starts NATS in Docker (if not running)
3. Starts Writer, Listener, Router (in order)
4. Publishes sample data
5. Waits 15 seconds for processing
6. Validates output files
7. Shows results
8. Cleans up

**Expected output**:
```
✓ All pipeline components executed successfully!
✓ Generated 1 output file(s)
✓ All output files are valid JSON (1/1)
✓ Output contains 'workout_id' field
✓ Output contains 'exercises' field
✓ Output contains 'date' field

NATS Pipeline Test PASSED ✓
```

### Option 2: Manual Testing (5 Terminals)

**Terminal 1** - Start NATS:
```bash
docker run -p 4222:4222 nats:latest
```

**Terminal 2** - Start Writer:
```bash
cd training-parser-antlr4
python nats_writer.py
```

**Terminal 3** - Start Training Listener:
```bash
cd training-parser-antlr4
python nats_training_listener.py
```

**Terminal 4** - Start Router:
```bash
cd google-keep-notes-parser
python nats_router.py
```

**Terminal 5** - Publish data:
```bash
cd google-keep-notes-parser
python nats_publisher.py --input-dir sample
```

**Terminal 6** - Check results:
```bash
watch -n 1 'ls -la /tmp/training/ && echo "---" && head -20 /tmp/training/0.json'
```

---

## Test Output Examples

### Successful Test Output

```
════════════════════════════════════════════════════════
NATS Pipeline Test PASSED ✓
════════════════════════════════════════════════════════

✓ All pipeline components executed successfully!
✓ Sample data published from google-keep-notes-parser
✓ Messages routed by type using ParserRegistry
✓ Training messages parsed with ANTLR4
✓ Parsed sessions written to /tmp/training

Pipeline Verification Summary:
  Input:  Google Keep notes (JSON files)
  Step 1: Publisher → messages.10.raw
  Step 2: Router → messages.20.type.training
  Step 3: Training Listener → messages.30.type.training.10.parsed
  Step 4: Writer → /tmp/training/*.json
  Output: 1 parsed workout session(s)
```

### Sample Output File

```json
{
  "workout_id": "w_20260123_000000",
  "type": "set-centric",
  "date": "2026-01-23",
  "location": "",
  "notes": "",
  "statistics": {},
  "exercises": [
    {
      "name": "Bench Press",
      "equipment": "other",
      "sets": [
        {
          "setNumber": 1,
          "repetitions": 30,
          "weight": {
            "amount": 13.6,
            "unit": "kg"
          }
        },
        {
          "setNumber": 2,
          "repetitions": 15,
          "weight": {
            "amount": 22.1,
            "unit": "kg"
          }
        }
      ]
    },
    {
      "name": "Machine Row",
      "equipment": "other",
      "sets": [
        {
          "setNumber": 1,
          "repetitions": 20,
          "weight": {
            "amount": 26,
            "unit": "kg"
          }
        }
      ]
    }
  ]
}
```

---

## Debugging

### Common Issues and Solutions

#### Script Can't Find Docker
```bash
# Install Docker
docker --version

# Make sure Docker daemon is running
docker ps

# Run with sudo if needed
sudo ./run_pipeline_test.sh
```

#### Script Can't Find Python
```bash
# Install Python 3.9+
python3 --version

# Use full path if needed
/usr/bin/python3 -m --version
```

#### No Output Files Generated

Check the component logs:
```bash
# See what Writer is doing
tail -20 /tmp/nats_writer.log

# See what Listener is doing
tail -20 /tmp/nats_training_listener.log

# See what Router is doing
tail -20 /tmp/nats_router.log
```

#### NATS Not Connecting

```bash
# Check if NATS is running
nc -z localhost 4222 && echo "NATS OK" || echo "NATS DOWN"

# If down, start it manually
docker run -d -p 4222:4222 nats:latest

# Check NATS logs
docker logs <container-id>
```

#### Invalid JSON Output

The ANTLR4 parser may have failed. Check listener log:
```bash
grep -i error /tmp/nats_training_listener.log
```

Check if sample data matches the grammar:
```bash
cd training-parser-antlr4
python3 -c "
from src.data_access import SessionGrouper, ExerciseParser
parser = ExerciseParser()
# Test manually with sample text
"
```

---

## Monitoring

### Watch NATS Messages in Real-Time

```bash
# Install nats CLI tools
docker run --rm -it natsio/nats-top -s nats://localhost:4222
```

### Monitor Output Files

```bash
# Watch for new files
watch -n 0.1 'ls -lh /tmp/training/ | tail -5'

# Count messages flowing
watch -n 1 'wc -l /tmp/nats_*.log'
```

### Check Component Health

```bash
# List running processes
ps aux | grep nats_

# Check memory usage
top -p $(pgrep -f nats_ | tr '\n' ',')
```

---

## Performance Expectations

| Metric | Expected |
|--------|----------|
| NATS startup | 2-3 seconds |
| Component startup | 1-2 seconds each |
| Publisher execution | <1 second |
| Per-message latency | 100-500ms |
| Total test duration | 15-20 seconds |
| Output file size | 1-5 KB per session |

---

## Extended Testing

### Test with Custom Data

```bash
# Create your own JSON note file
cat > google-keep-notes-parser/sample/training/custom.json <<'EOF'
{
  "id": "custom-001",
  "title": "My Workout",
  "text": "☐ Deadlift\n  ☐ 5x5x100\n☐ Bench Press\n  ☐ 3x8x80",
  "timestamps": {"created": "2026-04-30 12:00:00", "edited": "2026-04-30 12:00:00"},
  "archived": false,
  "trashed": false,
  "labels": [],
  "media_paths": [],
  "blob_names": [],
  "keep_url": ""
}
EOF

# Run test again
./run_pipeline_test.sh
```

### Test Multiple Sessions

Create a note with multiple workout sessions:
```json
{
  "id": "multi-session",
  "title": "Week of Training",
  "text": "2026-04-29\nDeadlift: 5x5x100\n\n2026-04-30\nBench Press: 3x8x80",
  ...
}
```

### Test Type Detection

Add different note types:
```bash
# Add a Toggl note (time entry)
# Add a Next note (task list)
# Add a Hacker News note
# Run test - router should distribute to different topics
```

---

## Advanced: Manual NATS Inspection

```bash
# Get NATS stats
curl http://localhost:8222/varz

# Get subsriber info
curl http://localhost:8222/subsz

# Get server info
curl http://localhost:8222/serverz

# Monitor a specific topic
nats sub messages.10.raw
nats sub messages.20.type.training
nats sub messages.30.type.training.10.parsed
```

---

## Troubleshooting Checklist

- [ ] Docker is installed and running (`docker ps`)
- [ ] Python 3.9+ is available (`python3 --version`)
- [ ] Sample data exists (`ls google-keep-notes-parser/sample/training/`)
- [ ] NATS is accessible (`nc -z localhost 4222`)
- [ ] Script is executable (`chmod +x run_pipeline_test.sh`)
- [ ] No other processes using port 4222
- [ ] `/tmp/training/` is writable
- [ ] All 4 Python files exist and are syntactically valid

---

## Success Criteria

The test passes when:

✅ All prerequisite checks pass  
✅ NATS starts successfully  
✅ All 4 components start without errors  
✅ Publisher publishes data  
✅ Output files are created in `/tmp/training/`  
✅ Output files contain valid JSON  
✅ Output JSON has required fields (workout_id, exercises, date)  
✅ All components still running at end of test  

---

## Additional Resources

- **Full Pipeline Docs**: `PIPELINE_README.md`
- **Quick Reference**: `QUICK_TEST.md`
- **Implementation Details**: `IMPLEMENTATION_SUMMARY.md`
- **NATS Docs**: https://docs.nats.io/
- **Docker Docs**: https://docs.docker.com/

---

**Last Updated**: 2026-04-30  
**Test Script Version**: 1.0  
**All Criteria**: ✅ PASSING
