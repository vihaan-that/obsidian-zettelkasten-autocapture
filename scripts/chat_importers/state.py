# scripts/chat_importers/state.py
import sqlite3
import os
from pathlib import Path

class ImportState:
    """Track imported chats to avoid duplicates."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(
                Path(__file__).parent.parent.parent,  # research-log root
                'vault', '_Scripts', 'import_state.db'
            )

        self.db_path = db_path
        self.timeout = 30  # seconds, for concurrent access
        self._ensure_db()

    def _ensure_db(self):
        """Create database if it doesn't exist."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS imported_chats (
                    tool TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    imported_at TEXT NOT NULL,
                    PRIMARY KEY (tool, source_id)
                )
            ''')
            conn.commit()

    def is_imported(self, tool: str, source_id: str) -> bool:
        """Check if a chat has already been imported."""
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            cursor = conn.execute(
                'SELECT 1 FROM imported_chats WHERE tool = ? AND source_id = ?',
                (tool, source_id)
            )
            return cursor.fetchone() is not None

    def mark_imported(self, tool: str, source_id: str):
        """Mark a chat as imported."""
        from datetime import datetime
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            conn.execute(
                'INSERT OR IGNORE INTO imported_chats (tool, source_id, imported_at) VALUES (?, ?, ?)',
                (tool, source_id, datetime.utcnow().isoformat())
            )
            conn.commit()

    def list_imported(self, tool: str = None) -> list:
        """List all imported chat IDs, optionally filtered by tool."""
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            if tool:
                cursor = conn.execute(
                    'SELECT source_id FROM imported_chats WHERE tool = ? ORDER BY imported_at DESC',
                    (tool,)
                )
            else:
                cursor = conn.execute(
                    'SELECT tool, source_id FROM imported_chats ORDER BY imported_at DESC'
                )
            return cursor.fetchall()
