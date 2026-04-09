# Research Log

A team daily research logging system built on Obsidian. Collects structured daily logs, freestyle journals, experiments, code sessions, and research notes into a shared vault — one centralized knowledge base for humans today, LLM agents tomorrow.

![System Architecture](docs/architecture.png)

---

## Table of Contents

- [Quick Start](#quick-start)
- [How It Works](#how-it-works)
- [Data Flow](#data-flow)
- [Process Flow — log.sh](#process-flow--logsh)
- [Watcher Pipeline](#watcher-pipeline)
- [Usage Guide](#usage-guide)
  - [Daily Logging (log.sh)](#daily-logging-logsh)
  - [Auto-Capture Watcher](#auto-capture-watcher)
  - [Scheduled Reminders](#scheduled-reminders)
  - [Claude Code Hook](#claude-code-session-hook)
  - [Git Commit Hook](#git-commit-hook)
  - [Browser Extension](#browser-extension-claude-web-chats)
- [Vault Structure](#vault-structure)
- [Frontmatter Schema](#frontmatter-schema)
- [Obsidian Setup](#obsidian-setup)
- [Environment Variables](#environment-variables)
- [LLM Consumption](#for-llm-consumption)
- [Project Layout](#project-layout)

---

## Quick Start

```bash
# Clone
git clone https://github.com/vihaan-that/obsidian-zettelkasten-autocapture.git research-log
cd research-log

# Log your first entry — the script walks you through it
bash scripts/log.sh
```

That's it. No dependencies, no config, no API keys. Just run the script.

---

## How It Works

There are five capture sources, one staging area, one processing daemon, and seven destination folders. Everything is markdown with YAML frontmatter, stored in a flat folder layout that's trivially queryable.

```
Team member runs log.sh  ──────────┐
Claude Code session ──(Stop hook)──┤
Git commit ──(post-commit hook)────┤──► 00-Inbox/ ──(watcher)──► classified & filed
Browser export ────────────────────┤                              + one question asked
Manual drop (papers, research)─────┘
```

- **Humans write entries** via `log.sh` (interactive CLI with prompts) or drop files manually
- **Hooks capture automatically** from Claude Code sessions and git commits
- **The inbox watcher** classifies each note (AI or keyword fallback), injects YAML frontmatter, moves it to the right folder, and pops a desktop notification with one targeted question
- **Cron/launchd** sends a daily reminder to log

---

## Data Flow

How entries move from creation through classification to their final vault location.

![Data Flow Diagram](docs/data-flow.png)

### Flow walkthrough

1. **Capture** — An entry is created by one of five sources: the interactive CLI (`log.sh`), a Claude Code session hook, a git post-commit hook, a browser extension export, or a manual file drop
2. **Staging** — The `.md` file lands in `vault/00-Inbox/`, the universal staging area
3. **Detection** — The `inbox_watcher.py` daemon (watchdog-based) detects the new file via filesystem events
4. **Classification** — The watcher classifies the note:
   - **With API key**: Sends the first 3000 characters to Gemini 2.0 Flash, which returns `{ type, summary, tags, contributor }`
   - **Without API key**: Falls back to keyword matching (checks for patterns like "hypothesis", "daily log", "git commit", etc.)
5. **Frontmatter injection** — YAML frontmatter is injected or updated with `type`, `date`, `contributor`, `summary`, and `tags`
6. **Filing** — The note is moved from `00-Inbox/` to its destination folder (e.g., `50-Daily-Logs/`, `55-Journals/`, `40-Experiments/`)
7. **Notification** — A desktop notification appears with one context question (e.g., "Anything you'd add in hindsight?"). The user's response is appended as a `## Reflection` section

---

## Process Flow — log.sh

The interactive CLI that walks team members through a daily entry.

![Process Flow](docs/process-flow.png)

### Step by step

1. **Run** `bash scripts/log.sh` (or with flags: `--name`, `--type`, `--editor`)
2. **Name prompt** — asks your name (cached in `.contributor` so you only type it once)
3. **Type selection** — pick from three entry types:
   - **daily-log** (structured): prompted through Work Done, Pivots, Decisions, Tangents, Blockers, Status
   - **journal** (freestyle): write freely with creative prompts if stuck
   - **experiment**: prompted through Hypothesis, Setup, Observations, Result, Next Steps
4. **`--editor` mode** — if the flag is set, opens the template in `$EDITOR` instead of inline prompts
5. **Tags** — comma-separated, optional (defaults to the entry type)
6. **Build** — assembles the markdown file with YAML frontmatter + section content
7. **Write** — saves to `vault/00-Inbox/<type>-<date>-<name>.md`
8. **Watcher** — if running, picks it up and files it automatically

---

## Watcher Pipeline

The `inbox_watcher.py` daemon — how notes are automatically processed after they land in the inbox.

![Watcher Pipeline](docs/watcher-pipeline.png)

### Pipeline stages

| Stage | What happens |
|-------|-------------|
| **File Detected** | `watchdog` fires `on_created` or `on_moved` for any new `.md` file in `00-Inbox/` |
| **Read Content** | File content is read as UTF-8 |
| **Classify** | AI classification via Gemini 2.0 Flash (or keyword fallback if no API key) extracts type, summary, tags, and contributor |
| **Inject Frontmatter** | YAML frontmatter is injected or updated. Existing frontmatter from `log.sh` is respected — only summary is updated |
| **Move to Destination** | File is moved to the appropriate folder. Filename collisions are handled with a timestamp suffix |
| **Ask User Question** | Desktop notification + dialog box with one targeted question. Response appended as `## Reflection` |

### Classification keywords (fallback mode)

| Type | Triggers on |
|------|------------|
| `daily-log` | "what i worked on", "pivots", "course correction", "daily log" |
| `journal` | "stream of consciousness", "journal" |
| `experiment` | "hypothesis", "observations", "result:" |
| `code-session` | "claude code", "git commit", "branch:" |
| `research` | "abstract", "paper", "doi:", "arxiv" |
| `llm-chat` | "chat", "prompt", "llm", "claude", "gemini" |
| `general` | anything else |

---

## Usage Guide

### Daily Logging (log.sh)

The primary way team members log their work.

```bash
# Fully interactive — prompts for everything
bash scripts/log.sh

# Pre-fill your name (remembered after first use)
bash scripts/log.sh --name alice

# Jump straight to a freestyle journal
bash scripts/log.sh --type journal

# Structured daily log opened in your editor
bash scripts/log.sh --type daily-log --editor

# Experiment log
bash scripts/log.sh --type experiment

# Combine flags
bash scripts/log.sh --name bob --type journal --editor
```

#### Entry types

**Structured daily log** (`--type daily-log`):
```
What did you work on today?
Any pivots or course corrections?
Key decisions & reasoning
Tangents explored
Blockers & open questions
Status & next steps
Links & references
```

**Freestyle journal** (`--type journal`):
```
Write freely. Prompts if stuck:
  - What surprised you today?
  - What's the thing you'll forget by next week?
  - What would you tell a teammate picking this up cold?
  - What's the dumbest thing you tried that almost worked?
```

**Experiment** (`--type experiment`):
```
Hypothesis
Setup
Observations
Result
Next steps
Status
```

---

### Auto-Capture Watcher

The background daemon that classifies and files notes automatically.

```bash
# Start (keyword classification — no API key needed)
bash scripts/start_watcher.sh

# Start with AI classification
export GEMINI_API_KEY="your-key"
bash scripts/start_watcher.sh

# Stop
bash scripts/stop_watcher.sh
```

The watcher is optional. Without it, entries still land in `vault/00-Inbox/` and you can file them manually or browse them directly in Obsidian.

Logs: `vault/_Scripts/watcher.log`

#### Auto-start on login

Add to `~/.bashrc` or `~/.zshrc`:

```bash
export GEMINI_API_KEY="your-key"  # optional
bash /path/to/research-log/scripts/start_watcher.sh
```

---

### Scheduled Reminders

Daily cron job (Linux) or launchd agent (macOS) that reminds you to log.

```bash
# Default: daily notification at 5:00 PM
bash scripts/setup-cron.sh

# Custom time (24h format)
bash scripts/setup-cron.sh --hour 18 --minute 30

# Also open a terminal with log.sh (not just a notification)
bash scripts/setup-cron.sh --open

# Remove the reminder
bash scripts/setup-cron.sh --remove
```

| Platform | Mechanism | Notification | Terminal |
|----------|-----------|-------------|----------|
| **Ubuntu/Linux** | crontab + `notify-send` | `notify-send` (handles DISPLAY/DBUS from cron) | gnome-terminal, xfce4-terminal, konsole, or x-terminal-emulator |
| **macOS** | launchd plist | `osascript` notification with sound | Terminal.app via AppleScript |

---

### Claude Code Session Hook

Automatically logs every Claude Code session when it ends.

**Install:**

```bash
mkdir -p ~/.claude/hooks
cp hooks/obsidian_logger.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/obsidian_logger.sh
```

**Register in `~/.claude/settings.json`:**

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

If `~/.claude/settings.json` already exists, merge only the hooks block:

```bash
jq '. * {"hooks":{"Stop":[{"hooks":[{"type":"command","command":"bash ~/.claude/hooks/obsidian_logger.sh"}]}]}}' \
  ~/.claude/settings.json > /tmp/s.json && mv /tmp/s.json ~/.claude/settings.json
```

**What gets captured:**
- Session ID
- Repository name and branch
- First 5 user prompts from the transcript
- Files changed in the last commit
- Contributor name (from `git config user.name` or `$LOG_CONTRIBUTOR`)

---

### Git Commit Hook

Logs every git commit from repos you instrument.

**Install per repo:**

```bash
cp scripts/git-post-commit-hook.sh /path/to/repo/.git/hooks/post-commit
chmod +x /path/to/repo/.git/hooks/post-commit
```

**What gets captured:**
- Repo name, branch, commit hash, commit message
- Files changed
- Contributor (git author name)

---

### Browser Extension (Claude Web Chats)

1. Chrome Web Store > search **"Claude to Obsidian & Markdown Export"**
2. Install and open its settings
3. Set the download folder to `vault/00-Inbox/`
4. Enable bulk export

Exported chats land in `00-Inbox/` and the watcher files them to `10-LLM-Chats/`.

---

## Vault Structure

```
vault/
├── 00-Inbox/           ← staging area — everything lands here first
├── 10-LLM-Chats/       ← Claude web chats (via browser extension)
├── 20-Code-Sessions/   ← Claude Code sessions + git commits
├── 30-Research/        ← papers, articles, PDF exports
├── 40-Experiments/     ← hypotheses, test logs, results
├── 50-Daily-Logs/      ← structured daily entries
├── 55-Journals/        ← freestyle journals
├── 60-Permanent/       ← evergreen / general notes
├── _Dashboard/         ← Home.md (Dataview queries)
├── _Scripts/           ← watcher PID, logs
└── _Templates/         ← daily-log.md, journal.md, experiment.md
```

### Folder routing

| Note type | Destination | Created by |
|-----------|-------------|------------|
| `daily-log` | `50-Daily-Logs/` | `log.sh`, manual |
| `journal` | `55-Journals/` | `log.sh`, manual |
| `experiment` | `40-Experiments/` | `log.sh`, manual |
| `code-session` | `20-Code-Sessions/` | Claude Code hook, git hook |
| `research` | `30-Research/` | Manual drop |
| `llm-chat` | `10-LLM-Chats/` | Browser extension |
| `general` | `60-Permanent/` | Anything unclassified |

---

## Frontmatter Schema

Every note in the vault has YAML frontmatter that makes it queryable:

```yaml
---
type: daily-log                    # daily-log | journal | experiment | code-session | research | llm-chat | general
date: 2026-04-09                   # ISO date
contributor: "alice"               # who wrote this
summary: "Explored new approach"   # one-liner, max 120 chars
status: "in-progress"              # for daily-logs and experiments (optional)
tags:                              # for filtering and search
  - "daily-log"
  - "ml-pipeline"
  - "tokenizer"
---
```

### Code session frontmatter (additional fields)

```yaml
---
type: code-session
date: 2026-04-09
contributor: "alice"
repo: research-log
branch: main
session_id: a1b2c3d4
summary: ""
tags:
  - "code-session"
---
```

---

## Obsidian Setup

1. Open Obsidian
2. **Open folder as vault** > select the `vault/` directory
3. Install **Dataview** plugin: Settings > Community Plugins > Browse > search "Dataview" > Install > Enable
4. Open `_Dashboard/Home.md` — this is your team activity dashboard

Optional: install **Obsidian Git** for automatic vault backup to the repo.

### Dashboard queries

`Home.md` provides live Dataview tables:

| Section | What it shows |
|---------|--------------|
| Recent Daily Logs | Last 10 daily logs with contributor, summary, status |
| Recent Journals | Last 10 journals with contributor and tags |
| Open Experiments | Experiments not marked as done/completed |
| Team Activity (7 days) | All entries from the past week |
| By Contributor | Entry count and last active date per person |
| Recent Code Sessions | Last 8 sessions with repo and branch |
| Recent Research | Last 8 research notes |
| Recent LLM Chats | Last 8 chat exports |

---

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `VAULT_PATH` | Path to the vault directory | `./vault` (relative to project root) |
| `GEMINI_API_KEY` | AI classification in the watcher (optional) | Keyword fallback if unset |
| `LOG_CONTRIBUTOR` | Override contributor name in hooks | `git config user.name` or `whoami` |
| `EDITOR` | Editor for `--editor` mode in log.sh | `vim` |

---

## For LLM Consumption

The vault is designed to be machine-readable from day one:

- **Consistent YAML frontmatter** on every note — `type`, `date`, `contributor`, `summary`, `tags`
- **Typed entries** with predictable section headers (not free-form soup)
- **Contributor attribution** on everything — agent can filter by person
- **Tags** for semantic filtering without parsing body text
- **Flat folder structure** — no nested hierarchies to traverse, just 7 top-level folders
- **Markdown body** — trivially parseable, no binary formats

### Example agent queries

```
"Show me all decisions alice made last week"
→ Filter 50-Daily-Logs/ by contributor=alice, date >= 7 days ago, extract "## Key decisions & reasoning"

"What experiments are still running?"
→ Filter 40-Experiments/ by status != done, return hypothesis + result

"What research has been done on tokenizers?"
→ Full-text search across 30-Research/ for "tokenizer", return summaries

"Summarize team activity for the standup"
→ All notes from today across all folders, group by contributor, extract summaries
```

---

## Project Layout

```
research-log/
├── README.md                       ← this file
├── .gitignore
├── docs/
│   ├── architecture.png            ← system architecture diagram
│   ├── data-flow.png               ← data flow diagram
│   ├── process-flow.png            ← log.sh process flow
│   ├── watcher-pipeline.png        ← watcher pipeline diagram
│   └── gen_diagrams.py             ← script that generates the PNGs
├── scripts/
│   ├── log.sh                      ← interactive daily log CLI
│   ├── inbox_watcher.py            ← watchdog daemon (classify + file)
│   ├── start_watcher.sh            ← start watcher as background daemon
│   ├── stop_watcher.sh             ← stop watcher
│   ├── setup-cron.sh               ← install daily reminder (cron/launchd)
│   ├── remind.sh                   ← reminder notification script
│   └── git-post-commit-hook.sh     ← per-repo git hook
├── hooks/
│   └── obsidian_logger.sh          ← Claude Code Stop hook
├── dashboard/
│   ├── Home.md                     ← Dataview dashboard
│   └── SETUP.md                    ← setup guide
└── vault/                          ← open this as your Obsidian vault
    ├── 00-Inbox/
    ├── 10-LLM-Chats/
    ├── 20-Code-Sessions/
    ├── 30-Research/
    ├── 40-Experiments/
    ├── 50-Daily-Logs/
    ├── 55-Journals/
    ├── 60-Permanent/
    ├── _Dashboard/
    │   ├── Home.md
    │   └── SETUP.md
    ├── _Scripts/
    └── _Templates/
        ├── daily-log.md
        ├── journal.md
        └── experiment.md
```
