# Chat Importers & Web Clipper Architecture

This document contains architecture diagrams for the extended research-log system with chat importers and web clipper.

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         RESEARCH-LOG SYSTEM                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  CAPTURE SOURCES (7 total)                                             │
│  ─────────────────────────                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │  Team CLI    │  │ Claude Code  │  │ Git Commits  │                 │
│  │  (log.sh)    │  │ (hook)       │  │ (hook)       │                 │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                 │
│         │                  │                  │                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │   Browser    │  │   Browser    │  │    Chat      │                 │
│  │ Extension v1 │  │ Extension v2 │  │  Importers   │  NEW COMPONENTS│
│  │(Claude chats)│  │(Web Clipper) │  │  (Daemon)    │                 │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                 │
│         │                  │                  │                         │
│         └──────────┬───────┴──────────┬───────┘                         │
│                    │                  │                                 │
│         ┌──────────▼──────────────────▼────────┐                       │
│         │      vault/00-Inbox/                 │                       │
│         │   (Universal Staging Area)           │                       │
│         └──────────┬─────────────────────────┬─┘                       │
│                    │                         │                         │
│         ┌──────────▼──────┐      ┌───────────▼──────┐                 │
│         │  Watcher/Cron   │      │  Organizer       │                 │
│         │  (optional)      │      │  (nightly, admin)│                 │
│         └──────────┬───────┘      └─────────┬────────┘                 │
│                    │                        │                           │
│         ┌──────────▴────────────────────────▴────────┐                 │
│         │   Classified & Filed to Destinations      │                 │
│         ├──────────────────────────────────────────┤                 │
│         │ 10-LLM-Chats/      ← llm-chat type      │                 │
│         │ 15-Web-Clips/      ← web-clip type (NEW)│                 │
│         │ 20-Code-Sessions/  ← code-session type  │                 │
│         │ 30-Research/       ← research type      │                 │
│         │ 40-Experiments/    ← experiment type    │                 │
│         │ 50-Daily-Logs/     ← daily-log type     │                 │
│         │ 55-Journals/       ← journal type       │                 │
│         │ 60-Permanent/      ← general type       │                 │
│         └──────────────────────────────────────────┘                 │
│                    │                                                   │
│         ┌──────────▼────────────────────────┐                         │
│         │      Obsidian Vault               │                         │
│         │  (Dashboard + team knowledge base)│                         │
│         └───────────────────────────────────┘                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Browser Extension Architecture

```
┌──────────────────────────────────┐
│   Chrome Browser                 │
├──────────────────────────────────┤
│                                  │
│  ┌────────────────────────────┐  │
│  │   Content Script           │  │
│  │   (content.js)             │  │
│  │                            │  │
│  │ - Listens for messages     │  │
│  │ - Captures selected text   │  │
│  │ - Returns to popup         │  │
│  └────────────┬───────────────┘  │
│               │                   │
│  ┌────────────▼───────────────┐  │
│  │   Popup UI                 │  │
│  │   (popup.html/js)          │  │
│  │                            │  │
│  │ - Show page URL/title      │  │
│  │ - Display selected text    │  │
│  │ - Toggle screenshot        │  │
│  │ - Add notes & tags         │  │
│  │ - Save button              │  │
│  └────────────┬───────────────┘  │
│               │                   │
│  ┌────────────▼───────────────┐  │
│  │   Service Worker           │  │
│  │   (background.js)          │  │
│  │                            │  │
│  │ - Receive save request     │  │
│  │ - Generate markdown        │  │
│  │ - Capture screenshot       │  │
│  │ - Call downloads API       │  │
│  │ - Save to folder           │  │
│  └────────────┬───────────────┘  │
│               │                   │
│  ┌────────────▼───────────────┐  │
│  │   Settings/Options         │  │
│  │   (options.html/js)        │  │
│  │                            │  │
│  │ - Configure download path  │  │
│  │ - Set contributor name     │  │
│  │ - Persist in chrome.store  │  │
│  └────────────────────────────┘  │
│               │                   │
└───────────────┼───────────────────┘
                │
        ┌───────▼──────────┐
        │  Downloads API   │
        │  (chrome.*)      │
        └───────┬──────────┘
                │
        ┌───────▼──────────────────┐
        │  vault/00-Inbox/         │
        │  (markdown file written) │
        └──────────────────────────┘
```

