# Obsidian Zettelkasten Auto-Capture

Passive knowledge capture system that automatically logs Claude web chats, Claude Code sessions, git commits, and research into an Obsidian vault — no manual filing.

## How it works

```
Claude web chat  ──(browser ext)──┐
Claude Code session ──(Stop hook)──┤──► 00-Inbox/ ──(watcher)──► tagged & filed
Git commit ──(post-commit hook)────┘                              + one question asked
Manual drop (papers, research)────────► 00-Inbox/
```

The inbox watcher classifies each note via Gemini AI (or keyword fallback), injects YAML frontmatter, moves it to the right folder, and pops a desktop dialog with one optional question.

---

## Prerequisites

- Python 3.8+
- An Obsidian vault
- `notify-send` + `zenity` (Linux) — usually pre-installed
- A Gemini API key (optional — keyword fallback works without one)
- Claude Code CLI (for the session hook)

---

## Installation

### 1 — Clone and set your vault path

```bash
git clone https://github.com/vihaan-that/obsidian-zettelkasten-autocapture.git
cd obsidian-zettelkasten-autocapture
```

Open **every file below** and replace the hardcoded vault path:

```
/home/vihaan/Documents/Work
```

with your actual vault path (e.g. `/home/yourname/Notes/MyVault`). Files to update:

| File | Lines to change |
|------|----------------|
| `scripts/inbox_watcher.py` | `VAULT_PATH = Path("...")` near the top |
| `scripts/start_watcher.sh` | `VAULT_PATH=...` near the top |
| `scripts/stop_watcher.sh` | `VAULT_PATH=...` near the top |
| `scripts/git-post-commit-hook.sh` | `VAULT_PATH=...` near the top |
| `hooks/obsidian_logger.sh` | `VAULT_PATH=...` near the top |

### 2 — Create the vault folder structure

Run this once (replace the path):

```bash
VAULT="/your/vault/path"
mkdir -p "$VAULT/00-Inbox" "$VAULT/10-LLM-Chats" "$VAULT/20-Code-Sessions" \
         "$VAULT/30-Research" "$VAULT/40-Experiments" "$VAULT/60-Permanent" \
         "$VAULT/_Templates" "$VAULT/_Scripts" "$VAULT/_Dashboard"
```

### 3 — Copy scripts into your vault

```bash
VAULT="/your/vault/path"
cp scripts/inbox_watcher.py       "$VAULT/_Scripts/"
cp scripts/start_watcher.sh       "$VAULT/_Scripts/"
cp scripts/stop_watcher.sh        "$VAULT/_Scripts/"
cp scripts/git-post-commit-hook.sh "$VAULT/_Scripts/"
cp dashboard/Home.md              "$VAULT/_Dashboard/"
cp dashboard/SETUP.md             "$VAULT/_Dashboard/"
chmod +x "$VAULT/_Scripts/"*.sh "$VAULT/_Scripts/"*.py
```

### 4 — Install the Claude Code Stop hook

> This file **cannot be auto-downloaded** by Obsidian — it must be placed manually in `~/.claude/hooks/`.

```bash
mkdir -p ~/.claude/hooks
cp hooks/obsidian_logger.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/obsidian_logger.sh
```

Then register it in `~/.claude/settings.json`. If the file doesn't exist yet, create it:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/hooks/obsidian_logger.sh"
          }
        ]
      }
    ]
  }
}
```

If `~/.claude/settings.json` already exists, merge only the `hooks` block in — don't overwrite other keys. With `jq`:

```bash
jq '. * {"hooks":{"Stop":[{"hooks":[{"type":"command","command":"bash ~/.claude/hooks/obsidian_logger.sh"}]}]}}' \
  ~/.claude/settings.json > /tmp/s.json && mv /tmp/s.json ~/.claude/settings.json
```

### 5 — Install the git post-commit hook (per repo)

> This file must be copied into each repo you want to track. It **cannot be a symlink** — git only runs plain files in `.git/hooks/`.

```bash
cp scripts/git-post-commit-hook.sh /path/to/your/repo/.git/hooks/post-commit
chmod +x /path/to/your/repo/.git/hooks/post-commit
```

Repeat for every repo you want logged.

### 6 — Start the watcher

```bash
export GEMINI_API_KEY="your-key-here"   # skip to use keyword classification
bash /your/vault/path/_Scripts/start_watcher.sh
```

To run on every login, add both lines to `~/.bashrc`.

To stop:

```bash
bash /your/vault/path/_Scripts/stop_watcher.sh
```

### 7 — Browser extension (Claude web chats)

1. Open the Chrome Web Store, search **"Claude to Obsidian & Markdown Export"**
2. Install and open its settings
3. Set the download folder to `your-vault-path/00-Inbox/`
4. Enable bulk export

### 8 — Obsidian plugins

Install via **Settings → Community Plugins → Browse**:

| Plugin | Required? |
|--------|-----------|
| **Dataview** | Required — powers `_Dashboard/Home.md` |
| **Obsidian Git** | Optional — vault backup |

Then open `_Dashboard/Home.md` in Obsidian.

---

## Folder structure

```
00-Inbox/          ← everything lands here first
10-LLM-Chats/      ← Claude web chats
20-Code-Sessions/  ← Claude Code sessions + git commits
30-Research/       ← papers, articles, exports
40-Experiments/    ← hypotheses and test logs
60-Permanent/      ← evergreen / general notes
_Dashboard/        ← Home.md (open this in Obsidian)
_Scripts/          ← watcher, hooks, logs
_Templates/        ← note templates
```

---

## Capture sources

| Source | Mechanism | Destination |
|--------|-----------|-------------|
| Claude web chats | Browser extension | `00-Inbox` → `10-LLM-Chats` |
| Claude Code sessions | `~/.claude/hooks/obsidian_logger.sh` | `00-Inbox` → `20-Code-Sessions` |
| Git commits | Per-repo `post-commit` hook | `00-Inbox` → `20-Code-Sessions` |
| Research / PDFs | Manual drop into `00-Inbox/` | `00-Inbox` → `30-Research` |

---

## Notes

- The watcher uses `gemini-2.0-flash` for classification. The code contains a `# TODO: swap to Anthropic API when ready` comment marking the API call block.
- All paths are hardcoded at setup time — if you move your vault, update the `VAULT_PATH` variable in each script.
- The watcher logs to `_Scripts/watcher.log`. Check there first if something isn't filing correctly.
