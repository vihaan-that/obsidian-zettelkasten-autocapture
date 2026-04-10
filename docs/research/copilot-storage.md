# Copilot Storage Research

## Overview

Microsoft Copilot and related AI products are offered in multiple forms, each with different storage mechanisms. This research covers storage locations for:

1. **GitHub Copilot Chat** (VS Code extension)
2. **Microsoft Copilot** (web-based at copilot.microsoft.com)
3. **Microsoft 365 Copilot Chat** (enterprise)
4. **Microsoft Copilot for Windows** (desktop app)

## Storage Paths

### GitHub Copilot Chat (VS Code)

This is the most well-documented Copilot product in terms of local storage.

**Windows:**
```
C:\Users\{USERNAME}\AppData\Roaming\Code\User\workspaceStorage\{HASH}\
```

**macOS:**
```
~/Library/Application Support/Code/User/workspaceStorage/{HASH}/
```

**Linux:**
```
~/.config/Code/User/workspaceStorage/{HASH}/
```

Where `{HASH}` is an alphanumeric folder name unique to each workspace.

### Microsoft Copilot (Web-based)

**Access:** `https://copilot.microsoft.com`

- **Primarily cloud-stored:** Chat history is stored server-side on Microsoft servers
- **Default retention:** 90 days from last update
- **Sync:** Conversations sync across devices when signed in with same Microsoft account
- **Local cache:** May cache minimal data using browser IndexedDB, LocalStorage, or Cache API (varies by implementation)

**Browser storage locations (if cached locally):**
- Windows Edge: `%APPDATA%\Microsoft\Edge\User Data\Default\` (IndexedDB/LocalStorage)
- macOS Safari: `~/Library/Safari/`
- macOS Chrome: `~/Library/Application Support/Google/Chrome/Default/`
- Linux: `~/.config/google-chrome/Default/`

### Microsoft 365 Copilot Chat

**Storage:** Cloud-based only, no local file storage

- Chat history stored in user's **Exchange mailbox** (hidden folder)
- Data location determined by Preferred Data Location (PDL)
- Primary retention in Tenant's Primary Provisioned Geography if PDL not set
- Files added to conversations: Stored in **OneDrive** under "Microsoft Copilot Chat Files" folder

### Microsoft Copilot for Windows (Desktop App)

**Storage:** Hybrid (cloud + limited local)

- Downloaded from Microsoft Store
- Chat history remains **local to device** (not synced to other devices)
- **Specific paths unclear** - documented as "local device storage" in official docs
- Persists after reboot and across sessions on same device
- No documented public API for accessing local storage location

## File Format

### GitHub Copilot Chat (VS Code)

**Primary storage:** SQLite database
- **File:** `state.vscdb` (located in workspaceStorage hash folder)
- **Format:** SQLite 3
- **Querying:** `sqlite3 ./state.vscdb "SELECT value FROM ItemTable WHERE key='memento/interactive-session';" > output.json`

**Secondary storage:** JSON files
- **Location:** `{workspaceStorage}/{HASH}/chatSessions/`
- **File naming:** `session.json` or similar
- **Format:** JSON containing conversation arrays

**Database structure:**
- `ItemTable` - contains session metadata and history
- Keys:
  - `memento/interactive-session` - Session index
  - `interactive.sessions` - Session data

### Microsoft Copilot (Web)

**Format:** Server-side storage (inaccessible to users)
- Likely JSON in Microsoft's backend databases
- Users cannot directly access or export via file system

**Browser cache format (if applicable):**
- IndexedDB: Structured database
- LocalStorage: Key-value pairs
- Cache API: Network request/response caches

### Microsoft 365 Copilot Chat

**Format:** Not directly accessible
- Stored as Exchange items in user's mailbox
- Accessible via Copilot app UI or Microsoft 365 services
- Export via File → Save As (creates local copy)

## Example Structure

### GitHub Copilot Chat - SQLite Query Result

Sample query output from `state.vscdb`:
```json
{
  "sessions": [
    {
      "id": "chat-session-uuid-1",
      "title": "Help with TypeScript generics",
      "created": "2024-04-10T10:30:00Z",
      "modified": "2024-04-10T10:45:00Z",
      "messages": [
        {
          "id": "msg-1",
          "type": "user",
          "text": "How do I create a generic function in TypeScript?",
          "timestamp": "2024-04-10T10:30:00Z"
        },
        {
          "id": "msg-2",
          "type": "assistant",
          "text": "Here's a generic function example...",
          "timestamp": "2024-04-10T10:30:05Z"
        }
      ]
    }
  ]
}
```

### GitHub Copilot Chat - JSON File Format

Sample from `chatSessions/session.json`:
```json
{
  "title": "Help with TypeScript generics",
  "description": "",
  "messages": [
    {
      "role": "user",
      "content": "How do I create a generic function in TypeScript?",
      "editorInfo": {
        "language": "typescript",
        "file": "example.ts"
      }
    },
    {
      "role": "assistant",
      "content": "Here's a generic function example:\n\n```typescript\nfunction identity<T>(arg: T): T {\n  return arg;\n}\n```",
      "command": "/explain"
    }
  ],
  "exportDate": "2024-04-10T10:45:00Z"
}
```

### Workspace.json Structure

Located at `workspaceStorage/{HASH}/workspace.json`:
```json
{
  "folders": [
    {
      "path": "/path/to/your/project"
    }
  ]
}
```

Use this to identify which folder hash corresponds to which project.

## Filename Patterns

### GitHub Copilot Chat Detection

**Required patterns:**
- Directory: `Code/User/workspaceStorage/{HASH}/chatSessions/`
- File pattern: `*.json` or `session.json`
- Database file: `state.vscdb`

**Detection strategy:**
1. Identify workspace hash by checking `workspace.json` in each folder
2. Match against known project paths
3. Query `state.vscdb` for session index
4. Read JSON files from `chatSessions/` directory

**Identification example:**
```
C:\Users\alice\AppData\Roaming\Code\User\workspaceStorage\
├── 7927a352490752d89d45d86565940562/
│   ├── workspace.json          # Check folder path here
│   ├── state.vscdb             # Query for sessions
│   └── chatSessions/
│       └── session.json        # Read conversation data
└── a8c3f4d2e1b9c7a5f6e8d0c1b2a3/
    └── ...
