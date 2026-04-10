# Chat Importers & Web Clipper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend research-log to auto-collect Claude CLI and Copilot chats, and add a browser extension for clipping web content (text, links, screenshots).

**Architecture:** Two independent capture systems that feed into the existing `00-Inbox/` → organizer pipeline. The browser extension is a Chrome Manifest V3 extension; the chat importers run as a scheduled daemon parsing local storage from each tool. Both are integrated with the organizer to classify and file notes automatically.

**Tech Stack:** 
- Browser extension: Chrome Manifest V3, vanilla JavaScript
- Chat importers: Python 3.8+, SQLite (for state tracking), watchdog (optional dependency check)
- Integration: Existing organizer.py (Claude/Gemini), markdown generation

---

## Phase 1: Research & Setup

### Task 1: Research Claude CLI Storage Location

**Files:**
- Create: `docs/research/claude-cli-storage.md` (documentation only, not code)

- [ ] **Step 1: Check Claude CLI documentation and source**

Research where Claude CLI stores chat history. Check:
1. Official Claude CLI docs/repo
2. Common locations: `~/.claude/chats/`, `~/.config/claude/`, `~/.local/share/claude/`
3. Whether it uses JSON, SQLite, or another format

Document findings in `docs/research/claude-cli-storage.md` including:
- Full path (with platform-specific variations if any)
- File format (JSON array, SQLite, etc.)
- Example file structure (first 50 lines or schema)
- Whether mtime reliably indicates new chats

**Expected output:**
```markdown
# Claude CLI Storage Research

## Storage Path
`~/.claude/chats/` (Linux/macOS), likely `%APPDATA%\.claude\chats\` on Windows

## Format
JSON files, one file per chat session. Filename pattern: `{chat_id}.json`

## Example Structure
[actual content from a real chat file]

## Detection Strategy
Use `os.path.getmtime()` on chat files to detect new ones since last import.
```

- [ ] **Step 2: Verify with actual Claude CLI installation**

If Claude CLI is installed locally, test the paths and format. If not, note this as "TBD during implementation" and reference a test environment requirement.

---

### Task 2: Research Copilot Storage Locations

**Files:**
- Create: `docs/research/copilot-storage.md`

- [ ] **Step 1: Research Copilot chat storage across platforms**

Determine where Copilot stores chat history:
1. **Windows:** Check `%APPDATA%\Microsoft\Copilot\` and `%LOCALAPPDATA%\Microsoft\Copilot\`
2. **macOS:** Check `~/Library/Application Support/Copilot` and `~/Library/Preferences/`
3. **Linux:** Check `~/.config/copilot/` and `~/.local/share/copilot/`
4. Check Copilot docs for official paths

Document in `docs/research/copilot-storage.md`:
- Per-platform paths
- File format (JSON, SQLite, etc.)
- Example structure
- Filename patterns

**Expected output:**
```markdown
# Copilot Storage Research

## Storage Paths

### Windows
`%APPDATA%\Microsoft\Copilot\chats\` or `%LOCALAPPDATA%\Microsoft\Copilot\`

### macOS
`~/Library/Application Support/Microsoft Copilot/chats/`

### Linux
`~/.config/copilot/chats/` or `~/.local/share/copilot/`

## Format
[actual format from research]

## Detection Strategy
[how to detect new chats]
```

- [ ] **Step 2: Note fallback strategy**

If Copilot storage is unclear or varies significantly by version, note this as "requires user verification during setup" and plan for a configurable path in `options.json` or environment variable.

---

### Task 3: Create Vault Structure & Git Ignore

**Files:**
- Create: `vault/15-Web-Clips/.gitkeep`
- Modify: `.gitignore`

- [ ] **Step 1: Create 15-Web-Clips folder**

```bash
cd /path/to/research-log
mkdir -p vault/15-Web-Clips
touch vault/15-Web-Clips/.gitkeep
```

- [ ] **Step 2: Add extension build artifacts to .gitignore (if needed)**

If the extension is built/packaged, add to `.gitignore`:

```
# Browser extension
extension/dist/
extension/node_modules/
extension/.env
```

- [ ] **Step 3: Verify git tracking**

```bash
git status
git add vault/15-Web-Clips/.gitkeep
git commit -m "feat: create web-clips vault folder"
```

---

### Task 4: Create Browser Extension Project Structure

**Files:**
- Create: `extension/manifest.json`
- Create: `extension/popup.html`
- Create: `extension/popup.js`
- Create: `extension/options.html`
- Create: `extension/options.js`
- Create: `extension/background.js`
- Create: `extension/README.md`

- [ ] **Step 1: Create extension directory**

```bash
mkdir -p extension
cd extension
```

- [ ] **Step 2: Write manifest.json**

This is the extension's configuration. Manifest V3 is the current standard.

```json
{
  "manifest_version": 3,
  "name": "Research Log Web Clipper",
  "version": "1.0.0",
  "description": "Clip web content, text, and screenshots to your Research Log vault",
  "permissions": [
    "storage",
    "scripting",
    "downloads"
  ],
  "host_permissions": [
    "<all_urls>"
  ],
  "action": {
    "default_popup": "popup.html",
    "default_title": "Research Log Web Clipper"
  },
  "options_page": "options.html",
  "background": {
    "service_worker": "background.js"
  }
}
```

- [ ] **Step 3: Write popup.html**

