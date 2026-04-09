#!/usr/bin/env bash
# ============================================================
# Research Log Reminder
# ============================================================
# Called by cron/launchd. Sends a desktop notification and
# optionally opens a terminal with log.sh.
#
# Modes:
#   remind.sh notify   — notification only (default)
#   remind.sh open     — notification + open terminal with log.sh
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_SCRIPT="${SCRIPT_DIR}/log.sh"
MODE="${1:-notify}"
OS="$(uname -s)"

# ── Notification ────────────────────────────────────────────
send_notify() {
    local title="Research Log"
    local body="Time to log your work. Run: bash scripts/log.sh"

    case "$OS" in
        Linux)
            # cron doesn't have DISPLAY/DBUS — find the active session
            export DISPLAY="${DISPLAY:-:0}"
            export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$(id -u)/bus}"

            if command -v notify-send &>/dev/null; then
                notify-send -u normal -i dialog-information "$title" "$body"
            fi
            ;;
        Darwin)
            osascript -e "display notification \"$body\" with title \"$title\" sound name \"Blow\""
            ;;
    esac
}

# ── Open terminal with log.sh ──────────────────────────────
open_terminal() {
    case "$OS" in
        Linux)
            export DISPLAY="${DISPLAY:-:0}"
            if command -v gnome-terminal &>/dev/null; then
                gnome-terminal -- bash -c "'$LOG_SCRIPT'; echo; echo 'Press Enter to close.'; read"
            elif command -v xfce4-terminal &>/dev/null; then
                xfce4-terminal -e "bash -c \"'$LOG_SCRIPT'; echo; echo 'Press Enter to close.'; read\""
            elif command -v konsole &>/dev/null; then
                konsole -e bash -c "'$LOG_SCRIPT'; echo; echo 'Press Enter to close.'; read"
            elif command -v x-terminal-emulator &>/dev/null; then
                x-terminal-emulator -e bash -c "'$LOG_SCRIPT'; echo; echo 'Press Enter to close.'; read"
            fi
            ;;
        Darwin)
            osascript -e "
                tell application \"Terminal\"
                    activate
                    do script \"bash '$LOG_SCRIPT'\"
                end tell
            "
            ;;
    esac
}

# ── Main ────────────────────────────────────────────────────
send_notify

if [[ "$MODE" == "open" ]]; then
    open_terminal
fi
