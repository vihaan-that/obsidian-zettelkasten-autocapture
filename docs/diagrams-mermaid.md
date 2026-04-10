# Architecture Diagrams (Mermaid Format)

These diagrams show the chat importers and web clipper architecture in Mermaid format.

## 1. System Flow: End-to-End Pipeline

```mermaid
graph TD
    A["📝 Capture Sources"] --> B["vault/00-Inbox/"]
    
    A1["💻 Team CLI<br/>log.sh"] --> A
    A2["🤖 Claude Code<br/>Session Hook"] --> A
    A3["🔗 Git Commit<br/>Hook"] --> A
    A4["🌐 Browser Ext v1<br/>Claude Chats"] --> A
    A5["🖼️ Browser Ext v2<br/>Web Clipper<br/>(NEW)"] --> A
    A6["📥 Chat Importers<br/>Daemon (NEW)"] --> A
    
    B --> C{"Watcher or<br/>Organizer?"}
    
    C -->|Real-time| D["inbox_watcher.py"]
    C -->|Nightly| E["organizer.py<br/>Admin PC"]
    
    D --> F["Classify + Frontmatter"]
    E --> F
    
    F --> G["Move to<br/>Destination Folder"]
    
    G --> H["📚 Organized Vault"]
    H1["10-LLM-Chats/"] --> H
    H2["15-Web-Clips/"] --> H
    H3["20-Code-Sessions/"] --> H
    H4["30-Research/"] --> H
    H5["40-Experiments/"] --> H
    H6["50-Daily-Logs/"] --> H
    H7["55-Journals/"] --> H
    H8["60-Permanent/"] --> H
    
    H --> I["🧠 Obsidian Vault<br/>Dataview Dashboard"]
    
    I --> J["👥 Team browsing<br/>🤖 LLM queries"]
    
    style A5 fill:#e1f5ff
    style A6 fill:#e1f5ff
    style H2 fill:#e1f5ff
```

## 2. Browser Extension Architecture

```mermaid
graph LR
    A["🌐 Web Page<br/>User Selected Text"] --> B["Content Script<br/>content.js"]
    
    B -->|getSelectedText| C["Popup UI<br/>popup.html/js"]
    
    C -->|Page URL<br/>Title<br/>Text Preview<br/>Options| D["Service Worker<br/>background.js"]
    
    D -->|captureVisibleTab| E["Screenshot<br/>PNG Data"]
    
    D -->|downloads API| F["vault/00-Inbox/<br/>markdown file"]
    
    C -->|Configure| G["Settings<br/>options.html/js"]
    
    G -->|Download Path<br/>Contributor| H["chrome.storage.sync"]
    
    style B fill:#fff3e0
    style C fill:#fff3e0
    style D fill:#fff3e0
    style G fill:#fff3e0
```

## 3. Chat Importers: Classes & Flow

```mermaid
graph TD
    A["chat_importers.py<br/>Main Coordinator"]
    
    A -->|Dynamic Import| B["ClaudeCliImporter"]
    A -->|Dynamic Import| C["CopilotImporter"]
    A -->|Dynamic Import| D["FutureImporter<br/>(Framework)"]
    
    B --> B1["_get_chat_dir()"]
    B1 --> B2["~/.claude/chats/"]
    B --> B3["find_new_chats()"]
    B3 --> B4["Glob *.jsonl<br/>Filter via state"]
    B --> B5["parse_chat()"]
    B5 --> B6["Read JSONL<br/>Extract messages"]
    B --> B7["to_markdown()<br/>from base"]
    
    C --> C1["_get_chat_dir()"]
    C1 --> C2["Platform-specific<br/>Windows/macOS/Linux"]
    C --> C3["find_new_chats()"]
    C3 --> C4["Glob *.json, *.db<br/>Filter via state"]
    C --> C5["parse_chat()"]
    C5 --> C5A["_parse_json_chat()"]
    C5 --> C5B["_parse_db_chat()"]
    
    B7 --> E["ImportState<br/>SQLite Tracking"]
    B7 --> F["Write to<br/>00-Inbox/"]
    
    C7["to_markdown()"] --> E
    C7 --> F
    
    D --> D1["Subclass ChatImporter"]
    D1 --> D2["Implement find_new_chats()"]
    D1 --> D3["Implement parse_chat()"]
    
    E -->|Mark Imported| G["import_state.db<br/>(tool, source_id)"]
    
    F --> H["Organizer picks up"]
    
    style A fill:#f3e5f5
    style B fill:#f3e5f5
    style C fill:#f3e5f5
    style D fill:#f3e5f5
    style E fill:#f3e5f5
    style G fill:#e0f2f1
```