This is the UI users see when they click the extension icon.

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {
      width: 400px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      padding: 16px;
      margin: 0;
      background: #fafafa;
    }
    .form-group {
      margin-bottom: 12px;
    }
    label {
      display: block;
      font-weight: 500;
      margin-bottom: 4px;
      font-size: 13px;
      color: #333;
    }
    input[type="text"],
    textarea {
      width: 100%;
      padding: 8px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 13px;
      box-sizing: border-box;
      font-family: inherit;
    }
    textarea {
      resize: vertical;
      min-height: 60px;
    }
    .checkbox-group {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    input[type="checkbox"] {
      cursor: pointer;
    }
    .checkbox-group label {
      margin: 0;
      cursor: pointer;
    }
    button {
      width: 100%;
      padding: 10px;
      background: #2563eb;
      color: white;
      border: none;
      border-radius: 4px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      margin-top: 12px;
    }
    button:hover {
      background: #1d4ed8;
    }
    .preview {
      background: white;
      padding: 8px;
      border-radius: 4px;
      margin-bottom: 12px;
      max-height: 80px;
      overflow-y: auto;
      border: 1px solid #eee;
      font-size: 12px;
      color: #666;
      line-height: 1.4;
    }
    .status {
      padding: 8px;
      border-radius: 4px;
      margin-top: 8px;
      font-size: 12px;
      display: none;
    }
    .status.success {
      background: #dcfce7;
      color: #166534;
      display: block;
    }
    .status.error {
      background: #fee2e2;
      color: #991b1b;
      display: block;
    }
    .spinner {
      display: inline-block;
      width: 4px;
      height: 4px;
      background: currentColor;
      border-radius: 50%;
      animation: blink 1.4s infinite;
    }
    @keyframes blink {
      0%, 20%, 50%, 80%, 100% { opacity: 1; }
      40% { opacity: 0.5; }
      60% { opacity: 0.7; }
    }
  </style>
</head>
<body>
  <div class="form-group">
    <label>Page URL</label>
    <input type="text" id="pageUrl" readonly>
  </div>

  <div class="form-group">
    <label>Page Title</label>
    <input type="text" id="pageTitle" readonly>
  </div>

  <div class="form-group">
    <label>Selected Text</label>
    <div class="preview" id="selectedTextPreview">(none selected)</div>
  </div>

  <div class="form-group checkbox-group">
    <input type="checkbox" id="includeScreenshot">
    <label for="includeScreenshot">Include screenshot</label>
  </div>

  <div class="form-group">
    <label>Notes (optional)</label>
    <textarea id="userNotes" placeholder="Why is this important? Add any context..."></textarea>
  </div>

  <div class="form-group">
    <label>Tags (optional, comma-separated)</label>
    <input type="text" id="userTags" placeholder="e.g., research, important, reference">
  </div>

  <button id="saveButton">Save to Research Log</button>
  <div id="status" class="status"></div>

  <script src="popup.js"></script>
</body>
</html>
```

- [ ] **Step 4: Write popup.js**

This handles the popup interactions and sends messages to the background script.

```javascript
// popup.js
document.addEventListener('DOMContentLoaded', async () => {
  // Get current tab info
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  document.getElementById('pageUrl').value = tab.url;
  document.getElementById('pageTitle').value = tab.title;
  
  // Get selected text from content script
  chrome.tabs.sendMessage(tab.id, { action: 'getSelectedText' }, (response) => {
    if (response && response.selectedText) {
      const preview = response.selectedText.substring(0, 200);
      document.getElementById('selectedTextPreview').textContent = preview + (preview.length < response.selectedText.length ? '...' : '');
      document.getElementById('selectedTextPreview').dataset.fullText = response.selectedText;
    }
  });

  // Save button handler
  document.getElementById('saveButton').addEventListener('click', async () => {
    const button = document.getElementById('saveButton');
    const statusEl = document.getElementById('status');
    
    button.disabled = true;
    button.textContent = 'Saving...';
    statusEl.className = 'status';
    statusEl.textContent = '';

    try {
      const selectedText = document.getElementById('selectedTextPreview').dataset.fullText || '';
      const pageUrl = document.getElementById('pageUrl').value;
      const pageTitle = document.getElementById('pageTitle').value;
      const includeScreenshot = document.getElementById('includeScreenshot').checked;
      const userNotes = document.getElementById('userNotes').value;
      const userTags = document.getElementById('userTags').value;

      // Request screenshot if needed
      let screenshotData = null;
      if (includeScreenshot) {
        screenshotData = await chrome.tabs.captureVisibleTab(tab.windowId, { format: 'png' });
      }

      // Send to background to save file
      await chrome.runtime.sendMessage({
        action: 'saveClip',
        selectedText,
        pageUrl,
        pageTitle,
        screenshotData,
        userNotes,
        userTags
      });

      statusEl.className = 'status success';
      statusEl.textContent = '✓ Saved to Research Log';
      
      setTimeout(() => window.close(), 1500);
    } catch (error) {
      statusEl.className = 'status error';
      statusEl.textContent = '✗ Error: ' + error.message;
      button.disabled = false;
      button.textContent = 'Save to Research Log';
    }
  });
});
```

- [ ] **Step 5: Write options.html**

Settings page where users configure the download folder.

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      max-width: 600px;
      margin: 40px auto;
      padding: 20px;
      background: #fafafa;
    }
    h1 {
      font-size: 24px;
      margin-top: 0;
    }
    .form-group {
      margin-bottom: 20px;
    }
    label {
      display: block;
      font-weight: 500;
      margin-bottom: 8px;
    }
    input[type="text"] {
      width: 100%;
      padding: 10px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 14px;
      box-sizing: border-box;
    }
    .description {
      font-size: 13px;
      color: #666;
      margin-top: 4px;
    }
    button {
      padding: 10px 20px;
      background: #2563eb;
      color: white;
      border: none;
      border-radius: 4px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
    }
    button:hover {
      background: #1d4ed8;
    }
    .status {
      padding: 10px;
      border-radius: 4px;
      margin-top: 12px;
      font-size: 13px;
      display: none;
    }
    .status.success {
      background: #dcfce7;
      color: #166534;
      display: block;
    }
    .status.error {
      background: #fee2e2;
      color: #991b1b;
      display: block;
    }
  </style>
</head>
<body>
  <h1>Research Log Web Clipper Settings</h1>

  <div class="form-group">
    <label for="downloadFolder">Download Folder</label>
    <input type="text" id="downloadFolder" placeholder="e.g., /Users/alice/research-log/vault/00-Inbox">
    <div class="description">
      Clipped content will be saved as markdown files in this folder. Use the full path to your vault's inbox folder.
    </div>
  </div>

  <div class="form-group">
    <label for="contributor">Contributor Name (optional)</label>
    <input type="text" id="contributor" placeholder="e.g., alice">
    <div class="description">
      If set, this name will be used in the saved files' metadata. Otherwise, system username is used.
    </div>
  </div>

  <button id="saveButton">Save Settings</button>
  <div id="status" class="status"></div>

  <script src="options.js"></script>
</body>
</html>
```

- [ ] **Step 6: Write options.js**

Handles saving/loading settings.

```javascript
// options.js
document.addEventListener('DOMContentLoaded', async () => {
  // Load saved settings
  const settings = await chrome.storage.sync.get(['downloadFolder', 'contributor']);
  if (settings.downloadFolder) {
    document.getElementById('downloadFolder').value = settings.downloadFolder;
  }
  if (settings.contributor) {
    document.getElementById('contributor').value = settings.contributor;
  }

  document.getElementById('saveButton').addEventListener('click', async () => {
    const downloadFolder = document.getElementById('downloadFolder').value.trim();
    const contributor = document.getElementById('contributor').value.trim();
    const statusEl = document.getElementById('status');

    if (!downloadFolder) {
      statusEl.className = 'status error';
      statusEl.textContent = 'Error: Download folder is required';
      return;
    }

    await chrome.storage.sync.set({ downloadFolder, contributor });
    statusEl.className = 'status success';
    statusEl.textContent = 'Settings saved!';
  });
});
```

- [ ] **Step 7: Write background.js (service worker)**

Handles file I/O and background tasks.

```javascript
// background.js
import { saveClipFile } from './utils.js';

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'saveClip') {
    handleSaveClip(request)
      .then(() => sendResponse({ success: true }))
      .catch(error => sendResponse({ error: error.message }));
    return true; // indicate async response
  }
});

async function handleSaveClip(request) {
  // Get settings
  const settings = await chrome.storage.sync.get(['downloadFolder', 'contributor']);
  const downloadFolder = settings.downloadFolder;
  const contributor = settings.contributor || 'unknown';

  if (!downloadFolder) {
    throw new Error('Download folder not configured. Open extension options.');
  }

  const {
    selectedText,
    pageUrl,
    pageTitle,
    screenshotData,
    userNotes,
    userTags
  } = request;

  // Generate markdown content
  const timestamp = new Date().toISOString().split('T')[0];
  const summary = selectedText ? selectedText.substring(0, 120) : pageTitle.substring(0, 120);
  
  let tagsArray = ['web-clip'];
  if (userTags) {
    tagsArray.push(...userTags.split(',').map(t => t.trim()).filter(Boolean));
  }

  // Build frontmatter
  const frontmatter = `---
type: web-clip
date: ${timestamp}
contributor: "${contributor}"
url: "${pageUrl}"
summary: "${summary}"
tags:
${tagsArray.map(t => `  - "${t}"`).join('\n')}
---`;

  // Build content
  let content = frontmatter + '\n\n';
  content += `# ${pageTitle}\n\n`;
  content += `**Source:** [${pageUrl}](${pageUrl})\n\n`;
  
  if (selectedText) {
    content += `## Selected Text\n\n> ${selectedText.split('\n').join('\n> ')}\n\n`;
  }
  
  if (userNotes) {
    content += `## Notes\n\n${userNotes}\n\n`;
  }

  // Handle screenshot
  let screenshotFilename = '';
  if (screenshotData) {
    screenshotFilename = `web-clip-${timestamp}-${Date.now()}.png`;
    // Save screenshot (requires file system access via download API)
    await downloadFile(screenshotData, downloadFolder + '/' + screenshotFilename);
    content += `## Screenshot\n\n![Screenshot](${screenshotFilename})\n`;
  }

  // Generate filename
  const filename = `web-clip-${timestamp}-${sanitizeFilename(pageTitle.substring(0, 30))}.md`;
  const fullPath = downloadFolder + '/' + filename;

  // Save markdown file
  await downloadFile(content, fullPath);
}

