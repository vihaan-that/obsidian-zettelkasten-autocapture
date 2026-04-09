#!/usr/bin/env bash
# ============================================================
# Team Research Daily Log — Interactive CLI
# ============================================================
# Usage:
#   bash scripts/log.sh                  # interactive mode
#   bash scripts/log.sh --name alice     # skip name prompt
#   bash scripts/log.sh --type journal   # skip type prompt
#   bash scripts/log.sh --editor         # open in $EDITOR for freestyle
# ============================================================

set -euo pipefail

# ── Config ──────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VAULT_PATH="${VAULT_PATH:-$PROJECT_ROOT/vault}"
INBOX="${VAULT_PATH}/00-Inbox"
TEMPLATES="${VAULT_PATH}/_Templates"

mkdir -p "$INBOX"

DATE="$(date +%Y-%m-%d)"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"

# ── Colors ──────────────────────────────────────────────────
BOLD='\033[1m'
DIM='\033[2m'
CYAN='\033[36m'
GREEN='\033[32m'
YELLOW='\033[33m'
RESET='\033[0m'

# ── Parse args ──────────────────────────────────────────────
CONTRIBUTOR=""
LOG_TYPE=""
USE_EDITOR=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --name)  CONTRIBUTOR="$2"; shift 2 ;;
        --type)  LOG_TYPE="$2"; shift 2 ;;
        --editor) USE_EDITOR=true; shift ;;
        -h|--help)
            echo "Usage: log.sh [--name NAME] [--type daily-log|journal|experiment] [--editor]"
            exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ── Helpers ─────────────────────────────────────────────────
prompt() {
    local label="$1" default="${2:-}"
    if [[ -n "$default" ]]; then
        printf "${CYAN}${label}${RESET} ${DIM}[${default}]${RESET}: "
    else
        printf "${CYAN}${label}${RESET}: "
    fi
    read -r input
    echo "${input:-$default}"
}

prompt_multiline() {
    local label="$1"
    printf "${CYAN}${label}${RESET} ${DIM}(blank line to finish)${RESET}:\n"
    local text=""
    while IFS= read -r line; do
        [[ -z "$line" ]] && break
        text+="${line}"$'\n'
    done
    echo "$text"
}

section_prompt() {
    local label="$1" hint="$2"
    printf "\n${BOLD}${label}${RESET}\n"
    printf "${DIM}${hint}${RESET}\n"
    prompt_multiline ">"
}

# ── Greeting ────────────────────────────────────────────────
echo ""
printf "${BOLD}========================================${RESET}\n"
printf "${BOLD}  Team Research Log  —  ${DATE}${RESET}\n"
printf "${BOLD}========================================${RESET}\n"
echo ""

# ── Contributor ─────────────────────────────────────────────
if [[ -z "$CONTRIBUTOR" ]]; then
    # Check for saved name
    NAME_CACHE="${PROJECT_ROOT}/.contributor"
    if [[ -f "$NAME_CACHE" ]]; then
        SAVED_NAME="$(cat "$NAME_CACHE")"
        CONTRIBUTOR="$(prompt "Your name" "$SAVED_NAME")"
    else
        CONTRIBUTOR="$(prompt "Your name")"
    fi
    echo "$CONTRIBUTOR" > "$NAME_CACHE"
fi

printf "${GREEN}Logging as: ${CONTRIBUTOR}${RESET}\n"

# ── Log type ────────────────────────────────────────────────
if [[ -z "$LOG_TYPE" ]]; then
    echo ""
    printf "${BOLD}What kind of entry?${RESET}\n"
    echo "  1) daily-log    — structured: work, pivots, decisions, status"
    echo "  2) journal      — freestyle: stream of consciousness"
    echo "  3) experiment   — hypothesis, setup, observations, result"
    echo ""
    TYPE_CHOICE="$(prompt "Pick [1/2/3]" "1")"
    case "$TYPE_CHOICE" in
        1|daily-log)   LOG_TYPE="daily-log" ;;
        2|journal)     LOG_TYPE="journal" ;;
        3|experiment)  LOG_TYPE="experiment" ;;
        *) LOG_TYPE="daily-log" ;;
    esac
fi

printf "${GREEN}Entry type: ${LOG_TYPE}${RESET}\n"

# ── Filename ────────────────────────────────────────────────
SAFE_NAME="$(echo "$CONTRIBUTOR" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//')"
FILENAME="${LOG_TYPE}-${DATE}-${SAFE_NAME}.md"
DEST="${INBOX}/${FILENAME}"

# ── Build the entry ─────────────────────────────────────────
case "$LOG_TYPE" in

