# Chat Importers & Web Clipper Extension Design

**Date:** 2026-04-10  
**Status:** Design (awaiting review)

---

## Overview

Extend the research-log system to capture chat logs from Claude CLI, Copilot, and other LLM tools, plus add a browser extension for saving web content (text clips, links, screenshots). Both new capture sources feed into the existing `00-Inbox/` → organizer pipeline, requiring no architectural changes to the core system.

---

## Problem Statement

The current research-log captures:
- Manual daily logs via CLI
- Claude Code sessions (via hook)
- Git commits (via hook)
- Claude web chats (via browser extension)

**Gaps:**
- Claude CLI and Copilot chats are lost or siloed locally
- No easy way to save important web pages/articles for team reference
- Teammates manually export or lose context from non-Claude tools

**Goal:** Automatically collect team chat logs + enable lightweight web clipping, all flowing into the shared vault.

---

## Architecture

### System Overview

The system expands from 5 capture sources to 7, all routing through the same inbox/organizer pipeline:

```
CAPTURE SOURCES (7 total)
├── Interactive CLI (log.sh)
├── Claude Code session hook
├── Git commit hook
├── Browser extension (Claude web chats) — existing
├── Browser extension v2 (text clips + links + screenshots) — NEW
├── Chat importers daemon (Claude CLI, Copilot, ...) — NEW
└── Manual drops

                    ↓

            vault/00-Inbox/
        (universal staging area)

                    ↓

    inbox_watcher.py (optional, real-time)
            OR
    organizer.py (nightly, admin PC)

                    ↓

    Classified & filed to destination folders
    + daily team digest generated
```

### New Component: Chat Importers Daemon

**Purpose:** Periodically scan for new chats from Claude CLI and Copilot, convert to markdown, write to inbox.

**How it works:**
1. Runs on a cron schedule (configurable, default: every 2 hours)
2. Scans tool-specific storage locations for new chat files
3. Parses each chat into structured markdown with YAML frontmatter
4. Writes to `vault/00-Inbox/` (one file per chat)
5. Tracks imported chats in state file (SQLite) to avoid duplicates
6. Done — existing watcher/organizer picks up and classifies

**Installation:**
- New script: `scripts/chat_importers.py`
- Integration: `setup-organizer.sh` includes `--enable-importers` flag
- Cron job: installed alongside the organizer cron job

### New Component: Browser Extension (Web Clipper)

**Purpose:** Lightweight capture of web content (text, links, optional screenshots) for team reference.

**User flow:**
1. User visits a web page
2. Selects text (or just wants page context)
3. Clicks extension icon → popup form appears
4. Popup shows: preview of selection, page URL/title, toggle for screenshot, optional note field
5. User clicks "Save to Obsidian" → file lands in `vault/00-Inbox/`
6. Organizer classifies and files to `15-Web-Clips/` or other destination

**What gets captured:**
- Selected text or full page content
- Page URL + title (auto-filled)
- Screenshot (if toggled, embedded as image)
- Timestamp
- User's optional note + tags
- Contributor name (detected from browser profile or set in extension settings)

**Tech stack:**
- Chrome Manifest V3 extension (vanilla JavaScript, no build step)
- Uses Chrome `captureVisibleTab` API for screenshots
- Settings page: user configures download folder once (points to `vault/00-Inbox/`)
- File structure:
  ```
  extension/
  ├── manifest.json
  ├── popup.html
  ├── popup.js
  ├── options.html
  ├── options.js
  └── background.js
  ```

---

## Chat Importers: Tool Support

### Claude CLI

**Storage location:** `~/.claude/chats/` or similar (TBD: research where CLI stores chat history)  
**Format:** Likely JSON or SQLite

**Import logic:**
1. Scan the chat directory for new files (use mtime to detect changes)
2. Parse chat structure (message exchanges, timestamps)
3. Convert to markdown: one conversation per file
4. Extract metadata: date, first few messages (for summary), tool="claude-cli"
5. Write to inbox

**Importer class:** `ClaudeCliImporter` in `chat_importers/claude_cli.py`

### Copilot

**Storage location:** OS-specific
- Windows: `%APPDATA%\Microsoft\Copilot` or similar
- macOS: `~/Library/Application Support/Copilot`
- Linux: `~/.config/copilot` or `~/.local/share/copilot`