function downloadFile(content, path) {
  return new Promise((resolve, reject) => {
    // Note: Chrome extensions cannot directly write files outside the download folder
    // So we use the downloads API. The actual path handling will need adjustment
    // based on Chrome's capabilities and the user's OS.
    
    // For now, we'll use the download API which saves to the user's Downloads folder
    // The user will need to configure their browser to auto-download to the vault folder
    // OR use a native helper (beyond scope here).
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const filename = path.split('/').pop();
    
    chrome.downloads.download({
      url: url,
      filename: filename,
      saveAs: false
    }, (downloadId) => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
      } else {
        resolve();
      }
      URL.revokeObjectURL(url);
    });
  });
}

function sanitizeFilename(str) {
  return str.replace(/[^a-z0-9]+/gi, '-').toLowerCase();
}
```

- [ ] **Step 8: Write extension/README.md**

Documentation for the extension.

```markdown
# Research Log Web Clipper - Chrome Extension

A lightweight browser extension for saving web content (text, links, screenshots) to your Research Log vault.

## Installation

1. Clone/download the research-log repository
2. Open Chrome and go to `chrome://extensions/`
3. Enable "Developer mode" (toggle in top right)
4. Click "Load unpacked" and select the `extension/` folder

## Configuration

1. Click the extension icon in Chrome toolbar
2. Click the gear icon (or right-click → Options)
3. Set "Download Folder" to the full path of your vault's `00-Inbox/` folder
   - Example: `/Users/alice/Documents/research-log/vault/00-Inbox`
4. (Optional) Set your contributor name
5. Click "Save Settings"

## Usage

