#!/usr/bin/env python3
"""
# ============================================================
# Research Log Organizer — runs every evening on the admin PC
# ============================================================
# What it does:
#   1. git pull (get all team entries)
#   2. Find unprocessed notes (in 00-Inbox or missing summary)
#   3. LLM-classify, summarize, and tag each note
#   4. Move notes from 00-Inbox to the correct folder
#   5. Generate a daily digest of all today's entries
#   6. git commit + push (organized notes back to the repo)
#
# Usage:
#   python3 scripts/organizer.py                    # run once
#   python3 scripts/organizer.py --dry-run          # preview without changes
#   python3 scripts/organizer.py --no-push          # organize but don't push
#   python3 scripts/organizer.py --provider gemini  # use gemini instead of anthropic
#
# Environment:
#   ANTHROPIC_API_KEY  — required (default provider)
#   GEMINI_API_KEY     — required if --provider gemini
#   VAULT_PATH         — override vault location
# ============================================================
"""

import os
import sys
import re
import json
import time
import shutil
import logging
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# ── Paths ───────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
VAULT_PATH = Path(os.environ.get("VAULT_PATH", str(PROJECT_ROOT / "vault")))
INBOX_PATH = VAULT_PATH / "00-Inbox"
DIGEST_PATH = VAULT_PATH / "50-Daily-Logs"

DEST_FOLDERS = {
    "daily-log":     VAULT_PATH / "50-Daily-Logs",
    "journal":       VAULT_PATH / "55-Journals",
    "experiment":    VAULT_PATH / "40-Experiments",
    "llm-chat":      VAULT_PATH / "10-LLM-Chats",
    "code-session":  VAULT_PATH / "20-Code-Sessions",
    "research":      VAULT_PATH / "30-Research",
    "web-clip":      VAULT_PATH / "15-Web-Clips",
    "general":       VAULT_PATH / "60-Permanent",
}

# ── Logging ─────────────────────────────────────────────────
LOG_PATH = VAULT_PATH / "_Scripts" / "organizer.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("organizer")


