#!/usr/bin/env bash
# ============================================================
# Team Member Setup — run once after cloning the repo
# ============================================================
# What it does:
#   1. Asks your name (saved for future logs)
#   2. Creates a shell alias 'rlog' for quick logging
#   3. Creates a shell alias 'rlog-sync' for commit + push
#   4. Optionally installs the daily reminder
#
# Usage:
#   git clone <repo-url> research-log
#   cd research-log
#   bash scripts/setup-member.sh
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

BOLD='\033[1m'
CYAN='\033[36m'
GREEN='\033[32m'
DIM='\033[2m'
RESET='\033[0m'

echo ""
printf "${BOLD}========================================${RESET}\n"
printf "${BOLD}  Research Log — Team Member Setup${RESET}\n"
printf "${BOLD}========================================${RESET}\n"
echo ""

# ── Step 1: Name ────────────────────────────────────────────
printf "${CYAN}Your name:${RESET} "
read -r NAME

if [[ -z "$NAME" ]]; then
    echo "Name is required."
    exit 1
fi

echo "$NAME" > "$PROJECT_ROOT/.contributor"
printf "${GREEN}Saved.${RESET} Your entries will be attributed to: ${NAME}\n"

# ── Step 2: Detect shell config ─────────────────────────────
if [[ -f "$HOME/.zshrc" ]]; then
    SHELL_RC="$HOME/.zshrc"
elif [[ -f "$HOME/.bashrc" ]]; then
    SHELL_RC="$HOME/.bashrc"
else
    SHELL_RC="$HOME/.bashrc"
fi

# ── Step 3: Create aliases ──────────────────────────────────
ALIAS_BLOCK="
# ── Research Log ────────────────────────────────────────────
alias rlog='bash ${PROJECT_ROOT}/scripts/log.sh'
alias rlog-sync='bash ${PROJECT_ROOT}/scripts/sync.sh'
alias rlog-journal='bash ${PROJECT_ROOT}/scripts/log.sh --type journal'
alias rlog-experiment='bash ${PROJECT_ROOT}/scripts/log.sh --type experiment'
# ── end Research Log ────────────────────────────────────────"

# Check if already installed
if grep -q "# ── Research Log" "$SHELL_RC" 2>/dev/null; then
    # Remove old block and re-add
    sed -i '/# ── Research Log/,/# ── end Research Log/d' "$SHELL_RC"
fi

echo "$ALIAS_BLOCK" >> "$SHELL_RC"

printf "${GREEN}Aliases added to ${SHELL_RC}:${RESET}\n"
echo "  rlog            — structured daily log"
echo "  rlog-journal    — freestyle journal"
echo "  rlog-experiment — experiment log"
echo "  rlog-sync       — commit and push your entries"

# ── Step 4: Optional daily reminder ─────────────────────────
echo ""
printf "${CYAN}Set up a daily reminder to log? [y/N]:${RESET} "
read -r REMIND

if [[ "$REMIND" =~ ^[Yy] ]]; then
    printf "${CYAN}What time? (24h, default 17:00):${RESET} "
    read -r REMIND_TIME
    REMIND_TIME="${REMIND_TIME:-17:00}"
    REMIND_HOUR="${REMIND_TIME%%:*}"
    REMIND_MIN="${REMIND_TIME##*:}"
    bash "$SCRIPT_DIR/setup-cron.sh" --hour "$REMIND_HOUR" --minute "$REMIND_MIN"
fi

# ── Done ────────────────────────────────────────────────────
echo ""
printf "${BOLD}${GREEN}Setup complete!${RESET}\n"
echo ""
echo "  Daily workflow:"
echo "    1. rlog              — log your work"
echo "    2. rlog-sync         — push to the shared repo"
echo ""
echo "  Reload your shell first:"
echo "    source ${SHELL_RC}"
echo ""
