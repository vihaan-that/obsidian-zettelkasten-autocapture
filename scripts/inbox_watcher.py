#!/usr/bin/env python3
"""
# ============================================================
# Research Log Inbox Watcher
# ============================================================
# Watches 00-Inbox/ for new .md files, classifies them,
# injects/updates YAML frontmatter, and moves them to the
# correct vault folder. Supports team daily logs, journals,
# experiments, and all original zettelkasten note types.
#
# 1. Install dependencies:
#      pip install watchdog google-genai
# 2. Export your Gemini API key (or skip for keyword mode):
#      export GEMINI_API_KEY="your-key-here"
# 3. Run directly or via scripts/start_watcher.sh:
#      python3 scripts/inbox_watcher.py
# 4. Drop any .md file into vault/00-Inbox/ and it will be
#    auto-tagged, filed, and you'll get one question.
# ============================================================
"""

import os
import sys
import json
import time
import shutil
import logging
import platform
import subprocess
import re
from datetime import datetime
from pathlib import Path

# ── Config ──────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
VAULT_PATH = Path(os.environ.get("VAULT_PATH", str(PROJECT_ROOT / "vault")))
INBOX_PATH = VAULT_PATH / "00-Inbox"
LOG_PATH   = VAULT_PATH / "_Scripts" / "watcher.log"

DEST_FOLDERS = {
    "daily-log":     VAULT_PATH / "50-Daily-Logs",
    "journal":       VAULT_PATH / "55-Journals",
    "experiment":    VAULT_PATH / "40-Experiments",
    "llm-chat":      VAULT_PATH / "10-LLM-Chats",
    "code-session":  VAULT_PATH / "20-Code-Sessions",
    "research":      VAULT_PATH / "30-Research",
    "general":       VAULT_PATH / "60-Permanent",
}

QUESTIONS = {
    "daily-log":    "Anything you'd add in hindsight? (Enter to skip)",
    "journal":      "One word for how today felt? (Enter to skip)",
    "experiment":   "What's the hypothesis status? (Enter to skip)",
    "llm-chat":     "What was the most useful thing from this chat? (Enter to skip)",
    "code-session": "What decision did you make in this session? (Enter to skip)",
    "research":     "What's your one takeaway from this? (Enter to skip)",
    "general":      "Any note worth keeping about this? (Enter to skip)",
}

# ── Logging ─────────────────────────────────────────────────
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ── OS detection ────────────────────────────────────────────
OS = platform.system()