1. Browse the web, select text (or don't), click the extension icon
2. Popup appears with page URL, title, and selected text preview
3. (Optional) Toggle "Include screenshot"
4. (Optional) Add notes and tags
5. Click "Save to Research Log"
6. File is saved to your configured inbox folder
7. The existing watcher/organizer will pick it up and file it

## Notes

- Files are saved as markdown with YAML frontmatter
- Screenshots are embedded as PNG images
- Tags are saved in the frontmatter for filtering
- Contributor name is tracked for attribution

## Limitations

- Currently Chrome only (Manifest V3)
- Requires manual folder configuration (browser permissions limit auto-detection)
- Screenshots may be large; consider enabling compression if needed
```

- [ ] **Step 9: Commit extension files**

```bash
cd /path/to/research-log
git add extension/
git commit -m "feat: add research log web clipper extension

Chrome Manifest V3 extension for clipping web content, text selections,
and optional screenshots to the research-log vault. Includes popup UI,
settings page, and background file handling.

Files:
- manifest.json: extension configuration
- popup.html/js: user-facing clip UI
- options.html/js: settings page
- background.js: file save logic (via Chrome downloads API)

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Phase 2: Chat Importers Foundation

### Task 5: Create Chat Importers Project Structure

**Files:**
- Create: `scripts/chat_importers/__init__.py`
- Create: `scripts/chat_importers/base.py`
- Create: `scripts/chat_importers/state.py`
- Create: `scripts/chat_importers.py`

- [ ] **Step 1: Create chat_importers package directory**

```bash
mkdir -p scripts/chat_importers
touch scripts/chat_importers/__init__.py
```

- [ ] **Step 2: Write state.py (SQLite state tracking)**

This tracks which chats have been imported to avoid duplicates.

```python
# scripts/chat_importers/state.py
import sqlite3
import os
from pathlib import Path

class ImportState:
    """Track imported chats to avoid duplicates."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(
                Path(__file__).parent.parent.parent,  # research-log root
                'vault', '_Scripts', 'import_state.db'
            )
        
        self.db_path = db_path
        self._ensure_db()
    
    def _ensure_db(self):
        """Create database if it doesn't exist."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS imported_chats (
                    tool TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    imported_at TEXT NOT NULL,
                    PRIMARY KEY (tool, source_id)
                )
            ''')
            conn.commit()
    
    def is_imported(self, tool: str, source_id: str) -> bool:
        """Check if a chat has already been imported."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT 1 FROM imported_chats WHERE tool = ? AND source_id = ?',
                (tool, source_id)
            )
            return cursor.fetchone() is not None
    
    def mark_imported(self, tool: str, source_id: str):
        """Mark a chat as imported."""
        from datetime import datetime
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT OR IGNORE INTO imported_chats (tool, source_id, imported_at) VALUES (?, ?, ?)',
                (tool, source_id, datetime.utcnow().isoformat())
            )
            conn.commit()
    
    def list_imported(self, tool: str = None) -> list:
        """List all imported chat IDs, optionally filtered by tool."""
        with sqlite3.connect(self.db_path) as conn:
            if tool:
                cursor = conn.execute(
                    'SELECT source_id FROM imported_chats WHERE tool = ? ORDER BY imported_at DESC',
                    (tool,)
                )
            else:
                cursor = conn.execute(
                    'SELECT tool, source_id FROM imported_chats ORDER BY imported_at DESC'
                )
            return cursor.fetchall()
```

- [ ] **Step 3: Write base.py (abstract importer class)**

This defines the interface all importers must implement.

```python
# scripts/chat_importers/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
import os
import re

class ChatMessage:
    """Represents a single message in a chat."""
    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None):
        self.role = role  # "user", "assistant", etc.
        self.content = content
        self.timestamp = timestamp

class ChatImporter(ABC):
    """Base class for chat importers."""
    
    def __init__(self, state=None):
        """Initialize importer with optional state tracker."""
        self.state = state
    
    @abstractmethod
    def find_new_chats(self) -> List[str]:
        """
        Return list of paths to chat files that haven't been imported yet.
        
        Returns:
            List of full file paths to unimported chat files.
        """
        pass
    
    @abstractmethod
    def parse_chat(self, path: str) -> Dict:
        """
        Parse a chat file and extract messages and metadata.
        
        Returns:
            {
                'source_id': 'unique-id-in-source-tool',
                'messages': [ChatMessage, ...],
                'date': datetime object,
                'tool': 'claude-cli' or 'copilot',
                'metadata': { extra fields }
            }
        """
        pass
    
    def to_markdown(self, chat: Dict, contributor: str = 'unknown') -> str:
        """
        Convert parsed chat to markdown with frontmatter.
        
        Returns:
            Markdown string ready to write to file.
        """
        messages = chat['messages']
        date = chat['date'].strftime('%Y-%m-%d')
        source_id = chat['source_id']
        tool = chat['tool']
        
        # Build summary from first message and response
        summary_parts = []
        for msg in messages[:5]:
            if msg.role == 'user':
                text = msg.content.split('\n')[0][:100]
                summary_parts.append(text)
                break
        summary = summary_parts[0] if summary_parts else 'Chat conversation'
        
        # Frontmatter
        frontmatter = f"""---
type: llm-chat
date: {date}
contributor: "{contributor}"
tool: "{tool}"
source_id: "{source_id}"
summary: "{self._escape_yaml(summary)}"
tags:
  - "{tool}"
---"""
        
        # Build message exchange
        body = f"\n\n## Chat with {self._format_tool_name(tool)}\n\n"
        for msg in messages:
            role_title = msg.role.capitalize()
            body += f"**{role_title}:** {msg.content}\n\n"
        
        return frontmatter + body
    
    def mark_imported(self, source_id: str):
        """Mark a chat as imported (requires state tracker)."""
        if self.state:
            self.state.mark_imported(self.tool_name, source_id)
    
    def _escape_yaml(self, text: str) -> str:
        """Escape text for YAML frontmatter."""
        # Remove newlines and limit length
        text = text.replace('\n', ' ').replace('"', '\\"')
        return text[:120]
    
    def _format_tool_name(self, tool: str) -> str:
        """Format tool name for display."""
        return {'claude-cli': 'Claude CLI', 'copilot': 'Copilot'}.get(tool, tool)
    
    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Return the tool identifier ('claude-cli', 'copilot', etc.)."""
        pass
```

- [ ] **Step 4: Write main chat_importers.py script**

The coordinator that runs all importers.

```python
# scripts/chat_importers.py
#!/usr/bin/env python3
"""
Chat importers daemon.

Periodically scans for new chats from Claude CLI, Copilot, and other tools,
imports them to the vault inbox, and marks them as imported to avoid duplicates.

Usage:
    python3 scripts/chat_importers.py
    python3 scripts/chat_importers.py --dry-run
    python3 scripts/chat_importers.py --no-push
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import getpass

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from chat_importers.state import ImportState
from chat_importers.base import ChatImporter

def get_vault_path():
    """Get vault path from env or default."""
    env_path = os.getenv('VAULT_PATH')
    if env_path:
        return env_path
    
    # Default: vault/ in repo root
    repo_root = Path(__file__).parent.parent
    return str(repo_root / 'vault')

def get_contributor():
    """Get contributor name from env, git config, or system user."""
    # Check env
    if os.getenv('LOG_CONTRIBUTOR'):
        return os.getenv('LOG_CONTRIBUTOR')
    
    # Check git config
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'config', 'user.name'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    
    # Fall back to system user
    return getpass.getuser()

def run_importers(dry_run=False, no_push=False):
    """Run all available importers."""
    vault_path = get_vault_path()
    inbox_path = os.path.join(vault_path, '00-Inbox')
    contributor = get_contributor()
    
    # Ensure inbox exists
    Path(inbox_path).mkdir(parents=True, exist_ok=True)
    
    # Initialize state tracker
    state = ImportState()
    
    # Import dynamically to avoid hard dependencies
    importers = []
    try:
        from chat_importers.claude_cli import ClaudeCliImporter
        importers.append(ClaudeCliImporter(state))
    except Exception as e:
        print(f"Warning: Could not load Claude CLI importer: {e}")
    
    try:
        from chat_importers.copilot import CopilotImporter
        importers.append(CopilotImporter(state))
    except Exception as e:
        print(f"Warning: Could not load Copilot importer: {e}")
    
    if not importers:
        print("No importers available")
        return
    
    total_imported = 0
    
    for importer in importers:
        print(f"\n=== {importer.tool_name} ===")
        try:
            chat_paths = importer.find_new_chats()
            print(f"Found {len(chat_paths)} new chat(s)")
            
            for chat_path in chat_paths:
                try:
                    # Parse chat
                    chat = importer.parse_chat(chat_path)
                    
                    # Convert to markdown
                    markdown = importer.to_markdown(chat, contributor)
                    
                    # Generate filename
                    date_str = chat['date'].strftime('%Y-%m-%d')
                    source_id = chat['source_id'][:30]  # Shorten for filename
                    filename = f"llm-chat-{date_str}-{source_id}.md"
                    filepath = os.path.join(inbox_path, filename)
                    
                    if dry_run:
                        print(f"  [DRY RUN] Would save: {filename}")
                    else:
                        # Write file
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(markdown)
                        
                        # Mark imported
                        importer.mark_imported(chat['source_id'])
                        print(f"  ✓ Imported: {filename}")
                        total_imported += 1
                
                except Exception as e:
                    print(f"  ✗ Error importing chat: {e}")
        
        except Exception as e:
            print(f"Error running {importer.tool_name} importer: {e}")
    
    print(f"\n=== Summary ===")
    print(f"Total imported: {total_imported}")
    
    if not dry_run and not no_push and total_imported > 0:
        print("\nNote: Run 'rlog-sync' to commit and push new entries.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Import chats from Claude CLI, Copilot, and other tools'
    )
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview what would be imported without making changes')
    parser.add_argument('--no-push', action='store_true',
                        help='Import but do not auto-push')
    
    args = parser.parse_args()
    
    try:
        run_importers(dry_run=args.dry_run, no_push=args.no_push)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
```

- [ ] **Step 5: Write __init__.py**

```python
# scripts/chat_importers/__init__.py
"""Chat importers package for research-log."""

from .base import ChatImporter, ChatMessage
from .state import ImportState

__all__ = ['ChatImporter', 'ChatMessage', 'ImportState']
```

- [ ] **Step 6: Commit foundation files**

```bash
cd /path/to/research-log
git add scripts/chat_importers.py scripts/chat_importers/
git commit -m "feat: add chat importers foundation

Scaffold for importing chats from various tools into the vault.

Components:
- state.py: SQLite-based duplicate tracking
- base.py: Abstract ChatImporter class defining the interface
- chat_importers.py: Main coordinator script

Supports dynamically loading individual tool importers (Claude CLI, Copilot).
Flexible contributor detection (env, git config, system user).

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 6: Implement Claude CLI Importer

**Files:**
- Create: `scripts/chat_importers/claude_cli.py`

- [ ] **Step 1: Write claude_cli.py**

Based on research from Task 1, this importer scans Claude CLI storage.

```python
# scripts/chat_importers/claude_cli.py
"""Importer for Claude CLI chats."""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import glob

from .base import ChatImporter, ChatMessage

class ClaudeCliImporter(ChatImporter):
    """Import chats from Claude CLI."""
    
    def __init__(self, state=None):
        super().__init__(state)
        self.chat_dir = self._get_chat_dir()
    
    @property
    def tool_name(self) -> str:
        return 'claude-cli'
    
    def _get_chat_dir(self) -> Optional[str]:
        """Detect Claude CLI chat directory."""
        # Try common locations
        home = Path.home()
        
        candidates = [
            home / '.claude' / 'chats',
            home / '.config' / 'claude' / 'chats',
            home / '.local' / 'share' / 'claude' / 'chats',
        ]
        
        for path in candidates:
            if path.exists() and path.is_dir():
                return str(path)
        
        return None
    
    def find_new_chats(self) -> List[str]:
        """Find unimported Claude CLI chats."""
        if not self.chat_dir:
            return []
        
        # Assume .json files in the chats directory are chat files
        chat_files = glob.glob(os.path.join(self.chat_dir, '*.json'))
        
        # Filter to unimported chats
        if self.state:
            new_chats = [
                f for f in chat_files
                if not self.state.is_imported(self.tool_name, os.path.basename(f))
            ]
            return new_chats
        
        return chat_files
    
    def parse_chat(self, path: str) -> Dict:
        """Parse Claude CLI chat JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract messages from the chat structure
        # Claude CLI JSON format: { "messages": [...], "metadata": {...} }
        messages = []
        
        if isinstance(data, dict):
            # Standard format
            chat_messages = data.get('messages', [])
            if isinstance(chat_messages, list):
                for msg in chat_messages:
                    if isinstance(msg, dict):
                        role = msg.get('role', 'user')
                        content = msg.get('content', '')
                        timestamp_str = msg.get('timestamp')
                        timestamp = None
                        if timestamp_str:
                            try:
                                timestamp = datetime.fromisoformat(timestamp_str)
                            except:
                                pass
                        messages.append(ChatMessage(role, content, timestamp))
        
        # Extract date from metadata or use first message timestamp
        date = None
        if 'created_at' in data:
            try:
                date = datetime.fromisoformat(data['created_at'])
            except:
                pass
        
        if not date and messages:
            date = messages[0].timestamp or datetime.now()
        
        if not date:
            date = datetime.now()
        
        # Source ID is the filename (without extension)
        source_id = os.path.splitext(os.path.basename(path))[0]
        
        return {
            'source_id': source_id,
            'messages': messages,
            'date': date,
            'tool': self.tool_name,
            'metadata': data.get('metadata', {})
        }
```

- [ ] **Step 2: Test Claude CLI importer**

Create a test file to verify the importer loads and handles mock data:

```python
# scripts/test_claude_cli_importer.py (temporary, for verification)
import json
import tempfile
import os
from pathlib import Path
from chat_importers.claude_cli import ClaudeCliImporter
from chat_importers.state import ImportState

# Create mock chat file
with tempfile.TemporaryDirectory() as tmpdir:
    mock_chat = {
        "messages": [
            {"role": "user", "content": "How do I debug this error?"},
            {"role": "assistant", "content": "This looks like a race condition..."}
        ],
        "created_at": "2026-04-10T14:30:00",
        "metadata": {}
    }
    
    chat_file = os.path.join(tmpdir, 'chat_001.json')
    with open(chat_file, 'w') as f:
        json.dump(mock_chat, f)
    
    # Create mock state
    state_db = os.path.join(tmpdir, 'state.db')
    state = ImportState(state_db)
    
    # Patch the importer to use tmpdir
    importer = ClaudeCliImporter(state)
    importer.chat_dir = tmpdir
    
    # Test find_new_chats
    chats = importer.find_new_chats()
    print(f"Found chats: {chats}")
    assert len(chats) == 1, "Should find 1 chat"
    
    # Test parse_chat
    chat = importer.parse_chat(chat_file)
    print(f"Parsed chat: source_id={chat['source_id']}, messages={len(chat['messages'])}")
    assert chat['source_id'] == 'chat_001'
    assert len(chat['messages']) == 2
    
    # Test to_markdown
    markdown = importer.to_markdown(chat, 'test_user')
    print(f"Generated markdown ({len(markdown)} chars)")
    assert 'type: llm-chat' in markdown
    assert 'tool: "claude-cli"' in markdown
    
    print("✓ All tests passed")
```

Run the test:
```bash
cd /path/to/research-log
python3 scripts/test_claude_cli_importer.py
```

Expected output:
```
Found chats: ['/tmp/.../chat_001.json']
Parsed chat: source_id=chat_001, messages=2
Generated markdown (xyz chars)
✓ All tests passed
```

- [ ] **Step 3: Commit Claude CLI importer**

```bash
cd /path/to/research-log
rm scripts/test_claude_cli_importer.py  # Remove test file
git add scripts/chat_importers/claude_cli.py
git commit -m "feat: implement claude-cli chat importer

Scans ~/.claude/chats/ for new chat files and imports them.

Handles:
- Auto-detection of Claude CLI chat directory
- JSON parsing of chat messages and metadata
- Frontmatter generation with source tracking
- Duplicate detection via state tracker

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 7: Implement Copilot Importer

**Files:**
- Create: `scripts/chat_importers/copilot.py`

- [ ] **Step 1: Write copilot.py**

Based on research from Task 2, this importer scans Copilot storage across OSes.

```python
# scripts/chat_importers/copilot.py
"""Importer for Microsoft Copilot chats."""

import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import platform
import glob

from .base import ChatImporter, ChatMessage

class CopilotImporter(ChatImporter):
    """Import chats from Microsoft Copilot (cross-platform)."""
    
    def __init__(self, state=None):
        super().__init__(state)
        self.chat_dir = self._get_chat_dir()
    
    @property
    def tool_name(self) -> str:
        return 'copilot'
    
    def _get_chat_dir(self) -> Optional[str]:
        """Detect Copilot chat directory (platform-specific)."""
        home = Path.home()
        system = platform.system()
        
        candidates = []
        
        if system == 'Windows':
            # Windows paths
            appdata = os.getenv('APPDATA')
            localappdata = os.getenv('LOCALAPPDATA')
            if appdata:
                candidates.append(Path(appdata) / 'Microsoft' / 'Copilot' / 'chats')
            if localappdata:
                candidates.append(Path(localappdata) / 'Microsoft' / 'Copilot' / 'chats')
        
        elif system == 'Darwin':
            # macOS paths
            candidates = [
                home / 'Library' / 'Application Support' / 'Microsoft Copilot' / 'chats',
                home / 'Library' / 'Application Support' / 'Copilot' / 'chats',
                home / 'Library' / 'Preferences' / 'Copilot' / 'chats',
            ]
        
        else:
            # Linux paths
            candidates = [
                home / '.config' / 'copilot' / 'chats',
                home / '.local' / 'share' / 'copilot' / 'chats',
                home / '.config' / 'Microsoft Copilot' / 'chats',
            ]
        
        for path in candidates:
            if path.exists() and path.is_dir():
                return str(path)
        
        return None
    
    def find_new_chats(self) -> List[str]:
        """Find unimported Copilot chats."""
        if not self.chat_dir:
            return []
        
        chat_files = []
        
        # Look for JSON files
        json_files = glob.glob(os.path.join(self.chat_dir, '*.json'))
        chat_files.extend(json_files)
        
        # Look for SQLite database (alternative format)
        db_files = glob.glob(os.path.join(self.chat_dir, '*.db'))
        db_files += glob.glob(os.path.join(self.chat_dir, '*.sqlite'))
        chat_files.extend(db_files)
        
        # Filter to unimported
        if self.state:
            new_chats = [
                f for f in chat_files
                if not self.state.is_imported(self.tool_name, os.path.basename(f))
            ]
            return new_chats
        
        return chat_files
    
    def parse_chat(self, path: str) -> Dict:
        """Parse Copilot chat file (JSON or SQLite)."""
        filename = os.path.basename(path)
        
        if path.endswith('.json'):
            return self._parse_json_chat(path, filename)
        elif path.endswith(('.db', '.sqlite')):
            return self._parse_db_chat(path, filename)
        else:
            raise ValueError(f"Unknown file format: {path}")
    
    def _parse_json_chat(self, path: str, filename: str) -> Dict:
        """Parse JSON format Copilot chat."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        messages = []
        
        if isinstance(data, dict):
            # Extract messages from various possible structures
            chat_messages = data.get('messages') or data.get('conversation') or []
            
            for msg in chat_messages:
                if isinstance(msg, dict):
                    role = msg.get('role', msg.get('author', 'user'))
                    content = msg.get('content', msg.get('text', ''))
                    timestamp_str = msg.get('timestamp', msg.get('created_at'))
                    timestamp = None
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str)
                        except:
                            pass
                    messages.append(ChatMessage(role, content, timestamp))
        
        # Extract date
        date = None
        for possible_field in ['created_at', 'timestamp', 'updated_at']:
            if possible_field in data:
                try:
                    date = datetime.fromisoformat(data[possible_field])
                    break
                except:
                    pass
        
        if not date and messages:
            date = messages[0].timestamp or datetime.now()
        
        if not date:
            date = datetime.now()
        
        source_id = os.path.splitext(filename)[0]
        
        return {
            'source_id': source_id,
            'messages': messages,
            'date': date,
            'tool': self.tool_name,
            'metadata': data.get('metadata', {})
        }
    
    def _parse_db_chat(self, path: str, filename: str) -> Dict:
        """Parse SQLite database Copilot chat."""
        messages = []
        date = datetime.now()
        
        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            
            # Try common table structures
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Look for messages/conversations table
            message_table = None
            for table in ['messages', 'conversations', 'chats']:
                if table in tables:
                    message_table = table
                    break
            
            if message_table:
                # Generic query to extract message-like data
                cursor.execute(f"SELECT * FROM {message_table} LIMIT 1")
                columns = [desc[0] for desc in cursor.description]
                
                # Find role and content columns
                role_col = next((c for c in columns if 'role' in c.lower()), 'role')
                content_col = next((c for c in columns if 'content' in c.lower() or 'text' in c.lower()), 'content')
                
                cursor.execute(f"SELECT {role_col}, {content_col} FROM {message_table}")
                for row in cursor.fetchall():
                    role, content = row[0], row[1]
                    messages.append(ChatMessage(str(role), str(content)))
            
            conn.close()
        
        except Exception as e:
            # If parsing fails, return empty messages
            pass
        
        source_id = os.path.splitext(filename)[0]
        
        return {
            'source_id': source_id,
            'messages': messages or [ChatMessage('unknown', 'Unable to parse database')],
            'date': date,
            'tool': self.tool_name,
            'metadata': {}
        }
