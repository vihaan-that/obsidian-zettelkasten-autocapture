---
tags: [setup, dashboard]
---

# Setup Guide

## 1 — Daily logging (no setup needed)

```bash
cd research-log
bash scripts/log.sh
```

The script prompts for your name (remembers it), entry type, and walks you through each section.

## 2 — Obsidian vault

1. Open Obsidian
2. "Open folder as vault" > select the `vault/` directory
3. Install **Dataview** plugin: Settings > Community Plugins > Browse > Dataview
4. Open `_Dashboard/Home.md` — your team dashboard

Optional: install **Obsidian Git** for auto-backup.

## 3 — Inbox watcher (optional auto-filing)

```bash
# Keyword classification (no API key needed)
bash scripts/start_watcher.sh

# With AI classification
export GEMINI_API_KEY="your-key"
bash scripts/start_watcher.sh

# Stop
bash scripts/stop_watcher.sh
```

Add to `~/.bashrc` for auto-start on login.

Logs: `vault/_Scripts/watcher.log`

## 4 — Claude Code session hook (optional)

```bash
mkdir -p ~/.claude/hooks
cp hooks/obsidian_logger.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/obsidian_logger.sh
```

Add to `~/.claude/settings.json`:
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

## 5 — Git post-commit hook (per repo, optional)

```bash
cp scripts/git-post-commit-hook.sh /path/to/repo/.git/hooks/post-commit
chmod +x /path/to/repo/.git/hooks/post-commit
```

Every commit logs a note with repo, branch, files changed, and commit message.

## 6 — Browser extension (Claude web chats, optional)

1. Chrome Web Store > **"Claude to Obsidian & Markdown Export"**
2. Set download folder to `vault/00-Inbox/`
3. Enable bulk export

## Folder map

```
vault/
├── 00-Inbox/          ← staging area
├── 10-LLM-Chats/      ← Claude web chats
├── 20-Code-Sessions/  ← code sessions + git commits
├── 30-Research/       ← papers, articles
├── 40-Experiments/    ← hypotheses and test logs
├── 50-Daily-Logs/     ← structured daily entries
├── 55-Journals/       ← freestyle journals
├── 60-Permanent/      ← general notes
├── _Dashboard/        ← this file + Home.md
├── _Scripts/          ← watcher logs
└── _Templates/        ← note templates
```

## Capture sources

| Source | Mechanism | Destination |
|--------|-----------|-------------|
| Daily log (interactive) | `scripts/log.sh` | `00-Inbox` > `50-Daily-Logs` |
| Journal (interactive) | `scripts/log.sh --type journal` | `00-Inbox` > `55-Journals` |
| Experiment (interactive) | `scripts/log.sh --type experiment` | `00-Inbox` > `40-Experiments` |
| Claude Code sessions | Stop hook | `00-Inbox` > `20-Code-Sessions` |
| Git commits | post-commit hook | `00-Inbox` > `20-Code-Sessions` |
| Claude web chats | Browser extension | `00-Inbox` > `10-LLM-Chats` |
| Research / PDFs | Manual drop into `00-Inbox/` | `00-Inbox` > `30-Research` |
