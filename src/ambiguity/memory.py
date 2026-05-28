"""Project-level memory — logs prompt interactions to docs/memory.md."""

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .analyzer import Analysis


MEMORY_PATH = Path("docs") / "memory.md"


def _find_memory() -> Path | None:
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        candidate = parent / MEMORY_PATH
        if candidate.exists():
            return candidate
    return None


def _prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:8]


def _format_entry(
    analysis: Analysis,
    action: str = "none",
    changes: list[dict[str, str]] | None = None,
    outcome: str = "accepted",
    note: str = "",
) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    h = _prompt_hash(analysis.raw_text)
    changes_str = ""
    if changes:
        items = []
        for c in changes:
            orig = c.get("original", "").replace('"', "'")
            repl = c.get("replacement", "").replace("\n", " ").replace('"', "'")[:60]
            items.append(f"      - type: {c['type']}\n        original: \"{orig}\"\n        replacement: \"{repl}\"")
        changes_str = "    changes:\n" + "\n".join(items) + "\n"
    note_str = f"    note: \"{note}\"\n" if note else ""

    return (
        f"- date: {ts}\n"
        f"  prompt: \"{analysis.raw_text[:80]}\"\n"
        f"  hash: {h}\n"
        f"  score: {analysis.score.total:.1f}\n"
        f"  band: {analysis.score.band}\n"
        f"  action: {action}\n"
        f"{changes_str}"
        f"  outcome: {outcome}\n"
        f"{note_str}"
    )


def log_interaction(
    prompt: str,
    action: str = "none",
    changes: list[dict[str, str]] | None = None,
    outcome: str = "accepted",
    note: str = "",
) -> Path | None:
    mem_path = _find_memory()
    if not mem_path:
        return None

    analysis = Analysis(prompt)
    entry = _format_entry(analysis, action, changes, outcome, note)

    try:
        existing = mem_path.read_text(encoding="utf-8")
    except (FileNotFoundError, IOError):
        existing = ""

    if "## Entries" not in existing:
        existing += "\n## Entries\n\n"

    section_marker = "## Entries"
    idx = existing.rfind(section_marker)
    if idx == -1:
        existing += entry + "\n"
    else:
        existing = existing[:idx] + section_marker + "\n\n" + entry + existing[idx + len(section_marker):]

    mem_path.write_text(existing, encoding="utf-8")
    return mem_path


def recent_entries(count: int = 5) -> list[dict[str, Any]]:
    mem_path = _find_memory()
    if not mem_path:
        return []

    try:
        text = mem_path.read_text(encoding="utf-8")
    except (FileNotFoundError, IOError):
        return []

    entries_marker = "## Entries"
    idx = text.find(entries_marker)
    if idx == -1:
        return []
    text = text[idx + len(entries_marker):]

    entries: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("- date:"):
            if current:
                entries.append(current)
            current = {"date": line.split(":", 1)[1].strip()}
        elif line.startswith("prompt:") and current:
            current["prompt"] = line.split(":", 1)[1].strip().strip('"')
        elif line.startswith("score:") and current:
            try:
                current["score"] = float(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif line.startswith("action:") and current:
            current["action"] = line.split(":", 1)[1].strip()

    if current:
        entries.append(current)

    return entries[-count:]


def summary() -> str:
    entries = recent_entries(20)
    if not entries:
        return "No interactions logged yet."

    lines = [f"Last {len(entries)} interaction(s):"]
    for e in entries:
        score = e.get("score", "?")
        action = e.get("action", "?")
        prompt = e.get("prompt", "?")[:50]
        lines.append(f"  [{score}/10] {action}: {prompt}")
    return "\n".join(lines)