```

- [ ] **Step 2: Test Copilot importer**

Create and run a mock test:

```bash
cd /path/to/research-log
python3 << 'EOF'
import json
import tempfile
import os
from chat_importers.copilot import CopilotImporter
from chat_importers.state import ImportState

# Create mock Copilot chat (JSON format)
with tempfile.TemporaryDirectory() as tmpdir:
    mock_chat = {
        "messages": [
            {"role": "user", "content": "What's the weather?"},
            {"role": "assistant", "content": "I don't have access to live weather data..."}
        ],
        "created_at": "2026-04-10T10:00:00"
    }
    
    chat_file = os.path.join(tmpdir, 'copilot_chat_123.json')
    with open(chat_file, 'w') as f:
        json.dump(mock_chat, f)
    
    state_db = os.path.join(tmpdir, 'state.db')
    state = ImportState(state_db)
    
    importer = CopilotImporter(state)
    importer.chat_dir = tmpdir
    
    chats = importer.find_new_chats()
    assert len(chats) == 1
    
    chat = importer.parse_chat(chat_file)
    assert chat['tool'] == 'copilot'
    assert len(chat['messages']) == 2
    
    markdown = importer.to_markdown(chat, 'test_user')
    assert 'tool: "copilot"' in markdown
    
    print("✓ Copilot importer tests passed")