**Format:** Likely JSON or local database

**Import logic:** Same as Claude CLI — scan for new, parse, convert to markdown

**Importer class:** `CopilotImporter` in `chat_importers/copilot.py`

### Extensibility

**Framework design:**
```python
# chat_importers/base.py
class ImporterBase:
    def find_new_chats(self) -> List[str]:
        """Return paths to unimported chat files"""
        pass
    
    def parse_chat(self, path: str) -> dict:
        """Return { messages, metadata }"""
        pass
    
    def to_markdown(self, chat: dict) -> str:
        """Convert chat to markdown + frontmatter"""
        pass
    
    def mark_imported(self, chat_id: str):
        """Update state file"""
        pass
```

Each tool gets a concrete implementation. Adding ChatGPT, Gemini, etc. is just subclassing `ImporterBase`.

---

## Data Flow

### Web Clipper Flow

```
User browses web
       ↓
Selects text + clicks extension
       ↓
Popup shows preview + options
       ↓
User clicks "Save"
       ↓
Extension creates .md file:
  - YAML frontmatter (type: web-clip, url, contributor, tags)
  - Selected text (or page summary)
  - Screenshot (if toggled)
  - URL as clickable link
  - User notes (if any)
       ↓
File written to vault/00-Inbox/
       ↓
Watcher/organizer picks up + files to 15-Web-Clips/
```

### Chat Importer Flow

```
Cron fires (every 2 hours)
       ↓
chat_importers.py runs
       ↓
For each tool (Claude CLI, Copilot):
  - Scan storage location for new chats
  - Parse each chat
  - Convert to markdown + frontmatter
  - Write to vault/00-Inbox/
  - Mark as imported in state file
       ↓
Watcher/organizer picks up + files to 10-LLM-Chats/
```

---

## Vault Structure Changes

### New folder

```
vault/
├── 00-Inbox/           ← staging area
├── 10-LLM-Chats/       ← all LLM chats (web, CLI, Copilot, etc.)
├── 15-Web-Clips/       ← NEW: articles, web pages, saved content
├── 20-Code-Sessions/
├── 30-Research/
├── 40-Experiments/
├── 50-Daily-Logs/
├── 55-Journals/
├── 60-Permanent/
├── _Dashboard/
├── _Scripts/
└── _Templates/
```

### Frontmatter Schema Updates

New optional fields:

```yaml
---
type: daily-log | journal | experiment | code-session | research | llm-chat | web-clip | general
date: 2026-04-10                              # ISO date
contributor: "alice"                          # who created this
summary: "..."                                # one-liner, max 120 chars
status: "in-progress" | "done" | ...          # optional, for some types
tags: [...]                                   # array of strings

# NEW — for web-clips:
url: "https://example.com/article"            # source URL

# NEW — for importers:
tool: "claude-cli" | "copilot" | "web" | ...  # identifies capture source
source_id: "chat_abc123"                      # unique ID in source tool (prevent duplicates)
---
```

### Folder Routing (updated)

| Note type | Destination | Source |
|-----------|-------------|--------|
| `daily-log` | `50-Daily-Logs/` | `log.sh`, manual |
| `journal` | `55-Journals/` | `log.sh`, manual |
| `experiment` | `40-Experiments/` | `log.sh`, manual |
| `code-session` | `20-Code-Sessions/` | Claude Code hook, git hook |
| `research` | `30-Research/` | Manual drop |
| `llm-chat` | `10-LLM-Chats/` | Browser extension, chat importers |
| `web-clip` | `15-Web-Clips/` | NEW: browser extension v2 |
| `general` | `60-Permanent/` | Anything unclassified |

---

## Output Format Examples

### Web Clip

```markdown
---
type: web-clip
date: 2026-04-10
contributor: "alice"
url: "https://arxiv.org/abs/2404.12345"
summary: "Transformer optimization techniques"
tags:
  - "transformers"
  - "optimization"
---

# Article: Transformer Optimization Techniques

**Source:** https://arxiv.org/abs/2404.12345

## Selected Text

> Layer normalization can be moved to the input side without affecting model capacity, potentially speeding up training by 15%.

## Notes

Found this while researching efficient training. Looks like our tokenizer work could benefit from this approach.

## Screenshot

![Screenshot](web-clip-2026-04-10-screenshot.png)
```

