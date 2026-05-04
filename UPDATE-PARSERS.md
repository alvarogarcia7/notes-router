# Parser Update Tool

The `update-parsers.sh` tool manages updating individual parser repositories from their remote sources. It handles version tracking, conflict detection, and provides status information.

## Quick Start

```bash
# Check all parsers for updates
make update-parsers-check

# Update all parsers
make update-parsers-all

# Check specific parser
make update-parser-time

# Update specific parser
make update-time

# Show parser versions
make parser-status

# Show version history
make parser-versions
```

## Script Usage

The script can be run directly or via Makefile targets:

```bash
# Direct usage
bash update-parsers.sh [PARSER] [MODE]

# Via Makefile
make update-parsers-check    # Check all
make update-time             # Update specific
make parser-status           # Show status
```

## Parsers

The tool manages these parsers:

| Name | Directory | Repository |
|------|-----------|------------|
| Time | `time-entry-notes-parser` | `notes-parser-time-entry` |
| Training | `training-parser-antlr4` | `training-parser-antlr4` |
| HackerNews | `hackernews-parser` | `hackernews-parser` |
| Next | `notes-parser-next-entry` | `notes-parser-next-entry` |

## Modes

### `check` (default)
Checks for available updates without modifying anything:

```bash
bash update-parsers.sh time check
```

Output shows:
- Current branch and commit
- Number of remote commits ahead
- Number of local commits ahead
- Latest remote commits
- Whether local changes exist

**Example:**
```
==> Checking time-entry-notes-parser for updates...

  Branch: master
  Local commit: 9bf2762
  Remote commits ahead of you: 3
  Your commits ahead of remote: 0
  
  Latest remote commits:
    abc1234 Fix timeout issue
    def5678 Add retry logic
    ghi9012 Improve error handling
```

### `update`
Pulls the latest changes from the remote repository:

```bash
bash update-parsers.sh training update
```

Features:
- Automatically fetches from remote
- Stashes local changes (with timestamp marker)
- Merges remote changes
- Updates version tracking file
- Shows before/after commits

**Example:**
```
==> Updating training-parser-antlr4...
==> Pulling latest from origin/08e4-implement-this-f...
✓ training-parser-antlr4 updated
  From: 6d18f62
  To:   abc1234
```

### `reset`
Resets parser to match remote version (discards local changes):

```bash
bash update-parsers.sh next reset
```

⚠️ **Warning:** This will discard all uncommitted changes. Asks for confirmation.

### `status`
Shows detailed status of a parser:

```bash
bash update-parsers.sh all status
```

Displays:
- Current branch
- Full commit hash
- Author and date
- Commit message
- Whether repository is clean or has changes

**Example:**
```
==> time-entry-notes-parser status

  Branch:  master
  Commit:  9bf2762 (9bf27621234567890abcdefghijklmnop)
  Author:  Claude Haiku
  Date:    2026-05-02 19:50:00 +0000
  Message: Add environment configuration sample (.env.sample)
  Status:  ✓ Clean
```

### `versions`
Shows version history from `parser-versions.txt`:

```bash
bash update-parsers.sh versions
```

**Example:**
```
# Parser Version Tracking
# Format: parser_name:last_updated:commit:branch

google-keep-notes-parser:2026-05-02 19:50:00 UTC:4f4f962
training-parser-antlr4:2026-05-02 19:50:00 UTC:6d18f62
time-entry-notes-parser:2026-05-02 19:50:00 UTC:9bf2762
notes-parser-next-entry:2026-05-02 19:50:00 UTC:9bf2762
```

## Targets

The tool supports filtering to specific parsers:

| Target | Description |
|--------|-------------|
| `all` | All parsers (default) |
| `time` | Time entry parser only |
| `training` | Training parser only |
| `hn` or `hackernews` | HackerNews parser only |
| `next` | Next entry parser only |
| `google` | Google Keep parser only |

## Examples

### Check Single Parser for Updates

