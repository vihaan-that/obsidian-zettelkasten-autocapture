#!/usr/bin/env bash
# ============================================================
# Setup daily research log reminder (cron on Linux, launchd on macOS)
# ============================================================
# Usage:
#   bash scripts/setup-cron.sh              # default: 5pm, notify only
#   bash scripts/setup-cron.sh --hour 17    # set hour (24h format)
#   bash scripts/setup-cron.sh --minute 30  # set minute
#   bash scripts/setup-cron.sh --open       # also open a terminal with log.sh
#   bash scripts/setup-cron.sh --remove     # remove the scheduled reminder
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REMIND_SCRIPT="${SCRIPT_DIR}/remind.sh"
OS="$(uname -s)"

# ── Defaults ────────────────────────────────────────────────
HOUR=17
MINUTE=0
MODE="notify"
REMOVE=false

# ── Parse args ──────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --hour)    HOUR="$2"; shift 2 ;;
        --minute)  MINUTE="$2"; shift 2 ;;
        --open)    MODE="open"; shift ;;
        --remove)  REMOVE=true; shift ;;
        -h|--help)
            echo "Usage: setup-cron.sh [--hour H] [--minute M] [--open] [--remove]"
            echo "  --hour H     Hour in 24h format (default: 17)"
            echo "  --minute M   Minute (default: 0)"
            echo "  --open       Also open a terminal with log.sh"
            echo "  --remove     Remove the scheduled reminder"
            exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

CRON_TAG="research-log-remind"
LAUNCHD_LABEL="com.research-log.remind"
LAUNCHD_PLIST="$HOME/Library/LaunchAgents/${LAUNCHD_LABEL}.plist"

# ── Remove ──────────────────────────────────────────────────
if $REMOVE; then
    case "$OS" in
        Linux)
            if crontab -l 2>/dev/null | grep -q "$CRON_TAG"; then
                crontab -l 2>/dev/null | grep -v "$CRON_TAG" | crontab -
                echo "Removed cron job."
            else
                echo "No cron job found to remove."
            fi
            ;;
        Darwin)
            if [[ -f "$LAUNCHD_PLIST" ]]; then
                launchctl unload "$LAUNCHD_PLIST" 2>/dev/null || true
                rm -f "$LAUNCHD_PLIST"
                echo "Removed launchd agent."
            else
                echo "No launchd agent found to remove."
            fi
            ;;
    esac
    exit 0
fi

# ── Install ─────────────────────────────────────────────────
chmod +x "$REMIND_SCRIPT"

case "$OS" in

# ── Linux: crontab ──────────────────────────────────────────
Linux)
    CRON_CMD="${MINUTE} ${HOUR} * * * bash ${REMIND_SCRIPT} ${MODE} # ${CRON_TAG}"

    # Remove old entry if exists, then add new one
    ( crontab -l 2>/dev/null | grep -v "$CRON_TAG"; echo "$CRON_CMD" ) | crontab -

    echo "Cron job installed:"
    echo "  Schedule: daily at $(printf '%02d:%02d' "$HOUR" "$MINUTE")"
    echo "  Mode: ${MODE}"
    echo "  Command: ${CRON_CMD}"
    echo ""
    echo "Verify with: crontab -l"
    echo "Remove with: bash scripts/setup-cron.sh --remove"
    ;;

# ── macOS: launchd ──────────────────────────────────────────
Darwin)
    mkdir -p "$HOME/Library/LaunchAgents"

    # Unload old agent if it exists
    if [[ -f "$LAUNCHD_PLIST" ]]; then
        launchctl unload "$LAUNCHD_PLIST" 2>/dev/null || true
    fi

    cat > "$LAUNCHD_PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${LAUNCHD_LABEL}</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>${REMIND_SCRIPT}</string>
        <string>${MODE}</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>${HOUR}</integer>
        <key>Minute</key>
        <integer>${MINUTE}</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>/tmp/research-log-remind.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/research-log-remind.log</string>
</dict>
</plist>
PLIST

    launchctl load "$LAUNCHD_PLIST"

    echo "launchd agent installed:"
    echo "  Schedule: daily at $(printf '%02d:%02d' "$HOUR" "$MINUTE")"
    echo "  Mode: ${MODE}"
    echo "  Plist: ${LAUNCHD_PLIST}"
    echo ""
    echo "Verify with: launchctl list | grep research-log"
    echo "Remove with: bash scripts/setup-cron.sh --remove"
    ;;

*)
    echo "Unsupported OS: ${OS}"
    exit 1
    ;;
esac
