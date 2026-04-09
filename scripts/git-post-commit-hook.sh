#!/usr/bin/env bash
# ============================================================
# Research Log git post-commit hook
# ============================================================
# Install into any repo:
#   cp scripts/git-post-commit-hook.sh /path/to/repo/.git/hooks/post-commit
#   chmod +x /path/to/repo/.git/hooks/post-commit
# ============================================================

# ── Config ──────────────────────────────────────────────────
# Set VAULT_PATH in your environment, or update this default
VAULT_PATH="${VAULT_PATH:-$HOME/Documents/work/research-log/vault}"
INBOX="${VAULT_PATH}/00-Inbox"

# Contributor — git author name for this commit
CONTRIBUTOR="$(git log -1 --pretty=%an 2>/dev/null || whoami)"

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
contributor: "${CONTRIBUTOR}"
repo: ${REPO}
branch: ${BRANCH}
---

## Commit
${HASH_SHORT} — ${COMMIT_MSG}

## Files changed
${FILES_MD}

## My take
MARKDOWN

echo "Research Log: logged commit by ${CONTRIBUTOR} to ${FILENAME}"
