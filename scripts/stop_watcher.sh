#!/usr/bin/env bash
# Stop the Obsidian inbox watcher daemon.

VAULT_PATH="/home/vihaan/Documents/Work"
PID_FILE="${VAULT_PATH}/_Scripts/watcher.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "No watcher.pid found — watcher may not be running."
    exit 0
fi

PID="$(cat "$PID_FILE")"

if kill -0 "$PID" 2>/dev/null; then
    kill "$PID"
    rm -f "$PID_FILE"
    echo "Watcher stopped (PID $PID)."
else
    echo "Process $PID not found — already stopped."
    rm -f "$PID_FILE"
fi