```

### Microsoft Copilot (Web)

**No direct file access.** Chat history accessible only through:
- Web UI at `copilot.microsoft.com`
- Chat history sidebar on left panel
- Browser developer tools (IndexedDB inspection) - varies by implementation

### Microsoft 365 Copilot Chat

**No direct file access.** Chat history accessible only through:
- Microsoft 365 Copilot app UI
- In-app conversation history panel
- Export via "Save As" option

## Detection Strategy

### GitHub Copilot Chat - Full Detection Flow

**Platform-specific base paths:**
- **Windows:** `%APPDATA%\Microsoft\Visual Studio Code\` or `AppData\Roaming\Code\`
- **macOS:** `~/Library/Application Support/Code/`
- **Linux:** `~/.config/Code/`

**Detection algorithm:**
```
1. Navigate to {BASE}/User/workspaceStorage/
2. For each {HASH} subfolder:
   a. Read workspace.json to get project path
   b. Check if chatSessions/ directory exists
   c. If exists, list all *.json files
   d. Query state.vscdb for session metadata
   e. Parse JSON files for conversation content
3. Build index of:
   - Project path
   - Session IDs
   - Message counts
   - Timestamps
```

**Sample detection code pattern:**
```bash
# Windows
workspaceStorage="$APPDATA/Microsoft/Visual Studio Code/User/workspaceStorage"

# macOS
workspaceStorage="~/Library/Application Support/Code/User/workspaceStorage"

# Linux
workspaceStorage="~/.config/Code/User/workspaceStorage"