## Chat Importers Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│               CHAT IMPORTERS DAEMON                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  chat_importers.py (main coordinator)                           │
│  ├─ get_vault_path()      → finds vault directory              │
│  ├─ get_contributor()     → git config or system user           │
│  └─ run_importers()       → orchestrates all importers          │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              ImportState (state.py)                        │ │
│  │                                                            │ │
│  │  SQLite Database: vault/_Scripts/import_state.db          │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │ imported_chats table:                                │ │ │
│  │  │   tool (TEXT)         ← 'claude-cli', 'copilot'     │ │ │
│  │  │   source_id (TEXT)    ← unique chat ID in tool      │ │ │
│  │  │   imported_at (TEXT)  ← ISO 8601 timestamp          │ │ │
│  │  │   PRIMARY KEY: (tool, source_id)                    │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                                                            │ │
│  │  Methods:                                                 │ │
│  │  - is_imported(tool, source_id) → bool                  │ │
│  │  - mark_imported(tool, source_id) → void               │ │
│  │  - list_imported(tool?) → List[tuple]                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              ChatImporter (base.py)                       │ │
│  │                                                            │ │
│  │  Abstract Base Class:                                      │ │
│  │  ├─ find_new_chats() → List[str]                          │ │
│  │  ├─ parse_chat(path) → Dict                              │ │
│  │  ├─ to_markdown(chat, contributor) → str               │ │
│  │  ├─ mark_imported(source_id) → void                     │ │
│  │  └─ tool_name (property) → str                          │ │
│  │                                                            │ │
│  │  Subclasses:                                              │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │        ClaudeCliImporter (claude_cli.py)                 │ │
│  │                                                            │ │
│  │  Scans: ~/.claude/chats/                                  │ │
│  │  Format: JSONL (one JSON object per line)                │ │
│  │  Files: *.jsonl                                           │ │
│  │                                                            │ │
│  │  Flow:                                                     │ │
│  │  1. _get_chat_dir() → find ~/.claude/chats/              │ │
│  │  2. find_new_chats() → glob *.jsonl, filter via state   │ │
│  │  3. parse_chat() → read JSONL, extract messages         │ │
│  │  4. to_markdown() → inherited, generates frontmatter     │ │
│  │  5. mark_imported() → update state DB                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │        CopilotImporter (copilot.py)                      │ │
│  │                                                            │ │
│  │  Scans: Platform-specific paths                           │ │
│  │  ├─ Windows:  %APPDATA%\Microsoft\Copilot\chats         │ │
│  │  ├─ macOS:   ~/Library/Application Support/.../chats    │ │
│  │  └─ Linux:   ~/.config/copilot/chats                    │ │
│  │                                                            │ │
│  │  Formats: JSON + SQLite (fallback)                        │ │
│  │                                                            │ │
│  │  Flow:                                                     │ │
│  │  1. _get_chat_dir() → detect per-platform path           │ │
│  │  2. find_new_chats() → glob *.json, *.db, filter         │ │
│  │  3. parse_chat() → delegate to JSON or DB parser         │ │
│  │     ├─ _parse_json_chat() → extract from JSON            │ │
│  │     └─ _parse_db_chat() → extract from SQLite            │ │
│  │  4. to_markdown() → inherited                             │ │
│  │  5. mark_imported() → update state DB                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                          │
                          │
                 Writes to inbox
                          │
                ┌─────────▼─────────┐
                │ vault/00-Inbox/   │
                │ (markdown files)  │
                └───────────────────┘
```

## Data Flow: Complete Pipeline

```
CAPTURE PHASE
─────────────

Claude Code Session      Git Commit              Claude Web Chat
(user stops)             (post-commit hook)      (browser extension)
    │                         │                        │
    ├─ Hook captures          ├─ Hook extracts         └─ Export button
    │  session ID             │  commit message           (existing feature)
    │  prompts                │  branch                   
    │  files changed          │  files changed
    │                         │
    └─────────────────────────┴────────────────────────┐
                              │
                    ┌─────────▼────────────┐
                    │   Watcher/Hook       │
                    │ Generates markdown   │
                    │ with YAML frontmatter│
                    └─────────┬────────────┘
                              │

STAGING PHASE
─────────────
                              │
                    ┌─────────▼────────────┐
                    │ vault/00-Inbox/      │
                    │ (universal staging)  │
                    │                      │
                    │ Files:               │
                    │ - llm-chat-*.md      │
                    │ - code-session-*.md  │
                    │ - web-clip-*.md (NEW)│
                    │ - journal-*.md       │
                    │ - daily-log-*.md     │
                    │ - experiment-*.md    │
                    └─────────┬────────────┘
                              │