# ── STRUCTURED DAILY LOG ────────────────────────────────────
daily-log)
    if $USE_EDITOR; then
        # Copy template and open in editor
        sed -e "s|{{date}}|$DATE|g" -e "s|{{contributor}}|$CONTRIBUTOR|g" \
            "$TEMPLATES/daily-log.md" > "$DEST"
        "${EDITOR:-vim}" "$DEST"
    else
        echo ""
        printf "${BOLD}Fill in each section. Blank line finishes each one.${RESET}\n"

        WORK="$(section_prompt \
            "What did you work on today?" \
            "Main tasks, deliverables, progress")"

        PIVOTS="$(section_prompt \
            "Any pivots or course corrections?" \
            "Plan changes, what shifted and why")"

        DECISIONS="$(section_prompt \
            "Key decisions & reasoning" \
            "What was decided, alternatives considered, why this path")"

        TANGENTS="$(section_prompt \
            "Tangents explored" \
            "Side investigations, rabbit holes, things that didn't pan out")"

        BLOCKERS="$(section_prompt \
            "Blockers & open questions" \
            "What's stuck, what needs input")"

        STATUS="$(section_prompt \
            "Status & next steps" \
            "Where things stand, what's queued for tomorrow")"

        LINKS="$(section_prompt \
            "Links & references (optional)" \
            "Papers, PRs, docs, Slack threads")"

        TAGS_INPUT="$(prompt "Tags (comma-separated, optional)" "daily-log")"
        IFS=',' read -ra TAG_ARRAY <<< "$TAGS_INPUT"
        TAGS_YAML=""
        for tag in "${TAG_ARRAY[@]}"; do
            tag="$(echo "$tag" | xargs)"  # trim whitespace
            TAGS_YAML+="  - \"${tag}\""$'\n'
        done

        cat > "$DEST" <<EOF
---
type: daily-log
date: ${DATE}
contributor: "${CONTRIBUTOR}"
status: "in-progress"
tags:
${TAGS_YAML:+${TAGS_YAML}}---

# Daily Log — ${DATE}

**Contributor:** ${CONTRIBUTOR}

## What I worked on today
${WORK}
## Pivots & course corrections
${PIVOTS}
## Key decisions & reasoning
${DECISIONS}
## Tangents explored
${TANGENTS}
## Blockers & open questions
${BLOCKERS}
## Status & next steps
${STATUS}
## Links & references
${LINKS}
EOF
    fi
    ;;

# ── FREESTYLE JOURNAL ──────────────────────────────────────
journal)
    if $USE_EDITOR; then
        sed -e "s|{{date}}|$DATE|g" -e "s|{{contributor}}|$CONTRIBUTOR|g" \
            "$TEMPLATES/journal.md" > "$DEST"
        "${EDITOR:-vim}" "$DEST"
    else
        echo ""
        printf "${BOLD}Write freely. Blank line to finish.${RESET}\n"
        printf "${DIM}Some prompts if you're stuck:${RESET}\n"
        printf "${DIM}  - What surprised you today?${RESET}\n"
        printf "${DIM}  - What's the thing you'll forget by next week?${RESET}\n"
        printf "${DIM}  - What would you tell a teammate picking this up cold?${RESET}\n"
        echo ""

        BODY="$(prompt_multiline "Journal")"

        TAGS_INPUT="$(prompt "Tags (comma-separated, optional)" "journal")"
        IFS=',' read -ra TAG_ARRAY <<< "$TAGS_INPUT"
        TAGS_YAML=""
        for tag in "${TAG_ARRAY[@]}"; do
            tag="$(echo "$tag" | xargs)"
            TAGS_YAML+="  - \"${tag}\""$'\n'
        done

        cat > "$DEST" <<EOF
---
type: journal
date: ${DATE}
contributor: "${CONTRIBUTOR}"
tags:
${TAGS_YAML:+${TAGS_YAML}}---

# Journal — ${DATE}

**Contributor:** ${CONTRIBUTOR}

${BODY}
EOF
    fi
    ;;

# ── EXPERIMENT ──────────────────────────────────────────────
experiment)
    if $USE_EDITOR; then
        sed -e "s|{{date}}|$DATE|g" -e "s|{{contributor}}|$CONTRIBUTOR|g" \
            "$TEMPLATES/experiment.md" > "$DEST"
        "${EDITOR:-vim}" "$DEST"
    else
        echo ""
        printf "${BOLD}Log your experiment. Blank line finishes each section.${RESET}\n"

        HYPOTHESIS="$(section_prompt \
            "Hypothesis" \
            "What are you testing? What do you expect?")"

        SETUP="$(section_prompt \
            "Setup" \
            "Parameters, data, environment, config")"

        OBSERVATIONS="$(section_prompt \
            "Observations" \
            "What actually happened? Raw notes, outputs")"

        RESULT="$(section_prompt \
            "Result" \
            "Did the hypothesis hold? What did you learn?")"

        NEXT="$(section_prompt \
            "Next" \
            "Follow-up experiments, things to try")"

        EXP_STATUS="$(prompt "Experiment status" "running")"

        TAGS_INPUT="$(prompt "Tags (comma-separated, optional)" "experiment")"
        IFS=',' read -ra TAG_ARRAY <<< "$TAGS_INPUT"
        TAGS_YAML=""
        for tag in "${TAG_ARRAY[@]}"; do
            tag="$(echo "$tag" | xargs)"
            TAGS_YAML+="  - \"${tag}\""$'\n'
        done

        cat > "$DEST" <<EOF
---
type: experiment
date: ${DATE}
contributor: "${CONTRIBUTOR}"
status: "${EXP_STATUS}"
tags:
${TAGS_YAML:+${TAGS_YAML}}---

# Experiment — ${DATE}

**Contributor:** ${CONTRIBUTOR}

## Hypothesis
${HYPOTHESIS}
## Setup
${SETUP}
## Observations
${OBSERVATIONS}
## Result
${RESULT}
## Next
${NEXT}
EOF
    fi
    ;;

esac

# ── Confirm ─────────────────────────────────────────────────
echo ""
printf "${GREEN}${BOLD}Logged!${RESET} ${DEST}\n"
printf "${DIM}The inbox watcher will classify, tag, and file it automatically.${RESET}\n"
printf "${DIM}Or view it directly in Obsidian under 00-Inbox/.${RESET}\n"
echo ""
