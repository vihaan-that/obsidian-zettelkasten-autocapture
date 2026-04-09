#!/usr/bin/env bash
# ============================================================
# Sync — commit local entries and push to the shared repo
# ============================================================
# Usage:
#   bash scripts/sync.sh           # commit + push
#   bash scripts/sync.sh --pull    # pull only (get latest from team)
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

BOLD='\033[1m'
GREEN='\033[32m'
YELLOW='\033[33m'
DIM='\033[2m'
RESET='\033[0m'

MODE="${1:-push}"

# ── Get contributor name ────────────────────────────────────
CONTRIBUTOR="unknown"
if [[ -f "$PROJECT_ROOT/.contributor" ]]; then
    CONTRIBUTOR="$(cat "$PROJECT_ROOT/.contributor")"
fi

# ── Pull latest first (rebase to keep history clean) ────────
printf "${DIM}Pulling latest...${RESET}\n"
git pull --rebase --autostash 2>&1 | tail -3

if [[ "$MODE" == "--pull" ]]; then
    printf "${GREEN}Up to date.${RESET}\n"
    exit 0
fi

# ── Check for changes ──────────────────────────────────────
CHANGES="$(git status --porcelain -- vault/ 2>/dev/null)"

if [[ -z "$CHANGES" ]]; then
    printf "${YELLOW}No new entries to sync.${RESET}\n"
    exit 0
fi

# ── Count what's new ───────────────────────────────────────
NEW_COUNT="$(echo "$CHANGES" | wc -l | tr -d ' ')"
printf "${GREEN}Found ${NEW_COUNT} changed file(s) in vault/${RESET}\n"

# ── Stage only vault entries ────────────────────────────────
git add vault/

# ── Commit with contributor name and date ───────────────────
DATE="$(date +%Y-%m-%d)"
git commit -m "$(cat <<EOF
logs: ${CONTRIBUTOR} — ${DATE}

${NEW_COUNT} entry/entries synced.
EOF
)"

# ── Push ────────────────────────────────────────────────────
printf "${DIM}Pushing...${RESET}\n"
if git push 2>&1; then
    printf "${GREEN}${BOLD}Synced!${RESET} ${NEW_COUNT} entry/entries pushed.\n"
else
    printf "${YELLOW}Push failed — you may need to pull first. Run: rlog-sync again${RESET}\n"
    exit 1
fi
