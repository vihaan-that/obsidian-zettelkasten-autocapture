#!/usr/bin/env bash
# ============================================================
# Obsidian git post-commit hook template
# ============================================================
# Install into any repo:
#   cp /home/vihaan/Documents/Work/_Scripts/git-post-commit-hook.sh \
#      /path/to/your/repo/.git/hooks/post-commit
#   chmod +x /path/to/your/repo/.git/hooks/post-commit
# ============================================================

VAULT_PATH="/home/vihaan/Documents/Work"
INBOX="${VAULT_PATH}/00-Inbox"

mkdir -p "$INBOX"

REPO="$(git rev-parse --show-toplevel 2>/dev/null | xargs basename)"
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "—")"
HASH_SHORT="$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")"
COMMIT_MSG="$(git log -1 --pretty=%s 2>/dev/null || echo "(no message)")"
DATE="$(date +%Y-%m-%d)"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
FILENAME="git-${REPO}-${TIMESTAMP}.md"
DEST="${INBOX}/${FILENAME}"

CHANGED_FILES="$(git diff --name-only HEAD~1 HEAD 2>/dev/null)"
if [ -z "$CHANGED_FILES" ]; then
    FILES_MD="- none detected"
else
    FILES_MD="$(echo "$CHANGED_FILES" | sed 's/^/- /')"
fi

cat > "$DEST" <<MARKDOWN
---
type: code-session
date: ${DATE}
repo: ${REPO}
branch: ${BRANCH}
---

## Commit
${HASH_SHORT} — ${COMMIT_MSG}

## Files changed
${FILES_MD}

## My take
MARKDOWN

echo "Obsidian: logged commit to ${FILENAME}"
