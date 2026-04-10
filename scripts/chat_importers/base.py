# scripts/chat_importers/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
import os
import re

class ChatMessage:
    """Represents a single message in a chat."""
    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None):
        self.role = role
        self.content = content
        self.timestamp = timestamp

class ChatImporter(ABC):
    """Base class for chat importers."""

    def __init__(self, state=None):
        """Initialize importer with optional state tracker."""
        self.state = state

    @abstractmethod
    def find_new_chats(self) -> List[str]:
        """
        Return list of paths to chat files that haven't been imported yet.

        Returns:
            List of full file paths to unimported chat files.
        """
        pass

    @abstractmethod
    def parse_chat(self, path: str) -> Dict:
        """
        Parse a chat file and extract messages and metadata.

        Returns:
            {
                'source_id': 'unique-id-in-source-tool',
                'messages': [ChatMessage, ...],
                'date': datetime object,
                'tool': 'claude-cli' or 'copilot',
                'metadata': { extra fields }
            }
        """
        pass

    def to_markdown(self, chat: Dict, contributor: str = 'unknown') -> str:
        """
        Convert parsed chat to markdown with frontmatter.

        Returns:
            Markdown string ready to write to file.
        """
        messages = chat['messages']
        date = chat['date'].strftime('%Y-%m-%d')
        source_id = chat['source_id']
        tool = chat['tool']

        # Build summary from first message and response
        summary_parts = []
        for msg in messages[:5]:
            if msg.role == 'user':
                text = msg.content.split('\n')[0][:100]
                summary_parts.append(text)
                break
        summary = summary_parts[0] if summary_parts else 'Chat conversation'

        # Frontmatter
        frontmatter = f"""---
type: llm-chat
date: {date}
contributor: "{contributor}"
tool: "{tool}"
source_id: "{source_id}"
summary: "{self._escape_yaml(summary)}"
tags:
  - "{tool}"
---"""

        # Build message exchange
        body = f"\n\n## Chat with {self._format_tool_name(tool)}\n\n"
        for msg in messages:
            role_title = msg.role.capitalize()
            body += f"**{role_title}:** {msg.content}\n\n"

        return frontmatter + body

    def mark_imported(self, source_id: str):
        """Mark a chat as imported (requires state tracker)."""
        if self.state:
            self.state.mark_imported(self.tool_name, source_id)

    def _escape_yaml(self, text: str) -> str:
        """Escape text for YAML frontmatter."""
        # Remove newlines and limit length
        text = text.replace('\n', ' ').replace('"', '\\"')
        return text[:120]

    def _format_tool_name(self, tool: str) -> str:
        """Format tool name for display."""
        return {'claude-cli': 'Claude CLI', 'copilot': 'Copilot'}.get(tool, tool)

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Return the tool identifier ('claude-cli', 'copilot', etc.)."""
        pass
