"""Importer for Microsoft Copilot chats."""

import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import platform
import glob

from .base import ChatImporter, ChatMessage

class CopilotImporter(ChatImporter):
    """Import chats from Microsoft Copilot (cross-platform)."""

    def __init__(self, state=None):
        super().__init__(state)
        self.chat_dir = self._get_chat_dir()

    @property
    def tool_name(self) -> str:
        return 'copilot'

    def _get_chat_dir(self) -> Optional[str]:
        """Detect Copilot chat directory (platform-specific)."""
        home = Path.home()
        system = platform.system()

        candidates = []

        if system == 'Windows':
            # Windows paths
            appdata = os.getenv('APPDATA')
            localappdata = os.getenv('LOCALAPPDATA')
            if appdata:
                candidates.append(Path(appdata) / 'Microsoft' / 'Copilot' / 'chats')
            if localappdata:
                candidates.append(Path(localappdata) / 'Microsoft' / 'Copilot' / 'chats')

        elif system == 'Darwin':
            # macOS paths
            candidates = [
                home / 'Library' / 'Application Support' / 'Microsoft Copilot' / 'chats',
                home / 'Library' / 'Application Support' / 'Copilot' / 'chats',
                home / 'Library' / 'Preferences' / 'Copilot' / 'chats',
            ]

        else:
            # Linux paths
            candidates = [
                home / '.config' / 'copilot' / 'chats',
                home / '.local' / 'share' / 'copilot' / 'chats',
                home / '.config' / 'Microsoft Copilot' / 'chats',
            ]

        for path in candidates:
            if path.exists() and path.is_dir():
                return str(path)

        return None

    def find_new_chats(self) -> List[str]:
        """Find unimported Copilot chats."""
        if not self.chat_dir:
            return []

        chat_files = []

        # Look for JSON files
        json_files = glob.glob(os.path.join(self.chat_dir, '*.json'))
        chat_files.extend(json_files)

        # Look for SQLite database (alternative format)
        db_files = glob.glob(os.path.join(self.chat_dir, '*.db'))
        db_files += glob.glob(os.path.join(self.chat_dir, '*.sqlite'))
        # Filter out state.db files
        db_files = [f for f in db_files if not f.endswith('state.db')]
        chat_files.extend(db_files)

        # Filter to unimported
        if self.state:
            new_chats = [
                f for f in chat_files
                if not self.state.is_imported(self.tool_name, os.path.splitext(os.path.basename(f))[0])
            ]
            return new_chats

        return chat_files

    def parse_chat(self, path: str) -> Dict:
        """Parse Copilot chat file (JSON or SQLite)."""
        filename = os.path.basename(path)

        if path.endswith('.json'):
            return self._parse_json_chat(path, filename)
        elif path.endswith(('.db', '.sqlite')):
            return self._parse_db_chat(path, filename)
        else:
            raise ValueError(f"Unknown file format: {path}")

    def _parse_json_chat(self, path: str, filename: str) -> Dict:
        """Parse JSON format Copilot chat."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        messages = []

        if isinstance(data, dict):
            # Extract messages from various possible structures
            chat_messages = data.get('messages') or data.get('conversation') or []

            for msg in chat_messages:
                if isinstance(msg, dict):
                    role = msg.get('role', msg.get('author', 'user'))
                    content = msg.get('content', msg.get('text', ''))
                    timestamp_str = msg.get('timestamp', msg.get('created_at'))
                    timestamp = None
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str)
                        except:
                            pass
                    messages.append(ChatMessage(role, content, timestamp))

        # Extract date
        date = None
        for possible_field in ['created_at', 'timestamp', 'updated_at']:
            if possible_field in data:
                try:
                    date = datetime.fromisoformat(data[possible_field])
                    break
                except:
                    pass

        if not date and messages:
            date = messages[0].timestamp or datetime.now()

        if not date:
            date = datetime.now()

        source_id = os.path.splitext(filename)[0]

        return {
            'source_id': source_id,
            'messages': messages,
            'date': date,
            'tool': self.tool_name,
            'metadata': data.get('metadata', {})
        }

    def _parse_db_chat(self, path: str, filename: str) -> Dict:
        """Parse SQLite database Copilot chat."""
        messages = []
        date = datetime.now()

        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()

            # Try common table structures
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            if not tables:
                # Database is empty or malformed
                conn.close()
                return {
                    'source_id': os.path.splitext(filename)[0],
                    'messages': [],
                    'date': date,
                    'tool': self.tool_name,
                    'metadata': {}
                }

            # Look for messages/conversations table
            message_table = None
            for table in ['messages', 'conversations', 'chats']:
                if table in tables:
                    message_table = table
                    break

            if message_table:
                # Generic query to extract message-like data
                cursor.execute(f"SELECT * FROM {message_table} LIMIT 1")
                columns = [desc[0] for desc in cursor.description]

                # Find role and content columns
                role_col = next((c for c in columns if 'role' in c.lower()), 'role')
                content_col = next((c for c in columns if 'content' in c.lower() or 'text' in c.lower()), 'content')

                cursor.execute(f"SELECT {role_col}, {content_col} FROM {message_table}")
                for row in cursor.fetchall():
                    role, content = row[0], row[1]
                    messages.append(ChatMessage(str(role), str(content)))

            conn.close()

        except Exception as e:
            # If parsing fails, return empty messages (don't create garbage)
            pass

        source_id = os.path.splitext(filename)[0]

        return {
            'source_id': source_id,
            'messages': messages,  # Empty if parsing failed
            'date': date,
            'tool': self.tool_name,
            'metadata': {}
        }
