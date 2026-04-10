# Research Log Web Clipper - Setup & Usage

## Installation

### Chrome / Edge

1. **Get the code:**
   ```bash
   cd research-log/extension
   ```

2. **Load extension:**
   - Open Chrome and go to `chrome://extensions/`
   - Enable **Developer mode** (toggle in top right)
   - Click **Load unpacked**
   - Select the `extension/` folder

3. **Configure settings:**
   - Click the extension icon (puzzle piece) in the toolbar
   - Click the **⚙️ gear icon** or right-click → Options
   - Set "Download Folder" to your vault's inbox folder
     - Example: `/Users/alice/Documents/research-log/vault/00-Inbox`
   - (Optional) Set your contributor name
   - Click **Save Settings**

## Usage

### Clipping a Page or Text

1. **Browse** to any web page
2. **(Optional)** Select text by highlighting it
3. **Click** the extension icon → popup appears
4. **Review:**
   - Page URL and title are pre-filled
   - Selected text preview shows (if any)
   - You can add a screenshot, notes, and tags
5. **Click "Save to Research Log"**
6. File is saved to your inbox folder and the organizer will pick it up

### What Gets Saved

Each clip is saved as a markdown file with:

```markdown
---
type: web-clip
date: 2026-04-10
contributor: "alice"
url: "https://example.com/article"
summary: "Article title or first 120 chars of selection"
tags:
  - "web-clip"
  - (any tags you added)
---

# Article Title

**Source:** [URL](URL)

## Selected Text

(Your selected text, if any)

## Notes

(Your notes, if any)

## Screenshot

![Screenshot](screenshot.png)

(If you toggled screenshot)
```

### Tips

- **Don't select anything** — clips the whole page content for reference
- **Select specific text** — captures just what matters
- **Add tags** — comma-separated, helps filtering in Obsidian
- **Include screenshot** — useful for layouts, designs, visual references
- **Notes** — explain *why* you're saving this (context for future-you)

### Troubleshooting

**Issue:** "Download folder not configured"
- **Solution:** Open extension options and set your inbox folder path

**Issue:** Files don't appear in Obsidian
- **Solution:** Check that the path you configured is correct and accessible
- Run `ls vault/00-Inbox/` to verify files exist
- If using organizer, wait for the next run (or run manually: `python3 scripts/organizer.py`)

**Issue:** Screenshots are huge
- **Solution:** Chrome captures at full resolution. Consider:
  - Cropping in the page before clipping
  - Using browser zoom to reduce capture size
  - Compression option (TBD)

## Advanced

### Changing the Download Folder

1. Open extension options (`chrome://extensions/` → gear icon)
2. Update the "Download Folder" path
3. Save

### Using with Organizer

If you have the organizer running (`setup-organizer.sh`), it will automatically:
1. Pick up files from `00-Inbox/`
2. Classify them (keep type=web-clip)
3. File to `15-Web-Clips/` folder
4. Add to the daily digest

To run organizer manually:
```bash
python3 scripts/organizer.py
```

## Development

See `extension/README.md` for extension code structure and development notes.