## 4. Data Flow: Single Note Lifecycle

```mermaid
graph TD
    A["Created by User<br/>via Capture Source"]
    
    A -->|Team logs via CLI| A1["log.sh"]
    A -->|Claude Code ends| A2["Hook captures"]
    A -->|Git commit made| A3["Post-commit hook"]
    A -->|Web page clipped| A4["Browser Extension"]
    A -->|Chat imported| A5["Chat Importer"]
    
    A1 --> B["Generate Markdown<br/>+ YAML Frontmatter"]
    A2 --> B
    A3 --> B
    A4 --> B
    A5 --> B
    
    B --> C["Write to<br/>vault/00-Inbox/"]
    
    C --> D{"File detected<br/>by Watcher<br/>or next cron?"}
    
    D -->|Real-time| E["inbox_watcher.py<br/>Parses + Classifies"]
    D -->|Nightly 9 PM| F["organizer.py<br/>Parses + Classifies"]
    
    E --> G["Extract type from<br/>frontmatter or<br/>LLM classification"]
    F --> G
    
    G --> H["Update frontmatter<br/>with summary,<br/>tags, type"]
    
    H --> I{"Determine<br/>destination<br/>folder"}
    
    I -->|web-clip| I1["15-Web-Clips/"]
    I -->|llm-chat| I2["10-LLM-Chats/"]
    I -->|code-session| I3["20-Code-Sessions/"]
    I -->|experiment| I4["40-Experiments/"]
    I -->|daily-log| I5["50-Daily-Logs/"]
    I -->|journal| I6["55-Journals/"]
    I -->|research| I7["30-Research/"]
    I -->|general| I8["60-Permanent/"]
    
    I1 --> J["File stored in vault"]
    I2 --> J
    I3 --> J
    I4 --> J
    I5 --> J
    I6 --> J
    I7 --> J
    I8 --> J
    
    J --> K["Available in<br/>Obsidian"]
    
    K --> L["Humans browse &<br/>search via Dataview"]
    K --> M["LLM agents<br/>query & summarize"]
    
    style C fill:#fff9c4
    style G fill:#c8e6c9
    style I fill:#bbdefb
    style K fill:#f8bbd0
```

## 5. State Tracking: Duplicate Prevention

```mermaid
graph LR
    A["Importer runs"] --> B["find_new_chats()"]
    
    B --> C["Glob storage<br/>for all chats"]
    
    C --> D{"For each chat:<br/>is_imported?"}
    
    D -->|✓ Already in DB| E["SKIP<br/>Don't re-import"]
    D -->|✗ New chat| F["Include in<br/>new_chats list"]
    
    F --> G["parse_chat()"]
    
    G --> H["Write to<br/>00-Inbox/"]
    
    H --> I["mark_imported()"]
    
    I --> J["INSERT INTO<br/>import_state.db"]
    
    J --> K["(tool, source_id,<br/>imported_at)"]
    
    K --> L["Next run:<br/>Query skips this<br/>via is_imported()"]
    
    style E fill:#ffcdd2
    style F fill:#c8e6c9
    style J fill:#e1f5fe
```

## 6. Setup & Cron Integration

```mermaid
graph TD
    A["bash setup-organizer.sh<br/>--enable-importers<br/>--importer-interval 2h"]
    
    A --> B["Parse arguments"]
    
    B -->|Standard| B1["Install organizer cron"]
    B1 -->|Schedule| B1A["0 21 * * *<br/>9 PM daily"]
    B1A --> B1B["python3 organizer.py"]
    
    B -->|--enable-importers| B2["Install importers cron"]
    B2 -->|Interval conversion| B2A["2h → 0 */2 * * *<br/>every 2 hours"]
    B2A --> B2B["python3 chat_importers.py"]
    
    B2B --> C["Dynamically loads<br/>available importers"]
    
    C --> C1["ClaudeCliImporter<br/>if ~/.claude/ exists"]
    C --> C2["CopilotImporter<br/>if copilot path exists"]
    
    C1 --> D["scan → parse →<br/>write → mark"]
    C2 --> D
    
    D --> E["vault/00-Inbox/<br/>new chats"]
    
    E --> F["Next organizer run<br/>picks them up"]
    
    F --> G["Classify & file"]
    
    style A fill:#ffe0b2
    style B1 fill:#c8e6c9
    style B2 fill:#c8e6c9
    style D fill:#bbdefb
    style G fill:#f8bbd0
```

