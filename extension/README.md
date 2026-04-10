# Research Log Web Clipper - Chrome Extension

A lightweight browser extension for saving web content (text, links, screenshots) to your Research Log vault.

## Installation

1. Clone/download the research-log repository
2. Open Chrome and go to `chrome://extensions/`
3. Enable "Developer mode" (toggle in top right)
4. Click "Load unpacked" and select the `extension/` folder

## Configuration

1. Click the extension icon in Chrome toolbar
2. Click the gear icon (or right-click → Options)
3. Set "Download Folder" to the full path of your vault's `00-Inbox/` folder
   - Example: `/Users/alice/Documents/research-log/vault/00-Inbox`
4. (Optional) Set your contributor name
5. Click "Save Settings"

## Usage

1. Browse the web, select text (or don't), click the extension icon
2. Popup appears with page URL, title, and selected text preview
3. (Optional) Toggle "Include screenshot"
4. (Optional) Add notes and tags
5. Click "Save to Research Log"
6. File is saved to your configured inbox folder
7. The existing watcher/organizer will pick it up and file it

## Notes

- Files are saved as markdown with YAML frontmatter
- Screenshots are embedded as PNG images
- Tags are saved in the frontmatter for filtering
- Contributor name is tracked for attribution

## Limitations

- Currently Chrome only (Manifest V3)
- Requires manual folder configuration (browser permissions limit auto-detection)
- Screenshots may be large; consider enabling compression if needed