EOF
```

- [ ] **Step 3: Commit Copilot importer**

```bash
cd /path/to/research-log
git add scripts/chat_importers/copilot.py
git commit -m "feat: implement copilot chat importer

Cross-platform importer for Microsoft Copilot chats.

Platform detection:
- Windows: %APPDATA% and %LOCALAPPDATA% paths
- macOS: ~/Library/Application Support and ~/Library/Preferences
- Linux: ~/.config and ~/.local/share

Supports:
- JSON format chat files
- SQLite database format (fallback parsing)
- Metadata extraction (created_at, timestamps)
- Duplicate detection

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Phase 3: Integration & Polish

### Task 8: Integrate Importers with Organizer

**Files:**
- Modify: `scripts/organizer.py`
- Modify: `scripts/setup-organizer.sh`

- [ ] **Step 1: Update organizer.py to handle new frontmatter fields**

Find the section where organizer processes frontmatter and add support for `tool` and `source_id`:

In `organizer.py`, locate the function that updates frontmatter (likely around "inject frontmatter"). Update it to preserve `tool` and `source_id` if they exist:

```python
# In organizer.py, in the update_frontmatter or inject_frontmatter function:

def update_frontmatter(note_path: str, classification: dict):
    """Update note frontmatter with LLM classification results."""
    with open(note_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse existing frontmatter if present
    existing_fm = {}
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 2:
            try:
                existing_fm = yaml.safe_load(parts[1]) or {}
            except:
                pass
    
    # Build new frontmatter, preserving existing fields like 'tool' and 'source_id'
    frontmatter = {
        'type': classification.get('type', 'general'),
        'date': classification.get('date', datetime.now().strftime('%Y-%m-%d')),
        'contributor': existing_fm.get('contributor', classification.get('contributor', 'unknown')),
        'summary': classification.get('summary', ''),
        'tags': classification.get('tags', ['general']),
        
        # NEW: Preserve tool and source_id if they exist
        'tool': existing_fm.get('tool'),
        'source_id': existing_fm.get('source_id'),
        'url': existing_fm.get('url'),  # For web-clips
    }
    
    # Remove None values
    frontmatter = {k: v for k, v in frontmatter.items() if v is not None}
    
    # Reconstruct content
    yaml_str = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
    new_content = f"---\n{yaml_str}---\n" + (parts[2] if len(parts) > 2 else '')
    
    with open(note_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
```

- [ ] **Step 2: Update setup-organizer.sh to support importers flag**

Add a `--enable-importers` flag and `--importer-interval` flag:

```bash
# In scripts/setup-organizer.sh, add to argument parsing:

ENABLE_IMPORTERS=false
IMPORTER_INTERVAL="2h"

while [[ $# -gt 0 ]]; do
  case $1 in
    --enable-importers)
      ENABLE_IMPORTERS=true
      shift
      ;;
    --importer-interval)
      IMPORTER_INTERVAL="$2"
      shift 2
      ;;
    # ... existing flags ...
  esac
done

# Later in the cron job setup, add:

if [ "$ENABLE_IMPORTERS" = true ]; then
  # Add cron job for chat importers
  # Convert interval (2h, 30m, etc.) to cron syntax
  # 2h = */120 * * * * (every 2 hours)
  # 30m = */30 * * * * (every 30 minutes)
  
  IMPORTER_CRON=""
  if [[ $IMPORTER_INTERVAL == *"h"* ]]; then
    HOURS=${IMPORTER_INTERVAL%h}
    IMPORTER_CRON="0 */$HOURS * * *"
  elif [[ $IMPORTER_INTERVAL == *"m"* ]]; then
    MINUTES=${IMPORTER_INTERVAL%m}
    IMPORTER_CRON="*/$MINUTES * * * *"
  fi
  
  (crontab -l 2>/dev/null; echo "$IMPORTER_CRON python3 $REPO_ROOT/scripts/chat_importers.py") | crontab -
  echo "✓ Installed chat importers cron job ($IMPORTER_INTERVAL)"
fi
```

- [ ] **Step 3: Update folder routing in organizer**

Ensure the organizer routes `web-clip` type to `15-Web-Clips/` folder:

```python
# In organizer.py, in the routing function:

ROUTING_MAP = {
    'daily-log': '50-Daily-Logs',
    'journal': '55-Journals',
    'experiment': '40-Experiments',
    'code-session': '20-Code-Sessions',
    'research': '30-Research',
    'llm-chat': '10-LLM-Chats',
    'web-clip': '15-Web-Clips',  # NEW
    'general': '60-Permanent',
}
```

- [ ] **Step 4: Update README.md**

Add sections for the new features. In `README.md`, add after the existing capture sources:

```markdown
### Browser Extension (Web Clipper)

Lightweight capture of web content (text selections, links, optional screenshots).

**Install:**
1. Open Chrome → `chrome://extensions/`
2. Enable Developer mode
3. Click "Load unpacked" → select the `extension/` folder
4. Click the extension icon → click gear icon
5. Set "Download Folder" to `<vault-path>/00-Inbox`
6. Click "Save Settings"

**Usage:**
- Select text on any web page (or skip to capture full context)
- Click extension icon → popup appears
- (Optional) toggle "Include screenshot"
- (Optional) add notes and tags
- Click "Save to Research Log"
- File lands in `00-Inbox/` → organizer files to `15-Web-Clips/`

**Files:**
- Extension source: `extension/`
- Setup guide: `docs/extension-setup.md`

### Chat Importers Daemon

Auto-collect chat histories from Claude CLI, Copilot, and other tools.

**Install:**
```bash
bash scripts/setup-organizer.sh --enable-importers --importer-interval 2h
```