# ── AI classification ────────────────────────────────────────
def classify_with_ai(content: str) -> dict:
    """
    Uses gemini-2.0-flash to extract type, summary, tags, and contributor.
    Returns dict with keys: type, summary, tags (list), contributor.
    Falls back to keyword classification if no API key or on failure.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return classify_with_keywords(content)

    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        prompt = (
            "Classify the following note from a team research log. "
            "Respond ONLY with raw JSON — no markdown fences, no preamble.\n"
            "Schema: {\"type\": \"<daily-log|journal|experiment|llm-chat|code-session|research|general>\","
            " \"summary\": \"<one line, max 12 words>\","
            " \"tags\": [\"<tag1>\", \"<tag2>\", \"<tag3>\"],"
            " \"contributor\": \"<name if found in note, else empty string>\"}\n\n"
            f"Note content:\n{content[:3000]}"
        )

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        raw = response.text.strip()
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        data = json.loads(raw)
        data["type"] = data.get("type", "general").lower()
        data["summary"] = data.get("summary", "")[:120]
        data["tags"] = data.get("tags", [])[:5]
        data["contributor"] = data.get("contributor", "")
        log.info(f"AI classified: {data}")
        return data
    except Exception as exc:
        log.warning(f"AI classification failed ({exc}), falling back to keywords")
        return classify_with_keywords(content)


def classify_with_keywords(content: str) -> dict:
    """Keyword-based fallback when no API key is set."""
    lower = content.lower()

    # Check for team log types first (they're more specific)
    if any(k in lower for k in ["type: daily-log", "daily log", "what i worked on", "pivots", "course correction"]):
        note_type = "daily-log"
    elif any(k in lower for k in ["type: journal", "stream of consciousness", "journal —"]):
        note_type = "journal"
    elif any(k in lower for k in ["hypothesis", "experiment", "observations", "result:"]):
        note_type = "experiment"
    elif any(k in lower for k in ["## session", "claude code", "code session", "git commit", "branch:"]):
        note_type = "code-session"
    elif any(k in lower for k in ["abstract", "paper", "source:", "doi:", "arxiv"]):
        note_type = "research"
    elif any(k in lower for k in ["chat", "prompt", "llm", "gpt", "claude", "gemini"]):
        note_type = "llm-chat"
    else:
        note_type = "general"

    # Try to extract contributor from frontmatter
    contributor = ""
    contributor_match = re.search(r'contributor:\s*"?([^"\n]+)"?', content)
    if contributor_match:
        contributor = contributor_match.group(1).strip()

    lines = [l.strip() for l in content.split("\n") if l.strip() and not l.startswith("---")]
    summary = lines[0][:120] if lines else "Untitled note"
    tags = [note_type]
    log.info(f"Keyword classified: type={note_type}, contributor={contributor}")
    return {"type": note_type, "summary": summary, "tags": tags, "contributor": contributor}


# ── Frontmatter ──────────────────────────────────────────────
def has_frontmatter(content: str) -> bool:
    return content.startswith("---")


def extract_frontmatter_field(content: str, field: str) -> str:
    """Extract a field value from existing YAML frontmatter."""
    match = re.search(rf'^{field}:\s*"?([^"\n]+)"?', content, re.MULTILINE)
    return match.group(1).strip() if match else ""


def inject_frontmatter(content: str, meta: dict) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    tags_yaml = "\n".join(f'  - "{t}"' for t in meta["tags"])
    contributor_line = f'contributor: "{meta["contributor"]}"\n' if meta.get("contributor") else ""

    fm = (
        f"---\n"
        f"type: {meta['type']}\n"
        f"date: {today}\n"
        f"{contributor_line}"
        f'summary: "{meta["summary"]}"\n'
        f"tags:\n{tags_yaml}\n"
        f"---\n\n"
    )
    if has_frontmatter(content):
        end = content.find("---", 3)
        if end != -1:
            content = content[end + 3:].lstrip("\n")
    return fm + content


def update_frontmatter_summary(content: str, summary: str) -> str:
    """Update just the summary field in existing frontmatter."""
    if has_frontmatter(content):
        return re.sub(
            r'(summary:\s*)"[^"]*"',
            f'\\1"{summary}"',
            content,
            count=1,
        )
    return content


# ── Desktop notification + question ─────────────────────────
def ask_user(question: str) -> str:
    """
    Shows a desktop notification then prompts for input via a dialog.
    Returns the user's typed response, or "" if skipped / unavailable.
    """
    try:
        if OS == "Linux":
            subprocess.run(
                ["notify-send", "Research Log", question],
                check=False, timeout=5,
            )
            if shutil.which("zenity"):
                result = subprocess.run(
                    ["zenity", "--entry",
                     "--title=Research Log Capture",
                     f"--text={question}",
                     "--width=500"],
                    capture_output=True, text=True, timeout=120,
                )
                return result.stdout.strip()

        elif OS == "Darwin":
            script = (
                f'set resp to text returned of '
                f'(display dialog "{question}" default answer "" '
                f'with title "Research Log Capture")'
                f'\nreturn resp'
            )
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=120,
            )
            return result.stdout.strip()

        elif OS == "Windows":
            try:
                from plyer import notification
                notification.notify(title="Research Log", message=question, timeout=5)
            except ImportError:
                pass
            return ""

    except Exception as exc:
        log.warning(f"Notification/dialog failed: {exc}")

    return ""


# ── Core processor ───────────────────────────────────────────
def process_file(path: Path) -> None:
    log.info(f"Processing: {path.name}")
    time.sleep(0.5)  # Let the file finish writing

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as exc:
        log.error(f"Could not read {path}: {exc}")
        return

    # If the file already has frontmatter with a type, respect it
    existing_type = extract_frontmatter_field(content, "type")
    existing_contributor = extract_frontmatter_field(content, "contributor")

    meta = classify_with_ai(content)

    # Prefer existing frontmatter values over AI classification
    if existing_type and existing_type in DEST_FOLDERS:
        meta["type"] = existing_type
    if existing_contributor:
        meta["contributor"] = existing_contributor

    # For notes that already have full frontmatter (from log.sh), just update summary
    if existing_type and has_frontmatter(content) and meta.get("summary"):
        content = update_frontmatter_summary(content, meta["summary"])
    else:
        content = inject_frontmatter(content, meta)

    dest_dir = DEST_FOLDERS.get(meta["type"], DEST_FOLDERS["general"])
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / path.name

    if dest_path.exists():
        stem = path.stem
        suffix = path.suffix
        dest_path = dest_dir / f"{stem}-{int(time.time())}{suffix}"

    path.write_text(content, encoding="utf-8")
    shutil.move(str(path), str(dest_path))
    log.info(f"Moved -> {dest_path}")

    question = QUESTIONS.get(meta["type"], QUESTIONS["general"])
    user_input = ask_user(question)
    if user_input:
        with open(dest_path, "a", encoding="utf-8") as f:
            f.write(f"\n## Reflection\n{user_input}\n")
        log.info(f"Appended user reflection to {dest_path.name}")


# ── Watchdog handler ─────────────────────────────────────────
try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    class InboxHandler(FileSystemEventHandler):
        def on_created(self, event):
            if event.is_directory:
                return
            p = Path(event.src_path)
            if p.suffix.lower() == ".md":
                try:
                    process_file(p)
                except Exception as exc:
                    log.error(f"Error processing {p.name}: {exc}", exc_info=True)

        def on_moved(self, event):
            if event.is_directory:
                return
            p = Path(event.dest_path)
            if p.suffix.lower() == ".md" and p.parent == INBOX_PATH:
                try:
                    process_file(p)
                except Exception as exc:
                    log.error(f"Error processing {p.name}: {exc}", exc_info=True)

except ImportError:
    log.error("watchdog not installed — run: pip install watchdog")
    sys.exit(1)


# ── Main ─────────────────────────────────────────────────────
def main():
    log.info(f"Inbox watcher starting. Watching: {INBOX_PATH}")
    INBOX_PATH.mkdir(parents=True, exist_ok=True)

    handler  = InboxHandler()
    observer = Observer()
    observer.schedule(handler, str(INBOX_PATH), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        log.info("Watcher stopped by user.")
    except Exception as exc:
        log.error(f"Watcher crashed: {exc}", exc_info=True)
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    main()