PROCESSING PHASE
────────────────
                              │
                    ┌─────────▼────────────────┐
                    │ Organizer (nightly) or   │
                    │ Watcher (real-time)      │
                    │                          │
                    │ 1. Read file             │
                    │ 2. Parse YAML frontmatter│
                    │ 3. Extract summary/type  │
                    │ 4. LLM classify (if no   │
                    │    type already set)     │
                    │ 5. Update frontmatter    │
                    │ 6. Determine destination │
                    │ 7. Move file to folder   │
                    │ 8. Ask context question  │
                    │ 9. Append reflection     │
                    └─────────┬────────────────┘
                              │

FILING PHASE
────────────
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
    ┌───▼────┐          ┌────▼────┐          ┌────▼────┐
    │ 10-    │          │ 15-     │          │ 20-     │
    │ LLM-   │          │ Web-    │          │ Code-   │
    │ Chats/ │          │ Clips/  │ (NEW)    │ Sessions│
    │        │          │         │          │         │
    │ llm-   │          │ web-    │          │ code-   │
    │ chat*  │          │ clip*   │          │ session*│
    └────────┘          └─────────┘          └────────┘
        │                   │                     │
        │   ┌───────────────┼───────────┐         │
        │   │               │           │         │
    ┌───▼───▴────┐  ┌────────▴──────┐   │  ┌───────▴─────┐
    │ 50-Daily-  │  │ 40-Experiments│   │  │ 30-Research │
    │ Logs/      │  │               │   │  │             │
    │ 55-Journals│  │               │   │  │             │
    │ 60-Permanent│ └────────────────┘   │  └─────────────┘
    └────────────┘                       │
                    ┌────────────────────▴─────┐
                    │ Dashboard (Home.md)       │
                    │ Dataview queries          │
                    │ Team activity summary     │
                    └───────────────────────────┘

CONSUMPTION PHASE
─────────────────
                    │
                    ├─ Humans browse in Obsidian
                    ├─ Search by tag, contributor, date
                    ├─ Query with Dataview
                    ├─ Follow links between notes
                    │
                    └─ LLM agents can query:
                       "Show me all decisions alice made"
                       "What experiments are still running?"
                       "Summarize team activity for standup"
```

## Chat Importer Cron Integration

```
┌─────────────────────────────────────────────────────────┐
│              SYSTEM SCHEDULER (cron/launchd)           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  setup-organizer.sh installed two jobs:               │
│                                                         │
│  Job 1: Organizer (Nightly)                            │
│  ─────────────────────────────                         │
│  Schedule: 0 21 * * * (9 PM daily)                    │
│  Command: cd repo && python3 scripts/organizer.py     │
│  Action:                                               │
│    - git pull (fetch team entries)                    │
│    - Find unprocessed notes in 00-Inbox/              │
│    - LLM classify each note                           │
│    - Update frontmatter                               │
│    - Move to destination folder                       │
│    - Generate daily team digest                       │
│    - git commit + push                                │
│                                                         │
│  Job 2: Chat Importers (Every N hours)  NEW           │
│  ────────────────────────────────────────             │
│  Schedule: 0 */2 * * * (every 2 hours)               │
│  Command: cd repo && python3 scripts/chat_importers.py│
│  Action:                                               │
│    - For each importer (Claude CLI, Copilot):       │
│      • Scan storage location                          │
│      • Find new unimported chats                      │
│      • Parse messages                                 │
│      • Generate markdown + frontmatter               │
│      • Write to vault/00-Inbox/                      │
│      • Mark imported in state DB                     │
│    - Outputs: "Found X new chats, imported Y"        │
│                                                         │
│  Flags available:                                      │
│  --dry-run           Preview changes, don't write    │
│  --no-push           Import but don't auto-push      │
│                                                         │
│  Environment overrides:                               │
│  VAULT_PATH          Custom vault location           │
│  LOG_CONTRIBUTOR     Override contributor name       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## State Tracking for Duplicate Prevention