for hash_dir in "$workspaceStorage"/*; do
  if [[ -f "$hash_dir/workspace.json" ]]; then
    project=$(jq -r '.folders[0].path' "$hash_dir/workspace.json")
    if [[ -d "$hash_dir/chatSessions" ]]; then
      echo "Found Copilot chats for project: $project"
      sqlite3 "$hash_dir/state.vscdb" \
        "SELECT value FROM ItemTable WHERE key = 'memento/interactive-session';"
    fi
  fi
done
```

### Microsoft Copilot (Web) - Detection

**Browser-based chat detection:**
- No direct file system detection available
- Requires browser API access or cloud service queries
- Authentication needed for accessing user's chat history
- Recommend: Use Microsoft Graph API with appropriate permissions

### Microsoft 365 Copilot Chat - Detection

**Cloud-based detection:**
- No local file system locations
- Requires Exchange mailbox access via Microsoft Graph or Outlook API
- Recommended approach: Use official Microsoft 365 APIs
- OneDrive files: Accessible via Microsoft Graph Files API

## Implementation Notes

### Platform-Specific Considerations

**Windows:**
- Use `%APPDATA%` and `%LOCALAPPDATA%` environment variables
- SQLite requires sqlite3 CLI or library (pre-installed on many systems)
- May need to handle file permissions for hidden folders

**macOS:**
- Paths use `~` which needs expansion
- SQLite available via Homebrew if not installed
- May need to request full disk access permission for app access

**Linux:**
- Paths follow XDG standards (`~/.config/`, `~/.local/share/`)
- SQLite usually pre-installed
- File permissions typically less restrictive than macOS/Windows

### Version Variations

**VS Code:**
- Storage format consistent across recent versions (v1.70+)
- Older versions may use different paths or format (rare)
- Consider checking multiple possible paths for legacy installs

**GitHub Copilot Chat:**
- Chat format has evolved; older installations may have different schema
- Consider version checks in workspaceStorage folder

### Fallback Strategies

**If exact storage location cannot be found:**

1. **GitHub Copilot Chat:**
   - Use VS Code telemetry data if available
   - Check VS Code's main settings/data directory
   - Fall back to searching system for `state.vscdb` files
   - Use `find` command: `find ~/ -name "state.vscdb" 2>/dev/null`

2. **Microsoft Copilot (Web):**
   - No reliable fallback for local access
   - Recommend: Prompt user to export from web UI
   - Alternative: Use authenticated cloud API access
   - Can parse browser history/cache if legal/ethical concerns addressed

3. **Microsoft 365 Copilot Chat:**
   - No local fallback available
   - Requires cloud API (Microsoft Graph)
   - Users must have appropriate Microsoft 365 licenses
   - Consider IT admin coordination for enterprise deployments

4. **Microsoft Copilot for Windows:**
   - Exact path unclear from documentation
   - Fallback: Search common paths:
     - `%APPDATA%\Microsoft\Copilot\`
     - `%LOCALAPPDATA%\Microsoft\Copilot\`
     - `%LOCALAPPDATA%\Packages\Microsoft.Copilot_*\`
   - Consider contacting Microsoft Support for clarity

### Error Handling

**Handle these scenarios:**
- SQLite database locked (in use by another process)
- Permission denied when accessing user directories
- Corrupted state.vscdb file (implement repair/recovery)
- Missing workspace.json (fall back to folder scanning)
- Incomplete or malformed JSON in chat files
- Cloud sync in progress (temporary unavailability)

### Data Privacy Considerations

- **GitHub Copilot Chat:** Local machine data, user has full access
- **Microsoft Copilot (Web):** Cloud storage, Microsoft's privacy policy applies
- **Microsoft 365 Copilot Chat:** Enterprise data subject to org policies
- **Windows Copilot:** Local device, limited cloud sync
- Always respect user privacy and obtain consent before accessing
- Handle sensitive data (credentials, passwords) that may appear in conversations

## References

- [GitHub Discussion: Where is Copilot Chat history in local file system](https://github.com/orgs/community/discussions/69740)
- [VS Code Copilot Chat History Transfer Guide](https://medium.com/@Manikandan.K.S/how-to-transfer-github-copilot-chat-history-in-vscode-between-devices-97edf082c160)
- [Microsoft Support: Conversation History in Microsoft Copilot](https://support.microsoft.com/en-us/topic/conversation-history-in-microsoft-copilot-9a07325a-0366-4c2d-82cb-dab61be8287c)
- [Data Residency for Microsoft 365 Copilot](https://learn.microsoft.com/en-us/microsoft-365/enterprise/m365-dr-workload-copilot)
- [Microsoft Edge Storage Policies](https://learn.microsoft.com/en-us/microsoft-edge/progressive-web-apps/how-to/offline)
- [GitHub Copilot CLI Chronicle Documentation](https://docs.github.com/en/copilot/concepts/agents/copilot-cli/chronicle)
- [VS Code Copilot Chat Viewer Tool](https://github.com/Timcooking/VSCode-Copilot-Chat-Viewer)

## Summary

**Most accessible storage:** GitHub Copilot Chat in VS Code has the clearest local file storage with documented SQLite database and JSON files.

**Most challenging:** Microsoft Copilot for Windows has unclear documentation; exact local storage paths require further investigation or reverse engineering.

**Recommendation:** Implement GitHub Copilot Chat importer first (most reliable), then web-based Copilot (requires authentication), then Microsoft 365 (enterprise API), and Windows Copilot (pending clarification).