# ── Git helpers ─────────────────────────────────────────────
def git(*args):
    result = subprocess.run(
        ["git", "-C", str(PROJECT_ROOT)] + list(args),
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0 and result.stderr:
        log.warning(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.strip()


def git_pull():
    log.info("Pulling latest from remote...")
    out = git("pull", "--rebase", "--autostash")
    log.info(f"  {out}")


def git_commit_and_push(message: str, push: bool = True):
    git("add", "vault/")
    status = git("status", "--porcelain", "--", "vault/")
    if not status:
        log.info("No changes to commit.")
        return False
    git("commit", "-m", message)
    log.info(f"Committed: {message}")
    if push:
        out = git("push")
        log.info(f"Pushed. {out}")
    return True


# ── YAML frontmatter helpers ────────────────────────────────
FM_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


def parse_frontmatter(content: str) -> dict:
    """Extract frontmatter fields as a dict (simple key: value parser)."""
    match = FM_RE.match(content)
    if not match:
        return {}
    fm = {}
    for line in match.group(1).split("\n"):
        if ":" in line and not line.strip().startswith("-"):
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm


def get_body(content: str) -> str:
    """Return content after frontmatter."""
    match = FM_RE.match(content)
    if match:
        return content[match.end():].strip()
    return content.strip()


def rebuild_frontmatter(meta: dict, body: str) -> str:
    """Rebuild full note from meta dict and body."""
    lines = ["---"]
    for key, val in meta.items():
        if key == "tags" and isinstance(val, list):
            lines.append("tags:")
            for t in val:
                lines.append(f'  - "{t}"')
        elif isinstance(val, str) and (" " in val or not val):
            lines.append(f'{key}: "{val}"')
        else:
            lines.append(f"{key}: {val}")
    lines.append("---")
    lines.append("")
    lines.append(body)
    return "\n".join(lines) + "\n"


# ── LLM providers ──────────────────────────────────────────
def llm_classify_anthropic(content: str) -> dict:
    """Classify using Claude via the Anthropic API."""
    import anthropic

    client = anthropic.Anthropic()

    prompt = (
        "You are a research log organizer. Classify this note and return ONLY raw JSON.\n\n"
        "Schema:\n"
        '{"type": "<daily-log|journal|experiment|llm-chat|code-session|research|web-clip|general>",\n'
        ' "summary": "<one line, max 15 words>",\n'
        ' "tags": ["<tag1>", "<tag2>", "<tag3>"],\n'
        ' "contributor": "<name if found, else empty string>"}\n\n'
        "Rules:\n"
        "- summary should capture the KEY insight or decision, not just 'daily log for april'\n"
        "- tags should be topical (what the work is about), not structural\n"
        "- if the note already has good frontmatter, preserve its type and contributor\n\n"
        f"Note:\n{content[:4000]}"
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


def llm_classify_gemini(content: str) -> dict:
    """Classify using Gemini."""
    from google import genai

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    prompt = (
        "You are a research log organizer. Classify this note and return ONLY raw JSON.\n\n"
        "Schema:\n"
        '{"type": "<daily-log|journal|experiment|llm-chat|code-session|research|web-clip|general>",\n'
        ' "summary": "<one line, max 15 words>",\n'
        ' "tags": ["<tag1>", "<tag2>", "<tag3>"],\n'
        ' "contributor": "<name if found, else empty string>"}\n\n'
        "Rules:\n"
        "- summary should capture the KEY insight or decision, not just 'daily log for april'\n"
        "- tags should be topical (what the work is about), not structural\n"
        "- if the note already has good frontmatter, preserve its type and contributor\n\n"
        f"Note:\n{content[:4000]}"
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    raw = response.text.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


def llm_digest_anthropic(entries: list[dict]) -> str:
    """Generate a daily digest from today's entries."""
    import anthropic

    client = anthropic.Anthropic()

    entries_text = ""
    for e in entries:
        entries_text += f"\n---\nContributor: {e['contributor']}\nType: {e['type']}\nSummary: {e['summary']}\n"
        entries_text += f"Content preview:\n{e['body'][:1000]}\n"

    prompt = (
        "You are a research team lead writing a daily digest.\n"
        "Given today's log entries from the team, write a concise daily digest in markdown.\n\n"
        "Structure:\n"
        "## Key Highlights\n"
        "- 3-5 bullet points of the most important things across all entries\n\n"
        "## By Contributor\n"
        "For each person: 1-2 sentence summary of what they worked on\n\n"
        "## Open Questions & Blockers\n"
        "- Any blockers or questions that need attention\n\n"
        "## Decisions Made\n"
        "- Any decisions or pivots noted today\n\n"
        "Be concise. No fluff. If a section has nothing, omit it.\n\n"
        f"Today's entries ({len(entries)} total):\n{entries_text}"
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def llm_digest_gemini(entries: list[dict]) -> str:
    """Generate a daily digest using Gemini."""
    from google import genai

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    entries_text = ""
    for e in entries:
        entries_text += f"\n---\nContributor: {e['contributor']}\nType: {e['type']}\nSummary: {e['summary']}\n"
        entries_text += f"Content preview:\n{e['body'][:1000]}\n"

    prompt = (
        "You are a research team lead writing a daily digest.\n"
        "Given today's log entries from the team, write a concise daily digest in markdown.\n\n"
        "Structure:\n"
        "## Key Highlights\n"
        "- 3-5 bullet points of the most important things across all entries\n\n"
        "## By Contributor\n"
        "For each person: 1-2 sentence summary of what they worked on\n\n"
        "## Open Questions & Blockers\n"
        "- Any blockers or questions that need attention\n\n"
        "## Decisions Made\n"
        "- Any decisions or pivots noted today\n\n"
        "Be concise. No fluff. If a section has nothing, omit it.\n\n"
        f"Today's entries ({len(entries)} total):\n{entries_text}"
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    return response.text.strip()


# ── Core processing ─────────────────────────────────────────
def find_unprocessed_notes() -> list[Path]:
    """Find notes in 00-Inbox that need processing."""
    notes = []
    if INBOX_PATH.exists():
        for f in INBOX_PATH.glob("*.md"):
            notes.append(f)
    return notes


def find_incomplete_notes() -> list[Path]:
    """Find notes in destination folders that have empty summaries."""
    notes = []
    for folder in DEST_FOLDERS.values():
        if not folder.exists():
            continue
        for f in folder.glob("*.md"):
            content = f.read_text(encoding="utf-8")
            fm = parse_frontmatter(content)
            if fm.get("summary") in ("", "Waiting for AI processing...", "*Waiting for AI processing...*"):
                notes.append(f)
    return notes


def process_note(path: Path, classify_fn, dry_run: bool = False) -> dict | None:
    """Classify a single note and update its frontmatter. Returns entry info."""
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as exc:
        log.error(f"Could not read {path}: {exc}")
        return None

    existing_fm = parse_frontmatter(content)
    body = get_body(content)

    # Classify
    try:
        result = classify_fn(content)
    except Exception as exc:
        log.error(f"LLM classification failed for {path.name}: {exc}")
        return None

    # Merge: prefer existing frontmatter for type and contributor
    note_type = existing_fm.get("type") if existing_fm.get("type") in DEST_FOLDERS else result.get("type", "general")
    contributor = existing_fm.get("contributor") or result.get("contributor", "")
    summary = result.get("summary", "")[:120]
    tags = result.get("tags", [])[:5]
    date = existing_fm.get("date", datetime.now().strftime("%Y-%m-%d"))
    status = existing_fm.get("status", "")

    # Build updated frontmatter
    meta = {"type": note_type, "date": date, "contributor": contributor, "summary": summary}
    if status:
        meta["status"] = status
    # Preserve extra fields (repo, branch, session_id, tool, source_id, url)
    for k in ("repo", "branch", "session_id", "tool", "source_id", "url"):
        if k in existing_fm and existing_fm[k]:
            meta[k] = existing_fm[k]
    meta["tags"] = tags

    new_content = rebuild_frontmatter(meta, body)

    log.info(f"  {path.name}: type={note_type}, contributor={contributor}, summary={summary[:60]}")

    if dry_run:
        return {"type": note_type, "contributor": contributor, "summary": summary, "body": body, "path": str(path)}

    # Write updated content
    path.write_text(new_content, encoding="utf-8")

    # Move if in inbox
    if path.parent == INBOX_PATH:
        dest_dir = DEST_FOLDERS.get(note_type, DEST_FOLDERS["general"])
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / path.name
        if dest_path.exists():
            dest_path = dest_dir / f"{path.stem}-{int(time.time())}{path.suffix}"
        shutil.move(str(path), str(dest_path))
        log.info(f"  Moved -> {dest_path.relative_to(VAULT_PATH)}")

    return {"type": note_type, "contributor": contributor, "summary": summary, "body": body, "path": str(path)}


def generate_digest(entries: list[dict], digest_fn, dry_run: bool = False) -> Path | None:
    """Generate a daily team digest from today's processed entries."""
    if not entries:
        log.info("No entries for digest.")
        return None

    today = datetime.now().strftime("%Y-%m-%d")
    digest_file = DIGEST_PATH / f"digest-{today}.md"

    if digest_file.exists():
        log.info(f"Digest already exists: {digest_file.name}")
        return digest_file

    log.info(f"Generating digest from {len(entries)} entries...")

    try:
        digest_body = digest_fn(entries)
    except Exception as exc:
        log.error(f"Digest generation failed: {exc}")
        return None

    contributors = sorted(set(e["contributor"] for e in entries if e["contributor"]))
    tags_list = ["digest", today]

    meta = {
        "type": "daily-log",
        "date": today,
        "contributor": "organizer",
        "summary": f"Team digest — {len(entries)} entries from {len(contributors)} contributors",
        "tags": tags_list,
    }

    content = rebuild_frontmatter(meta, f"# Team Digest — {today}\n\n{digest_body}")

    if dry_run:
        log.info(f"[DRY RUN] Would write digest to {digest_file.name}")
        print("\n--- DIGEST PREVIEW ---")
        print(content[:2000])
        return None

    DIGEST_PATH.mkdir(parents=True, exist_ok=True)
    digest_file.write_text(content, encoding="utf-8")
    log.info(f"Digest written: {digest_file.name}")
    return digest_file


# ── Main ────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Research Log Organizer")
    parser.add_argument("--dry-run", action="store_true", help="Preview without changes")
    parser.add_argument("--no-push", action="store_true", help="Organize but don't push")
    parser.add_argument("--no-pull", action="store_true", help="Skip git pull")
    parser.add_argument("--no-digest", action="store_true", help="Skip digest generation")
    parser.add_argument("--provider", default="anthropic", choices=["anthropic", "gemini"],
                        help="LLM provider (default: anthropic)")
    args = parser.parse_args()

    log.info("=" * 60)
    log.info(f"Organizer starting. Provider: {args.provider}")
    log.info(f"Vault: {VAULT_PATH}")

    # Select LLM functions
    if args.provider == "anthropic":
        if not os.environ.get("ANTHROPIC_API_KEY"):
            log.error("ANTHROPIC_API_KEY not set. Export it or use --provider gemini")
            sys.exit(1)
        classify_fn = llm_classify_anthropic
        digest_fn = llm_digest_anthropic
    else:
        if not os.environ.get("GEMINI_API_KEY"):
            log.error("GEMINI_API_KEY not set.")
            sys.exit(1)
        classify_fn = llm_classify_gemini
        digest_fn = llm_digest_gemini

    # Step 1: Pull
    if not args.no_pull and not args.dry_run:
        try:
            git_pull()
        except Exception as exc:
            log.warning(f"Pull failed: {exc}. Continuing with local state.")

    # Step 2: Find notes to process
    inbox_notes = find_unprocessed_notes()
    incomplete_notes = find_incomplete_notes()
    all_notes = inbox_notes + incomplete_notes

    if not all_notes:
        log.info("No notes to process.")
        return

    log.info(f"Found {len(inbox_notes)} inbox notes, {len(incomplete_notes)} incomplete notes")

    # Step 3: Process each note
    processed = []
    for note in all_notes:
        log.info(f"Processing: {note.name}")
        entry = process_note(note, classify_fn, dry_run=args.dry_run)
        if entry:
            processed.append(entry)
        # Rate limit
        time.sleep(0.5)

    log.info(f"Processed {len(processed)} notes.")

    # Step 4: Generate digest
    if not args.no_digest and processed:
        # Only include today's entries in the digest
        today = datetime.now().strftime("%Y-%m-%d")
        todays_entries = [e for e in processed if today in e.get("path", "")]
        if not todays_entries:
            todays_entries = processed  # fallback: include everything we just processed
        generate_digest(todays_entries, digest_fn, dry_run=args.dry_run)

    # Step 5: Commit and push
    if not args.dry_run:
        today = datetime.now().strftime("%Y-%m-%d")
        message = f"organizer: processed {len(processed)} notes — {today}"
        git_commit_and_push(message, push=not args.no_push)

    log.info("Organizer complete.")


if __name__ == "__main__":
    main()
