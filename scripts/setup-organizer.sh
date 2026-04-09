#!/usr/bin/env bash
# ============================================================
# Setup the evening LLM organizer on the admin PC
# ============================================================
# Installs a cron (Linux) or launchd (macOS) job that runs
# organizer.py every evening. This is for the admin PC only —
# team members don't need this.
#
# Usage:
#   bash scripts/setup-organizer.sh                    # default: 9pm, anthropic
#   bash scripts/setup-organizer.sh --hour 21          # custom hour
#   bash scripts/setup-organizer.sh --provider gemini  # use gemini
#   bash scripts/setup-organizer.sh --remove           # remove the job
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ORGANIZER="$SCRIPT_DIR/organizer.py"
OS="$(uname -s)"

# ── Defaults ────────────────────────────────────────────────
HOUR=21
MINUTE=0
PROVIDER="anthropic"
REMOVE=false
PYTHON="${PYTHON:-python3}"

# ── Parse args ──────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --hour)     HOUR="$2"; shift 2 ;;
        --minute)   MINUTE="$2"; shift 2 ;;
        --provider) PROVIDER="$2"; shift 2 ;;
        --python)   PYTHON="$2"; shift 2 ;;
        --remove)   REMOVE=true; shift ;;
        -h|--help)
            echo "Usage: setup-organizer.sh [--hour H] [--minute M] [--provider anthropic|gemini] [--remove]"
            echo "  --hour H       Hour in 24h format (default: 21)"
            echo "  --minute M     Minute (default: 0)"
            echo "  --provider P   LLM provider: anthropic or gemini (default: anthropic)"
            echo "  --python PATH  Python binary (default: python3)"
            echo "  --remove       Remove the scheduled organizer"
            exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ── Validate ────────────────────────────────────────────────
if [[ "$HOUR" -lt 0 || "$HOUR" -gt 23 ]] 2>/dev/null; then
    echo "ERROR: --hour must be 0-23 (got: $HOUR)"; exit 1
fi
if [[ "$MINUTE" -lt 0 || "$MINUTE" -gt 59 ]] 2>/dev/null; then
    echo "ERROR: --minute must be 0-59 (got: $MINUTE)"; exit 1
fi

CRON_TAG="research-log-organizer"
LAUNCHD_LABEL="com.research-log.organizer"
LAUNCHD_PLIST="$HOME/Library/LaunchAgents/${LAUNCHD_LABEL}.plist"

# ── Build the wrapper script (handles conda/venv activation) ─
WRAPPER="$SCRIPT_DIR/run-organizer.sh"
cat > "$WRAPPER" <<WRAP
#!/usr/bin/env bash
# Auto-generated wrapper for the organizer cron job.
# Handles conda activation and environment setup.

# Activate conda if available
if [ -f "\$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "\$HOME/miniconda3/etc/profile.d/conda.sh"
    conda activate
elif [ -f "\$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    source "\$HOME/anaconda3/etc/profile.d/conda.sh"
    conda activate
fi

# Set API key from keyring or env file
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

cd "$PROJECT_ROOT"
$PYTHON "$ORGANIZER" --provider $PROVIDER 2>&1
WRAP
chmod +x "$WRAPPER"

# ── Remove ──────────────────────────────────────────────────
if $REMOVE; then
    case "$OS" in
        Linux)
            if crontab -l 2>/dev/null | grep -q "$CRON_TAG"; then
                crontab -l 2>/dev/null | grep -v "$CRON_TAG" | crontab -
                echo "Removed cron job."
            else
                echo "No cron job found."
            fi
            ;;
        Darwin)
            if [[ -f "$LAUNCHD_PLIST" ]]; then
                launchctl unload "$LAUNCHD_PLIST" 2>/dev/null || true
                rm -f "$LAUNCHD_PLIST"
                echo "Removed launchd agent."
            else
                echo "No launchd agent found."
            fi
            ;;
    esac
    rm -f "$WRAPPER"
    exit 0
fi

# ── Check API key ───────────────────────────────────────────
if [[ "$PROVIDER" == "anthropic" ]]; then
    KEY_VAR="ANTHROPIC_API_KEY"
elif [[ "$PROVIDER" == "gemini" ]]; then
    KEY_VAR="GEMINI_API_KEY"
fi

if [[ -z "${!KEY_VAR:-}" ]]; then
    echo ""
    echo "WARNING: $KEY_VAR is not set in your current environment."
    echo "The organizer needs it at runtime. You have two options:"
    echo ""
    echo "  1. Create $PROJECT_ROOT/.env with:"
    echo "     ${KEY_VAR}=your-key-here"
    echo ""
    echo "  2. Export it in your shell profile (~/.bashrc or ~/.zshrc):"
    echo "     export ${KEY_VAR}=your-key-here"
    echo ""
fi

# ── Install ─────────────────────────────────────────────────
case "$OS" in

Linux)
    CRON_CMD="${MINUTE} ${HOUR} * * * bash ${WRAPPER} >> ${VAULT_PATH}/_Scripts/organizer.log 2>&1 # ${CRON_TAG}"
    ( crontab -l 2>/dev/null | grep -v "$CRON_TAG"; echo "$CRON_CMD" ) | crontab -

    echo "Cron job installed:"
    echo "  Schedule: daily at $(printf '%02d:%02d' "$HOUR" "$MINUTE")"
    echo "  Provider: ${PROVIDER}"
    echo "  Command: ${CRON_CMD}"
    echo ""
    echo "Verify:  crontab -l | grep organizer"
    echo "Remove:  bash scripts/setup-organizer.sh --remove"
    echo "Logs:    vault/_Scripts/organizer.log"
    ;;

Darwin)
    mkdir -p "$HOME/Library/LaunchAgents"
    [[ -f "$LAUNCHD_PLIST" ]] && launchctl unload "$LAUNCHD_PLIST" 2>/dev/null || true

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
        <string>${WRAPPER}</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>${HOUR}</integer>
        <key>Minute</key>
        <integer>${MINUTE}</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>${VAULT_PATH}/_Scripts/organizer.log</string>
    <key>StandardErrorPath</key>
    <string>${VAULT_PATH}/_Scripts/organizer.log</string>
</dict>
</plist>
PLIST

    launchctl load "$LAUNCHD_PLIST"

    echo "launchd agent installed:"
    echo "  Schedule: daily at $(printf '%02d:%02d' "$HOUR" "$MINUTE")"
    echo "  Provider: ${PROVIDER}"
    echo "  Plist: ${LAUNCHD_PLIST}"
    echo ""
    echo "Verify:  launchctl list | grep research-log"
    echo "Remove:  bash scripts/setup-organizer.sh --remove"
    echo "Logs:    vault/_Scripts/organizer.log"
    ;;

*)
    echo "Unsupported OS: ${OS}"
    exit 1
    ;;
esac
