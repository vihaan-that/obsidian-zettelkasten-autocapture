# Chat Importers Setup & Usage

## Installation

### Enable Chat Importers

During organizer setup, add the `--enable-importers` flag:

```bash
bash scripts/setup-organizer.sh --enable-importers
```

This installs two cron jobs:
1. **Organizer** (nightly, 9 PM by default)
2. **Chat importers** (every 2 hours by default)

### Custom Interval

```bash
bash scripts/setup-organizer.sh --enable-importers --importer-interval 4h
```

Supported intervals: `30m`, `1h`, `2h`, `6h`, `12h`, `24h`

### Remove Importers

```bash
bash scripts/setup-organizer.sh --remove-importers
```

## How It Works

1. **Daemon runs** on your schedule (default: every 2 hours)
2. **Scans sources:**
   - `~/.claude/chats/` (Claude CLI history)
   - Platform-specific Copilot paths (Windows/macOS/Linux)
3. **For each new chat:**
   - Parses messages and metadata
   - Converts to markdown with YAML frontmatter
   - Writes to `vault/00-Inbox/`
4. **Tracks state:** SQLite database remembers imported IDs (no duplicates)
5. **Organizer picks up:** Existing pipeline classifies and files to `10-LLM-Chats/`

## Supported Tools

### Claude CLI

**Storage:** `~/.claude/chats/`  
**Format:** JSON Lines (JSONL) files  
**Auto-detection:** ✅ Works out of the box if Claude CLI is installed

### Copilot

**Storage:** Platform-specific (see below)  
**Format:** JSON (preferred) or SQLite

| Platform | Path |
|----------|------|
| Windows | `%APPDATA%\Microsoft\Copilot\chats` |
| macOS | `~/Library/Application Support/Microsoft Copilot/chats` |
| Linux | `~/.config/copilot/chats` |

**Auto-detection:** ✅ Checked automatically on startup

### Future Tools

To add support for new tools (ChatGPT, Gemini, etc.), see `importer-developer-guide.md`.

## Troubleshooting

**Issue:** "No importers available"
- **Solution:** Ensure Claude CLI or Copilot is installed and has chat history
- Check storage paths above

**Issue:** Files not appearing in inbox
- **Solution:** 
  - Run manually: `python3 scripts/chat_importers.py`
  - Check for errors: `python3 scripts/chat_importers.py --dry-run`
  - Verify paths with `ls ~/.claude/chats/` (Claude CLI)

**Issue:** Duplicate imports
- **Solution:** SQLite state file tracks imports. If duplicates appear:
  - Delete: `vault/_Scripts/import_state.db`
  - Re-run importers

## Manual Execution

### Preview changes (dry-run):
```bash
python3 scripts/chat_importers.py --dry-run
```

### Import without auto-push:
```bash
python3 scripts/chat_importers.py --no-push
```

### Custom vault path:
```bash
VAULT_PATH=/custom/vault python3 scripts/chat_importers.py
```

### Custom contributor:
```bash
LOG_CONTRIBUTOR=alice python3 scripts/chat_importers.py
```

## Integration with Organizer

The chat importers run **independently** of the organizer. They:
1. Import raw chats to `00-Inbox/`
2. The organizer (nightly) picks them up and processes them

**Timeline:**
```
10:00 AM → Chat importer runs → new chats in 00-Inbox/
12:00 PM → Chat importer runs → more chats in 00-Inbox/
...
9:00 PM → Organizer runs → classifies, files, generates digest
```

You can run either manually anytime:
```bash
# Just import chats
python3 scripts/chat_importers.py

# Just organize existing inbox
python3 scripts/organizer.py
```

## Logs

Import logs are printed to stdout. To capture them:

```bash
python3 scripts/chat_importers.py >> vault/_Scripts/importers.log 2>&1
```

Check the cron execution log:
- macOS: `log show --predicate 'process == "cron"' --last 1d`
- Linux: `journalctl -u cron -n 50`
