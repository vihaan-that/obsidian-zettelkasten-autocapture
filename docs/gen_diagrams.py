#!/usr/bin/env python3
"""Generate PNG diagrams for the Research Log README."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
DPI = 180

# ── Color palette ───────────────────────────────────────────
BG       = "#0d1117"
FG       = "#c9d1d9"
ACCENT   = "#58a6ff"
GREEN    = "#3fb950"
ORANGE   = "#d29922"
PURPLE   = "#bc8cff"
RED      = "#f85149"
TEAL     = "#39d353"
GRAY     = "#484f58"
DARK     = "#161b22"
CARD     = "#21262d"
BORDER   = "#30363d"


def styled_fig(figsize=(16, 9)):
    fig, ax = plt.subplots(figsize=figsize, facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, color=ACCENT, fontsize=9, text_color=FG, style="round,pad=0.3", alpha=0.9, linewidth=1.5):
    rect = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=style,
        facecolor=color, edgecolor=BORDER,
        alpha=alpha, linewidth=linewidth, zorder=2,
    )
    ax.add_patch(rect)
    ax.text(
        x + w / 2, y + h / 2, text,
        ha="center", va="center", fontsize=fontsize,
        color=text_color, fontweight="bold", zorder=3,
        wrap=True,
    )
    return rect


def arrow(ax, x1, y1, x2, y2, color=FG, style="->", lw=1.5, connectionstyle="arc3,rad=0"):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle=style, color=color, lw=lw,
            connectionstyle=connectionstyle,
        ),
        zorder=1,
    )


def label(ax, x, y, text, fontsize=8, color=FG, ha="center", va="center", style="normal"):
    ax.text(x, y, text, ha=ha, va=va, fontsize=fontsize, color=color, fontstyle=style, zorder=4)


# ============================================================
# DIAGRAM 1: Data Flow
# ============================================================
def data_flow_diagram():
    fig, ax = styled_fig((18, 11))

    # Title
    ax.text(50, 97, "DATA FLOW DIAGRAM", ha="center", va="center",
            fontsize=16, color=ACCENT, fontweight="bold")
    ax.text(50, 94, "How entries move from creation to storage",
            ha="center", va="center", fontsize=10, color=GRAY)

    # ── Sources (left column) ───────────────────────────────
    label(ax, 12, 86, "CAPTURE SOURCES", fontsize=11, color=ORANGE)

    box(ax, 2, 74, 20, 7, "log.sh\n(interactive CLI)", color="#1a3a1a", text_color=GREEN)
    box(ax, 2, 62, 20, 7, "Claude Code\n(Stop hook)", color="#1a2a3a", text_color=ACCENT)
    box(ax, 2, 50, 20, 7, "Git Commits\n(post-commit hook)", color="#2a1a3a", text_color=PURPLE)
    box(ax, 2, 38, 20, 7, "Browser Export\n(Chrome extension)", color="#3a2a1a", text_color=ORANGE)
    box(ax, 2, 26, 20, 7, "Manual Drop\n(papers, PDFs)", color="#1a2a2a", text_color=TEAL)

    # ── Inbox (center-left) ─────────────────────────────────
    box(ax, 30, 48, 14, 14, "00-Inbox/\n\nStaging\nArea", color="#2a1a00", text_color=ORANGE, fontsize=10)

    # Arrows: sources -> inbox
    for sy in [77.5, 65.5, 53.5, 41.5, 29.5]:
        arrow(ax, 22, sy, 30, 55, color=GRAY, lw=1.2, connectionstyle="arc3,rad=0.1")

    # ── Watcher (center) ────────────────────────────────────
    box(ax, 50, 50, 16, 10, "Inbox Watcher\n\nClassify + Tag\n+ File", color="#0a1a2a", text_color=ACCENT, fontsize=10)

    arrow(ax, 44, 55, 50, 55, color=ORANGE, lw=2, style="-|>")
    label(ax, 47, 57.5, ".md file\ncreated", fontsize=7, color=GRAY)

    # ── AI / Keyword classification ─────────────────────────
    box(ax, 52, 68, 12, 7, "Gemini AI\nClassification", color="#1a1a2a", text_color=PURPLE, fontsize=8)
    box(ax, 52, 36, 12, 7, "Keyword\nFallback", color="#1a1a2a", text_color=GRAY, fontsize=8)

    arrow(ax, 58, 60, 58, 68, color=PURPLE, lw=1, style="->", connectionstyle="arc3,rad=0")
    arrow(ax, 58, 50, 58, 43, color=GRAY, lw=1, style="->", connectionstyle="arc3,rad=0")

    label(ax, 64, 65, "API key set?", fontsize=7, color=GRAY)
    label(ax, 64, 47, "no key", fontsize=7, color=GRAY)

    # ── Destinations (right column) ─────────────────────────
    label(ax, 85, 86, "VAULT DESTINATIONS", fontsize=11, color=GREEN)

    dests = [
        (78, 76, "50-Daily-Logs/", GREEN),
        (78, 68, "55-Journals/", TEAL),
        (78, 60, "40-Experiments/", PURPLE),
        (78, 52, "20-Code-Sessions/", ACCENT),
        (78, 44, "30-Research/", ORANGE),
        (78, 36, "10-LLM-Chats/", "#f0883e"),
        (78, 28, "60-Permanent/", GRAY),
    ]

    for dx, dy, dtxt, dcol in dests:
        box(ax, dx, dy, 20, 6, dtxt, color="#0d1a0d", text_color=dcol, fontsize=8)
        arrow(ax, 66, 55, dx, dy + 3, color=dcol, lw=1, style="->", connectionstyle="arc3,rad=0.05")

    # ── Notification + question ─────────────────────────────
    box(ax, 50, 18, 16, 8, "Desktop\nNotification\n+ Question", color="#2a1a1a", text_color=RED, fontsize=8)
    arrow(ax, 58, 50, 58, 26, color=RED, lw=1, style="->")
    label(ax, 48, 14, "User response appended\nas '## Reflection'", fontsize=7, color=GRAY, ha="center")

    # ── Frontmatter injection note ──────────────────────────
    box(ax, 30, 18, 14, 8, "YAML\nFrontmatter\nInjected", color="#0d1a1a", text_color=TEAL, fontsize=8)
    arrow(ax, 37, 48, 37, 26, color=TEAL, lw=1, style="->")

    # ── Cron reminder ───────────────────────────────────────
    box(ax, 2, 12, 20, 7, "Cron / launchd\n(daily reminder)", color="#1a1a1a", text_color=GRAY, fontsize=8)
    arrow(ax, 12, 19, 12, 74, color=GRAY, lw=1, style="->", connectionstyle="arc3,rad=-0.3")
    label(ax, 6, 22, "triggers", fontsize=7, color=GRAY)

    fig.savefig(os.path.join(OUT_DIR, "data-flow.png"), dpi=DPI, bbox_inches="tight",
                facecolor=BG, edgecolor="none", pad_inches=0.3)
    plt.close(fig)
    print("  data-flow.png")


# ============================================================
# DIAGRAM 2: Process Flow — log.sh
# ============================================================
def process_flow_diagram():
    fig, ax = styled_fig((18, 14))

    ax.text(50, 97, "PROCESS FLOW — log.sh", ha="center", va="center",
            fontsize=16, color=GREEN, fontweight="bold")
    ax.text(50, 94.5, "Interactive daily log entry walkthrough",
            ha="center", va="center", fontsize=10, color=GRAY)

    # ── Start ───────────────────────────────────────────────
    box(ax, 40, 87, 20, 5, "bash scripts/log.sh", color="#1a3a1a", text_color=GREEN, fontsize=10)

    # ── Args check ──────────────────────────────────────────
    box(ax, 40, 78, 20, 5, "Parse CLI args\n--name  --type  --editor", color=CARD, text_color=FG, fontsize=8)
    arrow(ax, 50, 87, 50, 83, color=GREEN, lw=2, style="-|>")

    # ── Name prompt ─────────────────────────────────────────
    box(ax, 40, 69, 20, 5, "Prompt: \"Your name\"", color="#1a2a3a", text_color=ACCENT, fontsize=9)
    arrow(ax, 50, 78, 50, 74, color=FG, lw=1.5, style="-|>")

    # cached name
    box(ax, 68, 69, 18, 5, ".contributor cache\n(remembers name)", color=CARD, text_color=GRAY, fontsize=7)
    arrow(ax, 60, 71.5, 68, 71.5, color=GRAY, lw=1, style="<->")

    # ── Type selection ──────────────────────────────────────
    box(ax, 40, 60, 20, 5, "Prompt: entry type\n1) daily-log  2) journal  3) experiment", color="#1a2a3a", text_color=ACCENT, fontsize=8)
    arrow(ax, 50, 69, 50, 65, color=FG, lw=1.5, style="-|>")

    # ── Branch: 3 types ─────────────────────────────────────
    # daily-log branch (left)
    box(ax, 5, 46, 25, 10, "STRUCTURED PROMPTS\n\nWork done\nPivots & corrections\nDecisions & reasoning\nTangents explored\nBlockers\nStatus & next steps",
        color="#0d1a0d", text_color=GREEN, fontsize=7)
    arrow(ax, 43, 60, 17.5, 56, color=GREEN, lw=1.5, style="-|>")
    label(ax, 28, 57, "daily-log", fontsize=8, color=GREEN)

    # journal branch (center)
    box(ax, 37, 46, 25, 10, "FREESTYLE\n\nWrite freely.\nPrompts if stuck:\n- What surprised you?\n- What will you forget?\n- What would you tell a teammate?",
        color="#0d1a2a", text_color=TEAL, fontsize=7)
    arrow(ax, 50, 60, 50, 56, color=TEAL, lw=1.5, style="-|>")
    label(ax, 50, 57.5, "journal", fontsize=8, color=TEAL)

    # experiment branch (right)
    box(ax, 68, 46, 25, 10, "EXPERIMENT PROMPTS\n\nHypothesis\nSetup\nObservations\nResult\nNext steps\nStatus",
        color="#1a0d1a", text_color=PURPLE, fontsize=7)
    arrow(ax, 57, 60, 80.5, 56, color=PURPLE, lw=1.5, style="-|>")
    label(ax, 70, 57, "experiment", fontsize=8, color=PURPLE)

    # ── Editor mode overlay ─────────────────────────────────
    box(ax, 5, 34, 25, 6, "--editor flag?\nOpen template in $EDITOR", color=CARD, text_color=ORANGE, fontsize=8)
    label(ax, 17.5, 31, "(skips inline prompts)", fontsize=7, color=GRAY)

    # ── Tags ────────────────────────────────────────────────
    box(ax, 37, 34, 25, 6, "Prompt: tags\n(comma-separated, optional)", color="#1a2a3a", text_color=ACCENT, fontsize=8)
    arrow(ax, 17.5, 46, 17.5, 42, color=FG, lw=1, style="-|>")
    arrow(ax, 50, 46, 50, 40, color=FG, lw=1, style="-|>")
    arrow(ax, 80.5, 46, 80.5, 42, color=FG, lw=1, style="-|>")
    # converge
    arrow(ax, 17.5, 38, 37, 37, color=FG, lw=1, style="-|>")
    arrow(ax, 80.5, 38, 62, 37, color=FG, lw=1, style="-|>")

    # ── Build YAML + markdown ───────────────────────────────
    box(ax, 35, 22, 30, 7, "Build Markdown File\n\nYAML frontmatter: type, date, contributor, tags\n+ section content from prompts",
        color=DARK, text_color=FG, fontsize=8)
    arrow(ax, 50, 34, 50, 29, color=FG, lw=1.5, style="-|>")

    # ── Write to inbox ──────────────────────────────────────
    box(ax, 35, 12, 30, 6, "Write to  vault/00-Inbox/\ndaily-log-2026-04-09-alice.md",
        color="#2a1a00", text_color=ORANGE, fontsize=9)
    arrow(ax, 50, 22, 50, 18, color=ORANGE, lw=2, style="-|>")

    # ── Watcher picks up ────────────────────────────────────
    box(ax, 35, 3, 30, 5, "Inbox watcher classifies, files, and asks one question",
        color="#0a1a2a", text_color=ACCENT, fontsize=8)
    arrow(ax, 50, 12, 50, 8, color=ACCENT, lw=1.5, style="-|>")
    label(ax, 50, 1.5, "(if watcher is running)", fontsize=7, color=GRAY)

    fig.savefig(os.path.join(OUT_DIR, "process-flow.png"), dpi=DPI, bbox_inches="tight",
                facecolor=BG, edgecolor="none", pad_inches=0.3)
    plt.close(fig)
    print("  process-flow.png")


# ============================================================
# DIAGRAM 3: Watcher Pipeline
# ============================================================
def watcher_pipeline_diagram():
    fig, ax = styled_fig((18, 10))

    ax.text(50, 96, "WATCHER PIPELINE", ha="center", va="center",
            fontsize=16, color=PURPLE, fontweight="bold")
    ax.text(50, 93, "inbox_watcher.py — automatic classification and filing",
            ha="center", va="center", fontsize=10, color=GRAY)

    # Pipeline stages left to right
    stages_y = 60

    # Stage 1: File detected
    box(ax, 2, stages_y - 5, 14, 10, "File Detected\n\nwatchdog\non_created\non_moved", color=DARK, text_color=FG, fontsize=8)

    # Stage 2: Read content
    box(ax, 20, stages_y - 5, 14, 10, "Read Content\n\n.read_text()\nUTF-8", color=DARK, text_color=FG, fontsize=8)
    arrow(ax, 16, stages_y, 20, stages_y, color=ACCENT, lw=2, style="-|>")

    # Stage 3: Classify
    box(ax, 38, stages_y - 5, 14, 10, "Classify\n\nAI (Gemini)\nor keywords", color="#1a1a2a", text_color=PURPLE, fontsize=8)
    arrow(ax, 34, stages_y, 38, stages_y, color=ACCENT, lw=2, style="-|>")

    # Stage 4: Inject frontmatter
    box(ax, 56, stages_y - 5, 14, 10, "Inject\nFrontmatter\n\ntype, date,\ncontributor,\nsummary, tags", color="#0d1a1a", text_color=TEAL, fontsize=8)
    arrow(ax, 52, stages_y, 56, stages_y, color=ACCENT, lw=2, style="-|>")

    # Stage 5: Move to destination
    box(ax, 74, stages_y - 5, 14, 10, "Move to\nDestination\n\n50-Daily-Logs/\n55-Journals/\netc.", color="#1a3a1a", text_color=GREEN, fontsize=8)
    arrow(ax, 70, stages_y, 74, stages_y, color=ACCENT, lw=2, style="-|>")

    # Stage 6: Ask question
    box(ax, 87, stages_y - 5, 12, 10, "Ask User\nQuestion\n\nnotify-send\n+ zenity\n(or osascript)", color="#2a1a1a", text_color=RED, fontsize=7)
    arrow(ax, 88, stages_y, 87, stages_y, color=ACCENT, lw=2, style="-|>")

    # ── Classification detail (below) ───────────────────────
    label(ax, 50, 44, "CLASSIFICATION LOGIC", fontsize=11, color=ORANGE)

    # AI path
    box(ax, 8, 28, 30, 12, "AI Classification (Gemini 2.0 Flash)\n\n"
        "Input: first 3000 chars of note\n"
        "Output: { type, summary, tags, contributor }\n"
        "Strips markdown fences, validates JSON",
        color="#1a1a2a", text_color=PURPLE, fontsize=7)
    label(ax, 23, 25, "when GEMINI_API_KEY is set", fontsize=7, color=GRAY)

    # Keyword path
    box(ax, 55, 28, 35, 12, "Keyword Fallback\n\n"
        "daily-log:    \"what i worked on\", \"pivots\", \"daily log\"\n"
        "journal:       \"stream of consciousness\", \"journal\"\n"
        "experiment:  \"hypothesis\", \"observations\"\n"
        "code-session: \"claude code\", \"git commit\", \"branch:\"\n"
        "research:      \"abstract\", \"paper\", \"doi:\", \"arxiv\"",
        color=DARK, text_color=GRAY, fontsize=7)
    label(ax, 72.5, 25, "when no API key", fontsize=7, color=GRAY)

    arrow(ax, 38, 34, 55, 34, color=GRAY, lw=1, style="<->")
    label(ax, 46.5, 36, "fallback", fontsize=8, color=GRAY)

    # ── Frontmatter schema (bottom) ─────────────────────────
    box(ax, 20, 6, 60, 14, "YAML FRONTMATTER SCHEMA\n\n"
        "type: daily-log | journal | experiment | code-session | research | llm-chat | general\n"
        "date: 2026-04-09\n"
        "contributor: \"alice\"\n"
        "summary: \"Explored new tokenizer approach for embedding pipeline\"\n"
        "status: \"in-progress\"    (daily-logs and experiments only)\n"
        "tags: [ \"daily-log\", \"ml-pipeline\", \"tokenizer\" ]",
        color=DARK, text_color=TEAL, fontsize=7)

    fig.savefig(os.path.join(OUT_DIR, "watcher-pipeline.png"), dpi=DPI, bbox_inches="tight",
                facecolor=BG, edgecolor="none", pad_inches=0.3)
    plt.close(fig)
    print("  watcher-pipeline.png")


# ============================================================
# DIAGRAM 4: System Architecture
# ============================================================
def architecture_diagram():
    fig, ax = styled_fig((18, 12))

    ax.text(50, 97, "SYSTEM ARCHITECTURE", ha="center", va="center",
            fontsize=16, color=ACCENT, fontweight="bold")
    ax.text(50, 94.5, "Full system overview — capture, processing, storage, consumption",
            ha="center", va="center", fontsize=10, color=GRAY)

    # ── Layer 1: Capture (top) ──────────────────────────────
    label(ax, 50, 89, "CAPTURE LAYER", fontsize=11, color=ORANGE)

    box(ax, 3, 82, 15, 5, "log.sh (CLI)", color="#1a3a1a", text_color=GREEN, fontsize=9)
    box(ax, 21, 82, 15, 5, "Claude Code\nStop Hook", color="#1a2a3a", text_color=ACCENT, fontsize=8)
    box(ax, 39, 82, 15, 5, "Git\npost-commit", color="#2a1a3a", text_color=PURPLE, fontsize=8)
    box(ax, 57, 82, 15, 5, "Browser\nExtension", color="#3a2a1a", text_color=ORANGE, fontsize=8)
    box(ax, 75, 82, 15, 5, "Manual\nDrop", color="#1a2a2a", text_color=TEAL, fontsize=8)

    # ── Layer 2: Cron ───────────────────────────────────────
    box(ax, 3, 74, 15, 5, "Cron / launchd\n(daily reminder)", color=CARD, text_color=GRAY, fontsize=7)
    arrow(ax, 10.5, 79, 10.5, 82, color=GRAY, lw=1, style="-|>")
    label(ax, 17, 76.5, "triggers", fontsize=7, color=GRAY)

    # ── Layer 2: Processing ─────────────────────────────────
    label(ax, 50, 73, "PROCESSING LAYER", fontsize=11, color=PURPLE)

    # Inbox
    box(ax, 22, 63, 16, 7, "00-Inbox/\n(staging)", color="#2a1a00", text_color=ORANGE, fontsize=10)

    # Arrows from capture to inbox
    for cx in [10.5, 28.5, 46.5, 64.5, 82.5]:
        arrow(ax, cx, 82, 30, 70, color=GRAY, lw=1, style="->", connectionstyle="arc3,rad=0.05")

    # Watcher
    box(ax, 45, 63, 20, 7, "inbox_watcher.py\n\nwatchdog daemon\nclassify + tag + file", color="#0a1a2a", text_color=ACCENT, fontsize=8)
    arrow(ax, 38, 66.5, 45, 66.5, color=ORANGE, lw=2, style="-|>")

    # AI
    box(ax, 72, 65, 16, 5, "Gemini 2.0 Flash\n(or keyword fallback)", color="#1a1a2a", text_color=PURPLE, fontsize=7)
    arrow(ax, 65, 66.5, 72, 67.5, color=PURPLE, lw=1, style="<->")

    # ── Layer 3: Storage ────────────────────────────────────
    label(ax, 50, 55, "STORAGE LAYER — Obsidian Vault", fontsize=11, color=GREEN)

    folders = [
        (3, 44, "50-Daily-\nLogs/", GREEN),
        (18, 44, "55-\nJournals/", TEAL),
        (33, 44, "40-\nExperiments/", PURPLE),
        (48, 44, "20-Code-\nSessions/", ACCENT),
        (63, 44, "30-\nResearch/", ORANGE),
        (78, 44, "10-LLM-\nChats/", "#f0883e"),
    ]
    for fx, fy, ftxt, fcol in folders:
        box(ax, fx, fy, 13, 7, ftxt, color="#0d1a0d", text_color=fcol, fontsize=8)

    # Arrows from watcher to folders
    for fx, _, _, fcol in folders:
        arrow(ax, 55, 63, fx + 6.5, 51, color=fcol, lw=1, style="->", connectionstyle="arc3,rad=0.02")

    # Support folders
    box(ax, 20, 34, 15, 6, "_Templates/\n3 templates", color=CARD, text_color=GRAY, fontsize=7)
    box(ax, 40, 34, 15, 6, "_Dashboard/\nHome.md", color=CARD, text_color=GRAY, fontsize=7)
    box(ax, 60, 34, 15, 6, "_Scripts/\nwatcher, logs", color=CARD, text_color=GRAY, fontsize=7)

    # ── Layer 4: Consumption ────────────────────────────────
    label(ax, 50, 27, "CONSUMPTION LAYER", fontsize=11, color=ACCENT)

    box(ax, 8, 14, 22, 10, "Obsidian\n\nDataview dashboard\nPer-contributor views\nTag-based queries\nTeam activity feed",
        color="#0d1a2a", text_color=ACCENT, fontsize=8)
    box(ax, 38, 14, 22, 10, "GitHub Repo\n\nVersion history\nPR-based review\nCollaborative editing\nBranch per contributor",
        color="#1a1a1a", text_color=FG, fontsize=8)
    box(ax, 68, 14, 22, 10, "LLM Agent System\n\nYAML frontmatter queries\nFull-text search\nSemantic filtering\nContext retrieval",
        color="#1a0d2a", text_color=PURPLE, fontsize=8)

    # Arrows from storage to consumption
    arrow(ax, 30, 40, 19, 24, color=ACCENT, lw=1.5, style="-|>")
    arrow(ax, 50, 40, 49, 24, color=FG, lw=1.5, style="-|>")
    arrow(ax, 70, 40, 79, 24, color=PURPLE, lw=1.5, style="-|>")

    # ── YAML schema note ────────────────────────────────────
    box(ax, 30, 3, 40, 7, "Every note: { type, date, contributor, summary, tags }\n"
        "Consistent schema = queryable by humans and machines",
        color=DARK, text_color=TEAL, fontsize=8)

    fig.savefig(os.path.join(OUT_DIR, "architecture.png"), dpi=DPI, bbox_inches="tight",
                facecolor=BG, edgecolor="none", pad_inches=0.3)
    plt.close(fig)
    print("  architecture.png")


# ============================================================
# DIAGRAM 5: Team Workflow (GitHub-centric)
# ============================================================
def team_workflow_diagram():
    fig, ax = styled_fig((18, 12))

    ax.text(50, 97, "TEAM WORKFLOW", ha="center", va="center",
            fontsize=16, color=GREEN, fontweight="bold")
    ax.text(50, 94, "GitHub as the central hub — team members push, organizer processes",
            ha="center", va="center", fontsize=10, color=GRAY)

    # ── Team Members (left side) ────────────────────────────
    label(ax, 18, 88, "TEAM MEMBERS", fontsize=12, color=GREEN)
    label(ax, 18, 85.5, "(each person's machine)", fontsize=8, color=GRAY)

    # Member boxes
    members = [
        (3, 70, "Alice", GREEN),
        (3, 55, "Bob", TEAL),
        (3, 40, "Carol", PURPLE),
    ]
    for mx, my, mname, mcol in members:
        box(ax, mx, my, 28, 11,
            f"{mname}'s Machine\n\n"
            f"1. rlog         (write daily entry)\n"
            f"2. rlog-sync    (commit + push)\n\n"
            f"One-time: bash scripts/setup-member.sh",
            color="#0d1a0d", text_color=mcol, fontsize=7)

    # ── GitHub (center) ─────────────────────────────────────
    box(ax, 38, 50, 22, 16, "GitHub Repo\n\n"
        "vault/\n"
        "  00-Inbox/\n"
        "  50-Daily-Logs/\n"
        "  55-Journals/\n"
        "  40-Experiments/\n"
        "  ...\n\n"
        "Single source of truth",
        color="#1a1a1a", text_color=FG, fontsize=8)

    label(ax, 49, 68, "github.com/...", fontsize=9, color=ACCENT)

    # Arrows: members -> GitHub (push)
    for _, my, _, mcol in members:
        arrow(ax, 31, my + 5.5, 38, 58, color=mcol, lw=1.5, style="-|>", connectionstyle="arc3,rad=0.08")

    label(ax, 35, 72, "git push", fontsize=8, color=GREEN)

    # ── Admin PC (right side) ──────────────────────────────
    label(ax, 78, 88, "ADMIN PC", fontsize=12, color=ORANGE)
    label(ax, 78, 85.5, "(Vihaan's machine — runs evening job)", fontsize=8, color=GRAY)

    # Organizer
    box(ax, 65, 64, 28, 16, "Evening Organizer\n(cron @ 9pm)\n\n"
        "1. git pull\n"
        "2. Find unprocessed notes\n"
        "3. LLM classify + summarize\n"
        "4. Generate daily digest\n"
        "5. Move to correct folders\n"
        "6. git commit + push",
        color="#2a1a00", text_color=ORANGE, fontsize=7)

    # Arrow: GitHub -> Organizer (pull)
    arrow(ax, 60, 60, 65, 70, color=ACCENT, lw=2, style="-|>")
    label(ax, 60, 63, "git pull", fontsize=8, color=ACCENT)

    # Arrow: Organizer -> GitHub (push)
    arrow(ax, 65, 66, 60, 58, color=ORANGE, lw=2, style="-|>")
    label(ax, 60, 60, "git push", fontsize=8, color=ORANGE)

    # LLM box
    box(ax, 72, 48, 18, 10, "LLM API\n\nClaude (Anthropic)\nor Gemini\n\nClassify, summarize,\ngenerate digest",
        color="#1a0d2a", text_color=PURPLE, fontsize=7)
    arrow(ax, 79, 64, 79, 58, color=PURPLE, lw=1.5, style="<->")

    # ── Daily Digest ────────────────────────────────────────
    box(ax, 38, 30, 22, 10, "Daily Digest\n\ndigest-2026-04-09.md\n\n"
        "Key highlights\n"
        "By contributor\n"
        "Open blockers\n"
        "Decisions made",
        color="#0d1a2a", text_color=ACCENT, fontsize=7)

    arrow(ax, 79, 48, 60, 35, color=ACCENT, lw=1.5, style="-|>")
    label(ax, 70, 42, "generates", fontsize=7, color=GRAY)

    # ── Timeline ────────────────────────────────────────────
    label(ax, 50, 22, "DAILY TIMELINE", fontsize=11, color=GRAY)

    # Timeline bar
    ax.plot([10, 90], [17, 17], color=GRAY, lw=2, zorder=1)

    times = [
        (15, "9:00 AM\nTeam logs work\n(rlog)", GREEN),
        (35, "Throughout day\nMore entries\n(rlog, hooks)", TEAL),
        (55, "5:00 PM\nTeam syncs\n(rlog-sync)", ACCENT),
        (75, "9:00 PM\nOrganizer runs\n(cron)", ORANGE),
    ]
    for tx, tlabel, tcol in times:
        ax.plot(tx, 17, 'o', color=tcol, markersize=8, zorder=3)
        label(ax, tx, 11, tlabel, fontsize=7, color=tcol)

    # ── Setup note ──────────────────────────────────────────
    box(ax, 15, 1, 70, 5, "Team member setup (one time):  git clone <repo>  &&  cd research-log  &&  bash scripts/setup-member.sh\n"
        "Admin setup (one time):  bash scripts/setup-organizer.sh --hour 21 --provider anthropic",
        color=DARK, text_color=FG, fontsize=7)

    fig.savefig(os.path.join(OUT_DIR, "team-workflow.png"), dpi=DPI, bbox_inches="tight",
                facecolor=BG, edgecolor="none", pad_inches=0.3)
    plt.close(fig)
    print("  team-workflow.png")


# ── Generate all ────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating diagrams...")
    data_flow_diagram()
    process_flow_diagram()
    watcher_pipeline_diagram()
    architecture_diagram()
    team_workflow_diagram()
    print("Done.")
