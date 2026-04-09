#!/usr/bin/env bash
# ============================================================
# Start the inbox watcher as a background daemon.
# Run once after login — add to your shell profile or autostart.
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VAULT_PATH="${VAULT_PATH:-$PROJECT_ROOT/vault}"
SCRIPT="${SCRIPT_DIR}/inbox_watcher.py"
PID_FILE="${VAULT_PATH}/_Scripts/watcher.pid"
LOG_FILE="${VAULT_PATH}/_Scripts/watcher.log"
GEMINI_KEY="${GEMINI_API_KEY:-}"

mkdir -p "${VAULT_PATH}/_Scripts"

# ── Check for existing running watcher ───────────────────────
if [ -f "$PID_FILE" ]; then
    OLD_PID="$(cat "$PID_FILE")"
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Watcher already running (PID $OLD_PID). Use stop_watcher.sh first."
        exit 0
    else
        echo "Stale PID file found — cleaning up."
        rm -f "$PID_FILE"
    fi
fi

# ── Ensure dependencies ───────────────────────────────────────
echo "Checking Python dependencies..."

python3 -c "import watchdog" 2>/dev/null || {
    echo "Installing watchdog..."
    pip install watchdog --quiet
}

if [ -n "$GEMINI_KEY" ]; then
    python3 -c "from google import genai" 2>/dev/null || {
        echo "Installing google-genai (Gemini support)..."
        pip install google-genai --quiet
    }
else
    echo "GEMINI_API_KEY not set — watcher will use keyword classification."
    echo "To enable AI: export GEMINI_API_KEY='your-key' before running this script."
fi

# ── Launch ────────────────────────────────────────────────────
echo "Starting inbox watcher..."
export VAULT_PATH
nohup python3 "$SCRIPT" >> "$LOG_FILE" 2>&1 &
WPD=$!
echo "$WPD" > "$PID_FILE"

sleep 1
if kill -0 "$WPD" 2>/dev/null; then
    echo "Watcher started. PID $WPD saved to _Scripts/watcher.pid"
    echo "Logs: ${LOG_FILE}"
else
    echo "ERROR: watcher failed to start. Check ${LOG_FILE}"
    rm -f "$PID_FILE"
    exit 1
fi