```bash
bash update-parsers.sh time check
```

### Update All Parsers

```bash
bash update-parsers.sh all update
```

### Check Training Parser Status

```bash
bash update-parsers.sh training status
```

### Reset Next Parser to Remote

```bash
bash update-parsers.sh next reset
```

### Show Version History

```bash
bash update-parsers.sh versions
```

## Makefile Integration

The Makefile provides convenient targets:

```bash
# Check targets
make update-parsers-check    # Check all parsers
make update-parser-time      # Check time parser
make update-parser-training  # Check training parser
make update-parser-hn        # Check HackerNews parser
make update-parser-next      # Check next parser

# Update targets
make update-parsers-all      # Update all parsers
make update-time             # Update time parser
make update-training         # Update training parser
make update-hn               # Update HackerNews parser
make update-next             # Update next parser

# Status targets
make parser-status           # Show all parser versions
make parser-versions         # Show version history
```

## Version Tracking

The tool maintains `parser-versions.txt` to track:
- Parser name
- Last update timestamp
- Commit hash
- Branch name

This file is automatically updated on successful parser updates and helps track what versions are currently deployed.

## Workflow Examples

### Monitor Parser Updates

```bash
# Check all parsers periodically
watch -n 3600 'bash update-parsers.sh all check'

# Or use Makefile
watch -n 3600 'make update-parsers-check'
```

### Update Parsers Before System Start

```bash
# Check for updates
make update-parsers-check

# If updates available, update them
make update-parsers-all

# Then start system
make up
```

### Safe Parser Update with Stashing

If you have local changes in a parser:

```bash
# Check status (will detect local changes)
make parser-status

# Update (will auto-stash changes with timestamp)
make update-training

# Restore changes if needed
cd training-parser-antlr4
git stash list
git stash pop  # or git stash apply stash@{N}
```

### Compare Versions Before/After

```bash
# Before update
make parser-versions

# Update parsers
make update-parsers-all

# Check what changed
make parser-versions

# See detailed changes
make parser-status
```

## Handling Conflicts

If there are merge conflicts during update:

1. The script will stop and notify you
2. Local changes are automatically stashed
3. Manual resolution needed:

```bash
# Go to the conflicted parser
cd training-parser-antlr4

# Check conflict status
git status

# Resolve conflicts manually
# Edit files to resolve conflicts
git add .
git commit -m "Resolved merge conflicts"

# Return to main directory
cd ..
```

## Error Handling

The script handles these scenarios:

- **Directory not found** - Shows error and continues with other parsers
- **Remote fetch fails** - Shows warning and skips update
- **Merge conflicts** - Stashes changes and informs user
- **Local changes** - Automatically stashes with timestamp
- **No remote** - Shows error if repository has no remote

## Security Notes

- The tool uses HTTPS remotes (no SSH key required)
- Local changes are preserved (stashed, not deleted)
- All commands require explicit confirmation for destructive operations
- Version history is maintained for audit trail

## Troubleshooting

### Parser Directory Not Found

```bash
# Ensure parser exists
ls -la training-parser-antlr4/

# If missing, initialize submodules
git submodule update --init --recursive
```

### Cannot Fetch from Remote

```bash
# Check remote configuration
cd training-parser-antlr4
git remote -v

# Update remote if needed
git remote set-url origin https://github.com/username/repo.git
```

### Merge Conflicts

```bash
# See status
cd training-parser-antlr4
git status

# See conflicts
git diff --name-only --diff-filter=U

# Resolve manually, then commit
```

### Restore Stashed Changes

```bash
cd parser-directory
git stash list
git stash show stash@{0}  # See what's in stash
git stash pop             # Apply and remove from stash
# or
git stash apply stash@{0} # Apply without removing
```

## Notes

- All operations are logged with timestamps
- Version history is persistent across sessions
- Stashed changes include auto-generated timestamp markers
- The tool respects current branch of each parser
- Failed updates don't affect other parsers
