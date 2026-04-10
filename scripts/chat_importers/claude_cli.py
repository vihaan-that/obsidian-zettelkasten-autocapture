# scripts/chat_importers/claude_cli.py
"""Importer for Claude CLI chats."""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import glob

from .base import ChatImporter, ChatMessage

class ClaudeCliImporter(ChatImporter):
    """Import chats from Claude CLI."""

    def __init__(self, state=None):
        super().__init__(state)
        self.chat_dir = self._get_chat_dir()

    @property
    def tool_name(self) -> str:
        return 'claude-cli'

    def _get_chat_dir(self) -> Optional[str]:
        """Detect Claude CLI chat directory."""
        # Try common locations
        home = Path.home()

        candidates = [
            home / '.claude' / 'chats',
            home / '.config' / 'claude' / 'chats',
            home / '.local' / 'share' / 'claude' / 'chats',
        ]

        for path in candidates:
            if path.exists() and path.is_dir():
                return str(path)

        return None

    def find_new_chats(self) -> List[str]:
        """Find unimported Claude CLI chats."""
        if not self.chat_dir:
            return []

        # Assume .jsonl files in the chats directory are chat files
        chat_files = glob.glob(os.path.join(self.chat_dir, '*.jsonl'))

        # Filter to unimported chats
        if self.state:
            new_chats = [
                f for f in chat_files
                if not self.state.is_imported(self.tool_name, os.path.basename(f))
            ]
            return new_chats

        return chat_files

    def parse_chat(self, path: str) -> Dict:
        """Parse Claude CLI chat JSONL file."""
        messages = []
        date = datetime.now()
        chat_id = None

        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    # Extract message info
                    msg_type = obj.get('type', '')

                    # Capture chat ID from first message
                    if not chat_id:
                        chat_id = obj.get('uuid', '')

                    # Extract timestamp for dating the chat
                    if 'timestamp' in obj:
                        try:
                            ts = datetime.fromisoformat(obj['timestamp'].replace('Z', '+00:00'))
                            if date == datetime.now() or ts < date:
                                date = ts
                        except:
                            pass

                    # Extract message content based on type
                    if msg_type == 'user':
                        content = obj.get('text', '')
                        if content:
                            messages.append(ChatMessage('user', content))

                    elif msg_type == 'assistant':
                        # Assistant messages may have thinking and content
                        content_parts = []

                        # Add thinking if present
                        if 'thinking' in obj and obj['thinking']:
                            thinking = obj['thinking']
                            if isinstance(thinking, list):
                                content_parts.extend(thinking)
                            else:
                                content_parts.append(str(thinking))

                        # Add main content
                        if 'content' in obj and obj['content']:
                            content_obj = obj['content']
                            if isinstance(content_obj, list):
                                for item in content_obj:
                                    if isinstance(item, dict) and 'text' in item:
                                        content_parts.append(item['text'])
                                    else:
                                        content_parts.append(str(item))
                            else:
                                content_parts.append(str(content_obj))

                        content = '\n'.join(content_parts) if content_parts else ''
                        if content:
                            messages.append(ChatMessage('assistant', content))

        except Exception as e:
            print(f"Warning: Error parsing {path}: {e}")

        # Use filename as source ID for tracking (consistent with find_new_chats)
        # but preserve chat_id for metadata
        source_id = os.path.basename(path)

        return {
            'source_id': source_id,
            'messages': messages,
            'date': date,
            'tool': self.tool_name,
            'metadata': {'chat_id': chat_id} if chat_id else {}
        }
