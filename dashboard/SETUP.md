---
tags: [setup, dashboard]
---

# Zettelkasten Setup Guide

## 1 — Browser Extension (Claude Web Chats)

1. Open the Chrome Web Store and search for **"Claude to Obsidian & Markdown Export"**
2. Install the extension
3. Open its settings and set the **download folder** to:
   ```
   /home/vihaan/Documents/Work/00-Inbox/
   ```
4. Enable **bulk export** in the extension options
5. After any Claude web chat, click the extension icon → Export → the file lands in `00-Inbox/` and the watcher files it automatically

> **Note:** Chrome extensions download to `~/Downloads` by default. You may need to either (a) configure the vault inbox as your default download folder, or (b) symlink: `ln -s /home/vihaan/Documents/Work/00-Inbox ~/Downloads/obsidian-inbox` and point the extension there.

---

## 2 — Obsidian Plugins Required

Install these from **Settings → Community Plugins → Browse**:

| Plugin | Purpose | Required? |
|--------|---------|-----------|
| **Dataview** | Powers the Home dashboard queries | Required |
| **Obsidian Git** | Auto-backup vault to a git repo | Optional |

Enable each after installing.

---

## 3 — Start the Inbox Watcher

Run once after login (add to `~/.bashrc` or your desktop autostart for persistence):

```bash
# First time — export your Gemini key so the watcher can AI-classify notes:
export GEMINI_API_KEY="your-key-here"

# Start:
bash /home/vihaan/Documents/Work/_Scripts/start_watcher.sh

# Stop:
bash /home/vihaan/Documents/Work/_Scripts/stop_watcher.sh
```

To auto-start on login, add to `~/.bashrc`:
```bash
export GEMINI_API_KEY="your-key-here"
bash /home/vihaan/Documents/Work/_Scripts/start_watcher.sh
```

Logs are written to `_Scripts/watcher.log`.

---

## 4 — Add the Git Post-Commit Hook to a Repo

Copy the template hook into any git repo you want to track:

```bash
cp /home/vihaan/Documents/Work/_Scripts/git-post-commit-hook.sh \
   /path/to/your/repo/.git/hooks/post-commit

chmod +x /path/to/your/repo/.git/hooks/post-commit
```

Every commit in that repo will drop a note into `00-Inbox/` automatically.

---

## 5 — What Gets Captured Automatically

| Source | How | Lands in |
|--------|-----|----------|
| Claude web chats | Browser extension export | `00-Inbox` → `10-LLM-Chats` |
| Claude Code sessions | `Stop` hook in `~/.claude/settings.json` | `00-Inbox` → `20-Code-Sessions` |
| Git commits | Per-repo `post-commit` hook | `00-Inbox` → `20-Code-Sessions` |
| Deep research / PDFs | Drop file manually into `00-Inbox/` | `00-Inbox` → `30-Research` |

The inbox watcher handles all routing — you never manually move or tag anything.

---

## 6 — Folder Map

```
00-Inbox/          ← everything lands here first
10-LLM-Chats/      ← Claude web chats
20-Code-Sessions/  ← Claude Code sessions + git commits
30-Research/       ← papers, articles, research exports
40-Experiments/    ← hypotheses and test logs
60-Permanent/      ← evergreen / general notes
_Dashboard/        ← Home.md (open this in Obsidian)
_Scripts/          ← watcher, hooks, logs
_Templates/        ← note templates (add your own)
```