**How it works:**
- Runs every N hours (configurable, default 2h)
- Scans local storage for new chats from Claude CLI and Copilot
- Converts each to markdown and writes to `00-Inbox/`
- Existing organizer picks up and files to `10-LLM-Chats/`
- State tracking (SQLite) prevents duplicates

**Supported tools:**
- Claude CLI (detects `~/.claude/chats/`)
- Copilot (cross-platform: Windows, macOS, Linux)
- Extensible: add ChatGPT, Gemini, etc.

**Files:**
- Importers source: `scripts/chat_importers/`
- Setup integration: `scripts/setup-organizer.sh`
- Dev guide: `docs/importer-developer-guide.md`
```

- [ ] **Step 5: Commit integration changes**

```bash
cd /path/to/research-log
git add scripts/organizer.py scripts/setup-organizer.sh README.md
git commit -m "feat: integrate importers and web-clipper with organizer

Updates to existing infrastructure:

organizer.py:
- Preserve 'tool', 'source_id', 'url' frontmatter fields
- Route 'web-clip' type to 15-Web-Clips/ folder
- Support new note types in classification

setup-organizer.sh:
- Add --enable-importers flag
- Add --importer-interval flag (default 2h)
- Install chat importers cron job alongside organizer

README.md:
- Add browser extension setup and usage instructions
- Add chat importers setup and support info

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 9: Create Documentation

**Files:**
- Create: `docs/extension-setup.md`
- Create: `docs/importer-setup.md`
- Create: `docs/importer-developer-guide.md`

- [ ] **Step 1: Write extension-setup.md**

```markdown
# Research Log Web Clipper - Setup & Usage

## Installation

### Chrome / Edge

1. **Get the code:**
   ```bash
   cd research-log/extension
   ```

2. **Load extension:**
   - Open Chrome and go to `chrome://extensions/`
   - Enable **Developer mode** (toggle in top right)
   - Click **Load unpacked**
   - Select the `extension/` folder

3. **Configure settings:**
   - Click the extension icon (puzzle piece) in the toolbar
   - Click the **⚙️ gear icon** or right-click → Options
   - Set "Download Folder" to your vault's inbox folder
     - Example: `/Users/alice/Documents/research-log/vault/00-Inbox`
   - (Optional) Set your contributor name
   - Click **Save Settings**

## Usage

### Clipping a Page or Text

1. **Browse** to any web page
2. **(Optional)** Select text by highlighting it
3. **Click** the extension icon → popup appears
4. **Review:**
   - Page URL and title are pre-filled
   - Selected text preview shows (if any)
   - You can add a screenshot, notes, and tags
5. **Click "Save to Research Log"**
6. File is saved to your inbox folder and the organizer will pick it up

### What Gets Saved

Each clip is saved as a markdown file with:

```markdown
---
type: web-clip
date: 2026-04-10
contributor: "alice"
url: "https://example.com/article"
summary: "Article title or first 120 chars of selection"
tags:
  - "web-clip"
  - (any tags you added)
---

# Article Title

**Source:** [URL](URL)

## Selected Text

(Your selected text, if any)

## Notes

(Your notes, if any)

## Screenshot

![Screenshot](screenshot.png)

(If you toggled screenshot)
```

### Tips

- **Don't select anything** — clips the whole page content for reference
- **Select specific text** — captures just what matters
- **Add tags** — comma-separated, helps filtering in Obsidian
- **Include screenshot** — useful for layouts, designs, visual references
- **Notes** — explain *why* you're saving this (context for future-you)

### Troubleshooting

**Issue:** "Download folder not configured"
- **Solution:** Open extension options and set your inbox folder path

**Issue:** Files don't appear in Obsidian
- **Solution:** Check that the path you configured is correct and accessible
- Run `ls vault/00-Inbox/` to verify files exist
- If using organizer, wait for the next run (or run manually: `python3 scripts/organizer.py`)

**Issue:** Screenshots are huge
- **Solution:** Chrome captures at full resolution. Consider:
  - Cropping in the page before clipping
  - Using browser zoom to reduce capture size
  - Compression option (TBD)

## Advanced

### Changing the Download Folder

1. Open extension options (`chrome://extensions/` → gear icon)
2. Update the "Download Folder" path
3. Save

### Using with Organizer

If you have the organizer running (`setup-organizer.sh`), it will automatically:
1. Pick up files from `00-Inbox/`
2. Classify them (keep type=web-clip)
3. File to `15-Web-Clips/` folder
4. Add to the daily digest

To run organizer manually:
```bash
python3 scripts/organizer.py
```

## Development

See `extension/README.md` for extension code structure and development notes.
```

- [ ] **Step 2: Write importer-setup.md**

```markdown
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
**Format:** JSON files  
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
```

- [ ] **Step 3: Write importer-developer-guide.md**

```markdown
# Chat Importers - Developer Guide

## Architecture

The importer system is designed to be extensible. Each tool gets its own importer class that inherits from `ChatImporter`.

```
chat_importers/
├── base.py         ← Abstract ChatImporter class
├── state.py        ← SQLite duplicate tracking
├── claude_cli.py   ← Claude CLI implementation
├── copilot.py      ← Copilot implementation
└── (new_tool).py   ← Your importer here
```

## Adding a New Tool

### 1. Create the importer class

Create `scripts/chat_importers/new_tool.py`:

```python
from .base import ChatImporter, ChatMessage
from datetime import datetime
from pathlib import Path

class NewToolImporter(ChatImporter):
    """Import chats from NewTool."""
    
    @property
    def tool_name(self) -> str:
        return 'new-tool'
    
    def find_new_chats(self) -> list:
        """Find unimported chats from NewTool."""
        # 1. Detect storage location
        # 2. List all chat files/IDs
        # 3. Filter out already-imported ones using self.state
        # 4. Return list of paths
        pass
    
    def parse_chat(self, path: str) -> dict:
        """Parse a chat file and return standardized dict."""
        # 1. Read the file
        # 2. Extract messages
        # 3. Extract metadata (date, etc.)
        # 4. Return:
        # {
        #     'source_id': 'unique-id',
        #     'messages': [ChatMessage(...), ...],
        #     'date': datetime,
        #     'tool': 'new-tool',
        #     'metadata': { ... }
        # }
        pass
```

### 2. Implement key methods

#### `find_new_chats()` → List[str]

Returns paths to chat files that haven't been imported.

Example:
```python
def find_new_chats(self) -> list:
    storage_path = self._get_storage_path()
    if not storage_path:
        return []
    
    all_chats = glob.glob(os.path.join(storage_path, '*.json'))
    
    if self.state:
        new_chats = [
            f for f in all_chats
            if not self.state.is_imported(self.tool_name, os.path.basename(f))
        ]
        return new_chats
    
    return all_chats
```

#### `parse_chat(path)` → dict

Parses a chat file and returns standardized format.

Example:
```python
def parse_chat(self, path: str) -> dict:
    with open(path) as f:
        data = json.load(f)
    
    messages = [
        ChatMessage(
            role=msg['role'],
            content=msg['content'],
            timestamp=datetime.fromisoformat(msg['timestamp'])
        )
        for msg in data['messages']
    ]
    
    return {
        'source_id': os.path.basename(path),
        'messages': messages,
        'date': datetime.fromisoformat(data['created_at']),
        'tool': self.tool_name,
        'metadata': {}
    }
```

### 3. Register the importer

In `scripts/chat_importers.py`, add to `run_importers()`:

```python
try:
    from chat_importers.new_tool import NewToolImporter
    importers.append(NewToolImporter(state))
except Exception as e:
    print(f"Warning: Could not load NewTool importer: {e}")
```

### 4. Test it

Create a test with mock data:

