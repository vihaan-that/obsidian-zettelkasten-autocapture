# Claude CLI Storage Research

## Storage Path

**Primary location:** `~/.claude/`

### Path Structure
- **Global history:** `~/.claude/history.jsonl`
- **Project conversations:** `~/.claude/projects/{encoded-project-path}/{session-uuid}.jsonl`
- **Session metadata:** `~/.claude/sessions/{pid}.json`
- **File history:** `~/.claude/file-history/{session-uuid}/{file-id}@v{version}`
- **Settings:** `~/.claude/settings.json`
- **Credentials:** `~/.claude/.credentials.json`

### Project Path Encoding
Project directories in `~/.claude/projects/` encode the filesystem path with:
- Forward slashes (`/`) replaced with hyphens (`-`)
- Example: `/home/vihaan/Documents/work` becomes `-home-vihaan-Documents-work`

### Platform Variations
- **Linux/macOS:** `~/.claude/` expands to `$HOME/.claude/`
- **Windows:** `%APPDATA%\.claude\` (TBD - requires verification on Windows system)

## Format

Claude CLI uses **JSONL (JSON Lines)** format for storing conversations:
- Each line is a valid JSON object
- One message/event per line
- Newline-delimited for streaming and append-only writes
- Files are created with restricted permissions (0600)

## Example Structure

### Global History File (`~/.claude/history.jsonl`)
Each line contains command/display information:

```json
{"display":"la","pastedContents":{},"timestamp":1775710678819,"project":"/home/vihaan","sessionId":"b2a94701-ca45-454e-9602-4ea02194e16a"}
{"display":"ls -la","pastedContents":{},"timestamp":1775710685352,"project":"/home/vihaan","sessionId":"b2a94701-ca45-454e-9602-4ea02194e16a"}
```

### Session Conversation Files (`~/.claude/projects/{encoded-path}/{session-uuid}.jsonl`)

**First entry - Permission mode:**
```json
{
  "type": "permission-mode",
  "permissionMode": "default",
  "sessionId": "5674e451-1bb3-47fc-861b-8531e255c528"
}
```

**User message entry:**
```json
{
  "parentUuid": "0475b74d-b949-49c7-bfff-5a40b6236d1a",
  "isSidechain": false,
  "type": "user",
  "message": {
    "role": "user",
    "content": "<command-message>superpowers:using-superpowers</command-message>\n<command-name>/superpowers:using-superpowers</command-name>"
  },
  "uuid": "2e68b509-c377-4c74-b210-f5b1f3fe55a6",
  "timestamp": "2026-04-10T05:58:39.100Z",
  "userType": "external",
  "entrypoint": "cli",
  "cwd": "/home/vihaan/Documents/work",
  "sessionId": "5674e451-1bb3-47fc-861b-8531e255c528",
  "version": "2.1.97",
  "gitBranch": "HEAD"
}
```

**Assistant message entry (minimal example):**
```json
{
  "parentUuid": "92f04424-8e46-4d08-abb6-289ba43fa23e",
  "isSidechain": false,
  "message": {
    "model": "claude-haiku-4-5-20251001",
    "id": "msg_01RXVTTqEwraj7yVmzEjHRcY",
    "type": "message",
    "role": "assistant",
    "content": [
      {
        "type": "thinking",
        "thinking": "[extended content...]"
      }
    ],
    "stop_reason": "end_turn",
    "usage": {
      "input_tokens": 9,
      "cache_creation_input_tokens": 29743,
      "cache_read_input_tokens": 0,
      "output_tokens": 429
    }
  },
  "requestId": "req_011CZuaV5S2A1SVFiPERskef",
  "type": "assistant",
  "uuid": "11673da2-1989-43d9-962b-413e928be90a",
  "timestamp": "2026-04-10T05:58:44.518Z",
  "userType": "external",
  "entrypoint": "cli",
  "cwd": "/home/vihaan/Documents/work",
  "sessionId": "5674e451-1bb3-47fc-861b-8531e255c528",
  "version": "2.1.97",
  "gitBranch": "HEAD"
}
```

### Session Metadata File (`~/.claude/sessions/{pid}.json`)
```json
{
  "pid": 9852,
  "sessionId": "5674e451-1bb3-47fc-861b-8531e255c528",
  "cwd": "/home/vihaan/Documents/work",
  "startedAt": 1775800546869,
  "kind": "interactive",
  "entrypoint": "cli"
}
```

### Settings File (`~/.claude/settings.json`)
```json
{
  "model": "haiku",
  "extraKnownMarketplaces": {
    "superpowers-marketplace": {
      "source": {
        "source": "github",
        "repo": "obra/superpowers-marketplace"
      }
    }
  },
  "enabledPlugins": {
    "superpowers@claude-plugins-official": true
  }
}
```

## Key Fields in Conversation Messages

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Message type: "user", "assistant", "system", "permission-mode" |
| `uuid` | string | Unique identifier for this message |
| `parentUuid` | string | UUID of parent message (threading) |
| `sessionId` | string | Session identifier (UUID v4 format) |
| `timestamp` | string | ISO 8601 timestamp |
| `cwd` | string | Working directory at time of message |
| `message` | object | Message content (user/assistant) |
| `message.role` | string | "user" or "assistant" |
| `message.content` | array/string | Message content (may contain thinking for assistant) |
| `version` | string | Claude CLI version |
| `gitBranch` | string | Git branch if in a repository |
| `userType` | string | "external" or internal type |
| `entrypoint` | string | "cli" for command-line usage |

## Detection Strategy

### Method 1: Modification Time (mtime)
- Use `stat` or `os.stat()` to check file modification times
- `Modify` timestamp indicates last write time
- Example: `stat ~/.claude/history.jsonl | grep Modify`
- Watch for changes in:
  - `~/.claude/history.jsonl` (global history)
  - `~/.claude/projects/**/*.jsonl` (session files)

### Method 2: File Watching
Use OS-level file watchers:
- **Linux:** `inotifywait`, `fsnotify` Python library
- **macOS:** `FSEvents`, `watchdog` Python library
- **Windows:** `FileSystemWatcher` .NET, `watchdog` Python library

### Method 3: Directory Scanning
Periodically scan and index:
```
1. Walk ~/.claude/projects/
2. For each *.jsonl file, compare mtime against last sync timestamp
3. Process files with newer mtime
4. Update sync timestamp to current time
```

### Detection Implementation Notes
- **Append-only format:** JSONL files are append-only, so track line count or file size for incremental imports
- **Session files:** Check `~/.claude/sessions/` for active PIDs (running sessions)
- **Global history:** `~/.claude/history.jsonl` is updated for every command in any session
- **Frequency:** New messages are appended instantly as conversation happens
- **Permissions:** Files are readable by owner only (0600), ensure proper access

### Example Timestamp Format
- Global history uses Unix milliseconds: `1775710678819`
- Conversation files use ISO 8601: `"2026-04-10T05:58:39.100Z"`

## Additional Storage Directories

Beyond conversation data, Claude CLI stores:

| Directory | Purpose |
|-----------|---------|
| `~/.claude/backups/` | Backup files |
| `~/.claude/cache/` | Cache data |
| `~/.claude/downloads/` | Downloaded files |
| `~/.claude/plugins/` | Installed plugins and marketplaces |
| `~/.claude/session-env/` | Session environment state |
| `~/.claude/tasks/` | Task history and state |
| `~/.claude/telemetry/` | Usage telemetry (if enabled) |
| `~/.claude/shell-snapshots/` | Shell state snapshots |

## Notes for Importer Implementation

1. **Path Resolution:** Always expand `~` to user's home directory using appropriate OS methods
2. **Encoding Handling:** When converting back to filesystem paths, replace leading `-` with `/` and subsequent `-` patterns appropriately (exact encoding needs verification)
3. **Session Threading:** Use `parentUuid` to reconstruct message threads within a session
4. **Time Zones:** Timestamps in conversation files are UTC (ISO 8601), global history uses Unix milliseconds
5. **File Permissions:** Respect 0600 permissions; files are user-readable only
6. **Subagent Tracking:** Messages from subagents appear in `./{session-uuid}/subagents/agent-{id}.jsonl`
7. **Large Files:** Session JSONL files can be large (tested file was 508KB for ~164 messages); use streaming JSON parser for efficient processing

## References

- **System tested:** Linux (Ubuntu 22.04+)
- **Claude CLI version:** 2.1.97
- **Storage verified:** April 10, 2026