```
┌──────────────────────────────────────────────────────────┐
│  ImportState: SQLite Duplicate Prevention                │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Database: vault/_Scripts/import_state.db               │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐│
│  │ imported_chats TABLE                                ││
│  ├─────────────────────────────────────────────────────┤│
│  │ tool       │ source_id      │ imported_at           ││
│  ├─────────────┼────────────────┼──────────────────────┤│
│  │ claude-cli  │ chat_001.jsonl │ 2026-04-10T10:30:00Z││
│  │ claude-cli  │ chat_002.jsonl │ 2026-04-10T12:45:00Z││
│  │ copilot     │ conv_abc123    │ 2026-04-10T10:35:00Z││
│  │ copilot     │ conv_def456    │ 2026-04-10T14:20:00Z││
│  └─────────────┴────────────────┴──────────────────────┘│
│                                                          │
│  Primary Key: (tool, source_id)                         │
│  → Prevents same chat from being imported twice         │
│                                                          │
│  Flow:                                                   │
│  1. find_new_chats()                                    │
│     │                                                    │
│     ├─ Scan storage for all chats                       │
│     │                                                    │
│     └─ For each chat:                                   │
│        ├─ is_imported(tool, source_id)?                 │
│        │  ├─ YES → skip (already imported)             │
│        │  └─ NO  → include in new_chats list           │
│                                                          │
│  2. parse_chat(path)                                    │
│     ├─ Extract messages                                │
│     ├─ Generate markdown                               │
│     └─ Return chat dict                                │
│                                                          │
│  3. mark_imported(source_id)                            │
│     ├─ INSERT INTO imported_chats                       │
│     ├─   (tool, source_id, imported_at)               │
│     └─ VALUES ('claude-cli', 'chat_001.jsonl', now)   │
│                                                          │
│  Concurrency:                                            │
│  - 30-second SQLite timeout prevents "locked" errors   │
│  - INSERT OR IGNORE handles race conditions            │
│  - Safe for multiple importer processes                │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Integration with Existing Organizer

```
┌────────────────────────────────────────────────────────┐
│  Organizer Enhanced for New Features                   │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Frontmatter Field Handling:                           │
│                                                        │
│  PRESERVED (don't overwrite):                         │
│  ├─ type         (if already set)                     │
│  ├─ tool         (NEW: 'claude-cli', 'copilot', 'web')│
│  ├─ source_id    (NEW: prevents duplicates)           │
│  ├─ url          (NEW: for web-clips)                 │
│  ├─ repo         (existing: for code-sessions)        │
│  ├─ branch       (existing: for code-sessions)        │
│  └─ session_id   (existing: for code-sessions)        │
│                                                        │
│  OVERWRITTEN (by LLM if blank):                       │
│  ├─ date         (current date if missing)            │
│  ├─ contributor  (git config or system user)          │
│  ├─ summary      (LLM-generated if blank)             │
│  └─ tags         (LLM-generated if blank)             │
│                                                        │
│  DEST_FOLDERS (updated routing):                      │
│                                                        │
│  type: web-clip   → vault/15-Web-Clips/               │
│  type: llm-chat   → vault/10-LLM-Chats/               │
│  type: daily-log  → vault/50-Daily-Logs/              │
│  type: journal    → vault/55-Journals/                │
│  type: experiment → vault/40-Experiments/             │
│  type: code-sesh  → vault/20-Code-Sessions/           │
│  type: research   → vault/30-Research/                │
│  type: general    → vault/60-Permanent/               │
│                                                        │
└────────────────────────────────────────────────────────┘
```

## Extensibility: Adding New Chat Tools

```
┌──────────────────────────────────────────────────────────┐
│  Adding a New Tool: ChatGPT Importer Example             │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  1. Create: scripts/chat_importers/chatgpt.py          │
│                                                          │
│     from .base import ChatImporter, ChatMessage        │
│                                                          │
│     class ChatGPTImporter(ChatImporter):               │
│         @property                                       │
│         def tool_name(self) -> str:                    │
│             return 'chatgpt'                           │
│                                                          │
│         def find_new_chats(self) -> List[str]:         │
│             # Scan ChatGPT local storage               │
│             # Return list of unimported chat paths     │
│             pass                                       │
│                                                          │
│         def parse_chat(self, path: str) -> Dict:       │
│             # Parse ChatGPT format                     │
│             # Extract messages + metadata              │
│             # Return standardized dict                 │
│             pass                                       │
│                                                          │
│  2. Register: scripts/chat_importers.py                │
│                                                          │
│     try:                                                │
│         from chat_importers.chatgpt import ChatGPTImporter │
│         importers.append(ChatGPTImporter(state))       │
│     except Exception as e:                             │
│         print(f"Warning: Could not load ChatGPT: {e}") │
│                                                          │
│  3. Test: scripts/test_chatgpt.py                      │
│                                                          │
│     - Mock ChatGPT chat file                           │
│     - Test find_new_chats()                            │
│     - Test parse_chat()                                │
│     - Test markdown generation                         │
│     - Test state tracking                              │
│                                                          │
│  4. Run: python3 scripts/chat_importers.py             │
│     → Automatically discovers and runs ChatGPT importer│
│                                                          │
│  Base class provides:                                   │
│  ├─ to_markdown()    → generates frontmatter           │
│  ├─ mark_imported()  → updates state DB                │
│  └─ _escape_yaml()   → handles YAML escaping           │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

**Legend:**
- `→` = direction of flow or data movement
- `◀▶` = bidirectional communication
- `⊡` = file/storage
- `⭘` = process/function
- `◆` = decision point