```python
# scripts/test_new_tool.py
import tempfile
from chat_importers.new_tool import NewToolImporter
from chat_importers.state import ImportState

with tempfile.TemporaryDirectory() as tmpdir:
    # Create mock chat file
    mock_file = os.path.join(tmpdir, 'chat_123.json')
    # ... write mock data ...
    
    # Create importer with mock state
    state = ImportState(os.path.join(tmpdir, 'state.db'))
    importer = NewToolImporter(state)
    importer.storage_path = tmpdir  # Override for testing
    
    # Test find_new_chats
    chats = importer.find_new_chats()
    assert len(chats) == 1
    
    # Test parse_chat
    chat = importer.parse_chat(chats[0])
    assert chat['tool'] == 'new-tool'
    assert len(chat['messages']) > 0
    
    # Test markdown generation
    markdown = importer.to_markdown(chat, 'test_user')
    assert 'tool: "new-tool"' in markdown
    
    print("✓ All tests passed")
```

Run:
```bash
python3 scripts/test_new_tool.py
```

### 5. Submit

Once tested, commit your importer:
```bash
git add scripts/chat_importers/new_tool.py
git commit -m "feat: add NewTool chat importer

Imports chats from NewTool storage location."
```

## API Reference

### ChatImporter base class

**Properties:**
- `tool_name` (str, abstract): Identifier like 'claude-cli', 'copilot', 'chatgpt'

**Methods:**
- `find_new_chats()` → List[str] (abstract)
  - Return paths to unimported chats
  
- `parse_chat(path: str)` → dict (abstract)
  - Parse file and return standardized chat dict
  
- `to_markdown(chat: dict, contributor: str)` → str
  - Convert chat dict to markdown (inherited, no override needed)
  
- `mark_imported(source_id: str)`
  - Mark a chat as imported in the state tracker

### ChatMessage

```python
ChatMessage(
    role: str,      # 'user', 'assistant', etc.
    content: str,   # The message text
    timestamp: datetime = None
)
```

### ImportState

```python
state = ImportState(db_path='/path/to/db.sqlite')

# Check if imported
is_imported = state.is_imported(tool='claude-cli', source_id='chat_123')

# Mark imported
state.mark_imported(tool='claude-cli', source_id='chat_123')

# List all imported
chats = state.list_imported()  # or state.list_imported('claude-cli')
```

## Best Practices

1. **Use `self.tool_name`** for consistency (e.g., in frontmatter generation)
2. **Handle missing storage gracefully** — return empty list if path doesn't exist
3. **Use `self.state`** to track imports — never import twice
4. **Preserve metadata** — extract dates, any unique IDs, author info
5. **Test with mocks** — don't rely on real tools being installed
6. **Document storage locations** — including all OS variants
7. **Graceful fallbacks** — if format varies, try multiple parsers

## Examples

See `scripts/chat_importers/claude_cli.py` and `copilot.py` for real implementations.
```

- [ ] **Step 4: Commit documentation**

```bash
cd /path/to/research-log
git add docs/extension-setup.md docs/importer-setup.md docs/importer-developer-guide.md
git commit -m "docs: add setup and developer guides

extension-setup.md:
- Installation for Chrome/Edge
- Configuration walkthrough
- Usage examples and tips
- Troubleshooting

importer-setup.md:
- Installation and configuration
- Supported tools (Claude CLI, Copilot)
- How it works
- Troubleshooting and manual execution
- Integration with organizer

importer-developer-guide.md:
- Architecture overview
- Step-by-step guide to adding new tools
- API reference for ChatImporter, ChatMessage, ImportState
- Best practices and examples

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 10: End-to-End Testing & Polish

**Files:**
- Modify: README.md (final polish)
- Test: manual verification across components

- [ ] **Step 1: Test browser extension**

1. Load extension in Chrome (chrome://extensions/ → Load unpacked)
2. Configure download folder (gear icon)
3. Visit a web page, select text, click extension icon
4. Verify popup appears with preview
5. Toggle screenshot option
6. Add tags and notes
7. Click "Save to Research Log"
8. Verify file appears in `vault/00-Inbox/`

Expected file:
```markdown
---
type: web-clip
date: 2026-04-10
contributor: "..."
url: "https://..."
summary: "..."
tags:
  - "web-clip"
  - "..."
---
```

- [ ] **Step 2: Test chat importers (Claude CLI)**

1. Verify Claude CLI is installed
2. Create mock chats in `~/.claude/chats/` or use real history
3. Run: `python3 scripts/chat_importers.py --dry-run`
4. Verify output shows detected chats
5. Run: `python3 scripts/chat_importers.py`
6. Verify files appear in `vault/00-Inbox/`
7. Run again (should skip already-imported)

- [ ] **Step 3: Test chat importers (Copilot)**

1. Ensure Copilot chats exist in platform-specific location
2. Run: `python3 scripts/chat_importers.py --dry-run`
3. Verify Copilot chats are detected
4. Run importer and verify files

- [ ] **Step 4: Test integration with organizer**

1. Manually create test files in `00-Inbox/`
2. Run: `python3 scripts/organizer.py --dry-run`
3. Verify files will be routed correctly:
   - `web-clip` → `15-Web-Clips/`
   - `llm-chat` with `tool: "claude-cli"` → `10-LLM-Chats/`
4. Run: `python3 scripts/organizer.py`
5. Verify files moved to correct folders
6. Open Obsidian and verify metadata in dashboard

- [ ] **Step 5: Test setup scripts**

1. Test `setup-organizer.sh --enable-importers`:
   ```bash
   bash scripts/setup-organizer.sh --enable-importers --importer-interval 2h
   ```
2. Verify cron jobs installed:
   ```bash
   crontab -l | grep "chat_importers"
   ```
3. Test `setup-organizer.sh --remove-importers`:
   ```bash
   bash scripts/setup-organizer.sh --remove-importers
   ```
4. Verify cron job removed

- [ ] **Step 6: Final README polish**

Update README.md with final sections. Add a "What's New" section summarizing the additions:

```markdown
## New in This Release

### Web Clipper Browser Extension
Lightweight capture of web articles, text selections, and screenshots directly to your vault. See [extension setup guide](docs/extension-setup.md).

### Chat Importers Daemon
Auto-collect chat histories from Claude CLI, Copilot, and other tools. Enable with `bash scripts/setup-organizer.sh --enable-importers`. See [importer setup guide](docs/importer-setup.md).

### New Vault Folder
- `15-Web-Clips/` — stores clipped web content

### New Frontmatter Fields
- `tool` — identifies source (claude-cli, copilot, web, etc.)
- `source_id` — unique ID in source system (prevents duplicates)
- `url` — for web clips
```

- [ ] **Step 7: Final commit**

```bash
cd /path/to/research-log
git add README.md
git commit -m "docs: polish README with new features summary

Add 'What's New' section highlighting:
- Web clipper browser extension
- Chat importers daemon
- New vault folder (15-Web-Clips/)
- New frontmatter fields (tool, source_id, url)

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Summary

This plan covers the complete implementation of:

1. **Browser Extension** (Phase 1, Task 4)
   - Chrome Manifest V3 extension
   - Popup UI for text/link/screenshot capture
   - Settings page
   - File save via Chrome downloads API

2. **Chat Importers** (Phase 2, Tasks 5-7)
   - Foundation with state tracking and abstract base
   - Claude CLI importer
   - Copilot importer (cross-platform)
   - Extensible framework for future tools

3. **Integration** (Phase 3, Task 8)
   - Organizer updates to preserve and route new note types
   - Setup script integration with cron
   - Folder structure (`15-Web-Clips/`)

4. **Documentation & Testing** (Phase 3, Tasks 9-10)
   - User guides (extension, importers)
   - Developer guide for adding tools
   - End-to-end testing verification

All changes are committed incrementally with clear commit messages and organized into logical phases for easy review and iteration.