## 7. Chat Tool Storage Map

```mermaid
graph TD
    A["Platform"] --> B["OS Detection"]
    
    B -->|Windows| B1["APPDATA / LOCALAPPDATA<br/>env vars"]
    B1 --> B1A["%APPDATA%<br/>\\Microsoft\\Copilot\\"]
    
    B -->|macOS| B2["Home directory<br/>Library paths"]
    B2 --> B2A["~/Library/<br/>Application Support/"]
    
    B -->|Linux| B3["Standard XDG<br/>user dirs"]
    B3 --> B3A["~/.config/<br/>~/.local/share/"]
    
    C["Tool"] --> D["Claude CLI"]
    C --> E["Copilot"]
    
    D --> D1["Location"]
    D1 --> D2["~/.claude/chats/"]
    D2 --> D3["Format: JSONL<br/>Files: *.jsonl"]
    
    E --> E1["Location"]
    E1 --> E2A["Windows:<br/>%APPDATA%\\Microsoft\\Copilot"]
    E1 --> E2B["macOS:<br/>~/Library/.../Copilot"]
    E1 --> E2C["Linux:<br/>~/.config/copilot/"]
    E2A --> E3["Format: JSON + SQLite<br/>Files: *.json, *.db"]
    E2B --> E3
    E2C --> E3
```

## 8. Error Handling & Robustness

```mermaid
graph TD
    A["Start Importer"] --> B["try:"]
    
    B --> C["Connect to storage"]
    
    C -->|Not found| C1["❌ return empty list<br/>No chats available"]
    C -->|Found| D["Scan for new files"]
    
    D --> E["For each file"]
    
    E --> F{"parse_chat()?"}
    
    F -->|JSON valid| F1["✓ Extract messages"]
    F -->|JSON invalid| F2["❌ Skip file<br/>except Exception"]
    F -->|Copilot DB empty| F3["❌ Return empty<br/>messages"]
    F -->|Copilot parse fails| F4["❌ Return empty<br/>messages"]
    
    F1 --> G["Write to inbox"]
    F2 --> H["Log warning"]
    F3 --> H
    F4 --> H
    
    G --> I["mark_imported()"]
    
    I -->|SQLite locked| I1["Retry with<br/>30s timeout"]
    I1 --> I2["✓ Success"]
    
    I2 --> J["Done"]
    
    H --> K["Continue to<br/>next file"]
    
    style C1 fill:#ffcdd2
    style F2 fill:#ffcdd2
    style F3 fill:#ffcdd2
    style F4 fill:#ffcdd2
    style F1 fill:#c8e6c9
    style I2 fill:#c8e6c9
```

## 9. Extensibility: Adding ChatGPT

```mermaid
graph LR
    A["Create New<br/>Importer"] --> A1["scripts/chat_importers/<br/>chatgpt.py"]
    
    A1 --> B["class ChatGPTImporter"]
    
    B -->|Extends| B1["ChatImporter"]
    
    B --> B2["@property<br/>tool_name"]
    B2 -->|returns| B2A["'chatgpt'"]
    
    B --> B3["find_new_chats()"]
    B3 -->|scan| B3A["~/.chatgpt/chats/"]
    B3 -->|return| B3B["List unimported"]
    
    B --> B4["parse_chat()"]
    B4 -->|read| B4A["JSON/SQLite"]
    B4 -->|return| B4B["Dict with messages"]
    
    B --> B5["(Inherited)"]
    B5 -->|uses| B5A["to_markdown()"]
    B5 -->|uses| B5B["mark_imported()"]
    
    A1 --> C["Register in"]
    C -->|chat_importers.py| C1["try/except import"]
    
    C1 --> D["Runs automatically<br/>on cron"]
    
    D --> E["Users don't<br/>need to change<br/>anything"]
    
    style A1 fill:#e1bee7
    style B fill:#e1bee7
    style B1 fill:#c8e6c9
    style D fill:#f8bbd0
```

---

## How to View These Diagrams

1. **In GitHub/Markdown viewer:** Diagrams render directly (requires Mermaid support)
2. **Live preview:** Use https://mermaid.live/ and paste the code
3. **Export to PNG:** Use the Mermaid CLI or online export
4. **In Obsidian:** Install the Mermaid plugin to view inline

