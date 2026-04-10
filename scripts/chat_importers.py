#!/usr/bin/env python3
"""
Chat importers daemon.

Periodically scans for new chats from Claude CLI, Copilot, and other tools,
imports them to the vault inbox, and marks them as imported to avoid duplicates.

Usage:
    python3 scripts/chat_importers.py
    python3 scripts/chat_importers.py --dry-run
    python3 scripts/chat_importers.py --no-push
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import getpass

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from chat_importers.state import ImportState
from chat_importers.base import ChatImporter

def get_vault_path():
    """Get vault path from env or default."""
    env_path = os.getenv('VAULT_PATH')
    if env_path:
        return env_path

    # Default: vault/ in repo root
    repo_root = Path(__file__).parent.parent
    return str(repo_root / 'vault')

def get_contributor():
    """Get contributor name from env, git config, or system user."""
    # Check env
    if os.getenv('LOG_CONTRIBUTOR'):
        return os.getenv('LOG_CONTRIBUTOR')

    # Check git config
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'config', 'user.name'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass

    # Fall back to system user
    return getpass.getuser()

def run_importers(dry_run=False, no_push=False):
    """Run all available importers."""
    vault_path = get_vault_path()
    inbox_path = os.path.join(vault_path, '00-Inbox')
    contributor = get_contributor()

    # Ensure inbox exists
    Path(inbox_path).mkdir(parents=True, exist_ok=True)

    # Initialize state tracker
    state = ImportState()

    # Import dynamically to avoid hard dependencies
    importers = []
    try:
        from chat_importers.claude_cli import ClaudeCliImporter
        importers.append(ClaudeCliImporter(state))
    except Exception as e:
        print(f"Warning: Could not load Claude CLI importer: {e}")

    try:
        from chat_importers.copilot import CopilotImporter
        importers.append(CopilotImporter(state))
    except Exception as e:
        print(f"Warning: Could not load Copilot importer: {e}")

    if not importers:
        print("No importers available")
        return

    total_imported = 0

    for importer in importers:
        print(f"\n=== {importer.tool_name} ===")
        try:
            chat_paths = importer.find_new_chats()
            print(f"Found {len(chat_paths)} new chat(s)")

            for chat_path in chat_paths:
                try:
                    # Parse chat
                    chat = importer.parse_chat(chat_path)

                    # Convert to markdown
                    markdown = importer.to_markdown(chat, contributor)

                    # Generate filename
                    date_str = chat['date'].strftime('%Y-%m-%d')
                    source_id = chat['source_id'][:30]  # Shorten for filename
                    filename = f"llm-chat-{date_str}-{source_id}.md"
                    filepath = os.path.join(inbox_path, filename)

                    if dry_run:
                        print(f"  [DRY RUN] Would save: {filename}")
                    else:
                        # Write file
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(markdown)

                        # Mark imported
                        importer.mark_imported(chat['source_id'])
                        print(f"  ✓ Imported: {filename}")
                        total_imported += 1

                except Exception as e:
                    print(f"  ✗ Error importing chat: {e}")

        except Exception as e:
            print(f"Error running {importer.tool_name} importer: {e}")

    print(f"\n=== Summary ===")
    print(f"Total imported: {total_imported}")

    if not dry_run and not no_push and total_imported > 0:
        print("\nNote: Run 'rlog-sync' to commit and push new entries.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Import chats from Claude CLI, Copilot, and other tools'
    )
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview what would be imported without making changes')
    parser.add_argument('--no-push', action='store_true',
                        help='Import but do not auto-push')

    args = parser.parse_args()

    try:
        run_importers(dry_run=args.dry_run, no_push=args.no_push)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