### Imported Chat (Claude CLI)

```markdown
---
type: llm-chat
date: 2026-04-10
contributor: "bob"
tool: "claude-cli"
source_id: "claude_chat_xyz789"
summary: "Debugged authentication flow race condition"
tags:
  - "claude-cli"
  - "debugging"
  - "auth"
---

## Chat with Claude

**Bob:** I'm seeing intermittent auth failures in the token refresh flow. Sometimes it works, sometimes I get "token expired" even though it shouldn't.

**Claude:** This sounds like a classic race condition. When you call the refresh endpoint, are you:
1. Making requests before the refresh completes?
2. Keeping old tokens in memory?

**Bob:** Ah, we're doing both. We call refresh asynchronously but don't wait for it. Let me check if we're using the old token...

**Claude:** That's likely it. Try this pattern:
```javascript
const refreshPromise = refreshToken();
const newToken = await refreshPromise;
// Now use newToken
```

**Bob:** That fixed it! The issue was the refresh wasn't awaited. Thanks!
```

### Imported Chat (Copilot)

Same structure as Claude CLI, but `tool: "copilot"`.

---

## Implementation Scope

### Browser Extension

**Files to create:**
- `extension/manifest.json` — extension config
- `extension/popup.html` — popup UI
- `extension/popup.js` — popup logic
- `extension/options.html` — settings page
- `extension/options.js` — settings logic
- `extension/background.js` — file I/O and download handling

**Capabilities:**
- Capture visible tab screenshot (via `chrome.tabs.captureVisibleTab`)
- Save files to configured folder (via `chrome.downloads` API)
- Extract page title, URL, selected text
- Persist settings in `chrome.storage.sync`

### Chat Importers

**Files to create:**
- `scripts/chat_importers.py` — main script
- `scripts/chat_importers/base.py` — `ImporterBase` class
- `scripts/chat_importers/claude_cli.py` — Claude CLI importer
- `scripts/chat_importers/copilot.py` — Copilot importer
- `scripts/chat_importers/state.py` — SQLite state tracking

**Integration points:**
- Update `scripts/setup-organizer.sh` to support `--enable-importers` and `--importer-interval`
- Update `scripts/organizer.py` to handle `tool` and `source_id` frontmatter fields
- Update README with extension setup + importer setup instructions

### Vault & Documentation

**Changes:**
- Create `vault/15-Web-Clips/` folder
- Update `vault/_Templates/` (optional: template for web-clips)
- Update README with new folders and frontmatter schema
- Add extension setup guide
- Add importer developer guide (how to add new tools)

---

## Testing & Validation

**Browser extension:**
- Manual testing: capture text, links, screenshots in various browsers
- Verify files land in `00-Inbox/` with correct format
- Test settings persistence

**Chat importers:**
- Mock Claude CLI and Copilot storage locations
- Verify parsing and markdown conversion
- Test duplicate detection (state file)
- Test cron integration

**Integration:**
- Verify organizer correctly processes web-clips and imported chats
- Verify Obsidian dashboard includes new content
- Test end-to-end: capture web clip → organizer runs → file in correct folder

---

## Success Criteria

- ✅ Browser extension captures text/links/screenshots, saves to inbox
- ✅ Chat importers daemon discovers and imports Claude CLI chats
- ✅ Chat importers daemon discovers and imports Copilot chats
- ✅ Existing organizer processes web clips and imported chats correctly
- ✅ All new notes appear in Obsidian with correct metadata and destination folder
- ✅ No duplicate imports (state tracking works)
- ✅ Framework is extensible (easy to add ChatGPT, Gemini, etc. later)

---

## Out of Scope

- Advanced analytics or reporting
- Collaboration features (comments, reactions)
- AI-generated summaries beyond what organizer already does
- Native app versions of the extension (web only, start with Chrome)

---

## Open Questions

1. **Claude CLI storage:** Where does Claude CLI store chat history? (JSON file, SQLite, or somewhere else?)
2. **Copilot storage:** Same question for Copilot on each OS.
3. **Screenshot size:** Should screenshots be compressed or downsampled to avoid vault bloat?
4. **Web clip summary:** Auto-extract first 200 chars of selection as summary, or let organizer handle it?

These will be researched during implementation.
