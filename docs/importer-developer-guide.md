# Chat Importers - Developer Guide

## Architecture

The importer system is designed to be extensible. Each tool gets its own importer class that inherits from `ChatImporter`.

```
chat_importers/
├── base.py         ← Abstract ChatImporter class
├── state.py        ← SQLite duplicate tracking
├── claude_cli.py   ← Claude CLI implementation
├── copilot.py      ← Copilot implementation
└── (new_tool).py   ← Your importer here
```

## Adding a New Tool

### 1. Create the importer class

Create `scripts/chat_importers/new_tool.py`:

```python
from .base import ChatImporter, ChatMessage
from datetime import datetime
from pathlib import Path

class NewToolImporter(ChatImporter):
    """Import chats from NewTool."""
    
    @property
    def tool_name(self) -> str:
        return 'new-tool'
    
    def find_new_chats(self) -> list:
        """Find unimported chats from NewTool."""
        # 1. Detect storage location
        # 2. List all chat files/IDs
        # 3. Filter out already-imported ones using self.state
        # 4. Return list of paths
        pass
    
    def parse_chat(self, path: str) -> dict:
        """Parse a chat file and return standardized dict."""
        # 1. Read the file
        # 2. Extract messages
        # 3. Extract metadata (date, etc.)
        # 4. Return:
        # {
        #     'source_id': 'unique-id',
        #     'messages': [ChatMessage(...), ...],
        #     'date': datetime,
        #     'tool': 'new-tool',
        #     'metadata': { ... }
        # }
        pass
```

### 2. Implement key methods

#### `find_new_chats()` → List[str]

Returns paths to chat files that haven't been imported.

Example:
```python
def find_new_chats(self) -> list:
    storage_path = self._get_storage_path()
    if not storage_path:
        return []
    
    all_chats = glob.glob(os.path.join(storage_path, '*.json'))
    
    if self.state:
        new_chats = [
            f for f in all_chats
            if not self.state.is_imported(self.tool_name, os.path.basename(f))
        ]
        return new_chats
    
    return all_chats
```

#### `parse_chat(path)` → dict

Parses a chat file and returns standardized format.

Example:
```python
def parse_chat(self, path: str) -> dict:
    with open(path) as f:
        data = json.load(f)
    
    messages = [
        ChatMessage(
            role=msg['role'],
            content=msg['content'],
            timestamp=datetime.fromisoformat(msg['timestamp'])
        )
        for msg in data['messages']
    ]
    
    return {
        'source_id': os.path.basename(path),
        'messages': messages,
        'date': datetime.fromisoformat(data['created_at']),
        'tool': self.tool_name,
        'metadata': {}
    }
```

### 3. Register the importer

In `scripts/chat_importers.py`, add to `run_importers()`:

```python
try:
    from chat_importers.new_tool import NewToolImporter
    importers.append(NewToolImporter(state))
except Exception as e:
    print(f"Warning: Could not load NewTool importer: {e}")
```

### 4. Test it

Create a test with mock data:

```python
# scripts/test_new_tool.py
import tempfile
from chat_importers.new_tool import NewToolImporter
from chat_importers.state import ImportState

with tempfile.TemporaryDirectory() as tmpdir:
    # Create mock chat file
    mock_file = os.path.join(tmpdir, 'chat_123.json')
    # ... write mock data ...
    
    # Create importer with mock state
    state = ImportState(os.path.join(tmpdir, 'state.db'))
    importer = NewToolImporter(state)
    importer.storage_path = tmpdir  # Override for testing
    
    # Test find_new_chats
    chats = importer.find_new_chats()
    assert len(chats) == 1
    
    # Test parse_chat
    chat = importer.parse_chat(chats[0])
    assert chat['tool'] == 'new-tool'
    assert len(chat['messages']) > 0
    
    # Test markdown generation
    markdown = importer.to_markdown(chat, 'test_user')
    assert 'tool: "new-tool"' in markdown
    
    print("✓ All tests passed")
```

Run:
```bash
python3 scripts/test_new_tool.py
```

### 5. Submit

Once tested, commit your importer:
```bash
git add scripts/chat_importers/new_tool.py
git commit -m "feat: add NewTool chat importer

Imports chats from NewTool storage location."
```

## API Reference

### ChatImporter base class

**Properties:**
- `tool_name` (str, abstract): Identifier like 'claude-cli', 'copilot', 'chatgpt'

**Methods:**
- `find_new_chats()` → List[str] (abstract)
  - Return paths to unimported chats
  
- `parse_chat(path: str)` → dict (abstract)
  - Parse file and return standardized chat dict
  
- `to_markdown(chat: dict, contributor: str)` → str
  - Convert chat dict to markdown (inherited, no override needed)
  
- `mark_imported(source_id: str)`
  - Mark a chat as imported in the state tracker

### ChatMessage

```python
ChatMessage(
    role: str,      # 'user', 'assistant', etc.
    content: str,   # The message text
    timestamp: datetime = None
)
```

### ImportState

```python
state = ImportState(db_path='/path/to/db.sqlite')

# Check if imported
is_imported = state.is_imported(tool='claude-cli', source_id='chat_123')

# Mark imported
state.mark_imported(tool='claude-cli', source_id='chat_123')

# List all imported
chats = state.list_imported()  # or state.list_imported('claude-cli')
```

## Best Practices

1. **Use `self.tool_name`** for consistency (e.g., in frontmatter generation)
2. **Handle missing storage gracefully** — return empty list if path doesn't exist
3. **Use `self.state`** to track imports — never import twice
4. **Preserve metadata** — extract dates, any unique IDs, author info
5. **Test with mocks** — don't rely on real tools being installed
6. **Document storage locations** — including all OS variants
7. **Graceful fallbacks** — if format varies, try multiple parsers

## Examples

See `scripts/chat_importers/claude_cli.py` and `copilot.py` for real implementations.
