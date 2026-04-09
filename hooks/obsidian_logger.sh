#!/usr/bin/env bash
# Claude Code Stop hook — logs each session to the research log vault inbox.
# Registered under hooks.Stop in ~/.claude/settings.json
# Receives session JSON on stdin from Claude Code.

# ── Config ──────────────────────────────────────────────────
# Set VAULT_PATH to your vault location, or it defaults to vault/ in the project root
VAULT_PATH="${VAULT_PATH:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/vault}"
INBOX="${VAULT_PATH}/00-Inbox"
LOG="${VAULT_PATH}/_Scripts/watcher.log"

# Contributor name — set in env or falls back to git user or system user
CONTRIBUTOR="${LOG_CONTRIBUTOR:-$(git config user.name 2>/dev/null || whoami)}"

mkdir -p "$INBOX"

# ── Read stdin ───────────────────────────────────────────────
INPUT="$(cat)"

# ── Extract fields from session JSON ────────────────────────
SESSION_ID="$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('session_id', d.get('sessionId', 'unknown')))
except Exception:
    print('unknown')
" 2>/dev/null)"

CWD="$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('cwd', ''))
except Exception:
    print('')
" 2>/dev/null)"

TRANSCRIPT_PATH="$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('transcript_path', d.get('transcriptPath', '')))
except Exception:
    print('')
" 2>/dev/null)"

# ── Git info ─────────────────────────────────────────────────
REPO="no-git"
BRANCH="—"
if [ -n "$CWD" ] && [ -d "$CWD" ]; then
    REPO="$(git -C "$CWD" rev-parse --show-toplevel 2>/dev/null | xargs basename 2>/dev/null || echo "no-git")"
    BRANCH="$(git -C "$CWD" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "—")"
fi

# ── Changed files ────────────────────────────────────────────
CHANGED_FILES="none detected"
if [ -n "$CWD" ] && [ -d "$CWD" ]; then
    FILES="$(git -C "$CWD" diff --name-only HEAD~1 HEAD 2>/dev/null)"
    [ -n "$FILES" ] && CHANGED_FILES="$FILES"
fi

# ── First 5 user prompts from transcript ─────────────────────
PROMPTS="*(transcript not available)*"
if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
    PROMPTS="$(python3 -c "
import sys, json

path = sys.argv[1]
try:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    messages = []
    if isinstance(data, list):
        messages = data
    elif isinstance(data, dict):
        messages = data.get('messages', data.get('conversation', []))

    user_msgs = [
        m for m in messages
        if isinstance(m, dict) and m.get('role') == 'user'
    ][:5]

    for i, m in enumerate(user_msgs, 1):
        content = m.get('content', '')
        if isinstance(content, list):
            text_parts = [
                b.get('text', '') for b in content
                if isinstance(b, dict) and b.get('type') == 'text'
            ]
            content = ' '.join(text_parts)
        content = str(content).replace('\n', ' ')[:200]
        print(f'{i}. {content}')
except Exception as e:
    print(f'(could not parse transcript: {e})')
" "$TRANSCRIPT_PATH" 2>/dev/null)"
fi

# ── Build note ───────────────────────────────────────────────
DATE="$(date +%Y-%m-%d)"
SESSION_SHORT="${SESSION_ID:0:8}"
FILENAME="cc-${DATE}-${SESSION_SHORT}.md"
DEST="${INBOX}/${FILENAME}"

if [ "$CHANGED_FILES" != "none detected" ]; then
    FILES_MD="$(echo "$CHANGED_FILES" | sed 's/^/- /')"
else
    FILES_MD="- none detected"
fi

cat > "$DEST" <<MARKDOWN
---
type: code-session
date: ${DATE}
contributor: "${CONTRIBUTOR}"
repo: ${REPO}
branch: ${BRANCH}
session_id: ${SESSION_SHORT}
summary: ""
tags:
  - "code-session"
---

## Session summary
*Waiting for AI processing...*

## Prompts (first 5)
${PROMPTS}

## Files touched
${FILES_MD}

## My take
MARKDOWN

echo "$(date '+%Y-%m-%d %H:%M:%S')  [obsidian_logger] wrote ${FILENAME} (${CONTRIBUTOR})" >> "$LOG"
