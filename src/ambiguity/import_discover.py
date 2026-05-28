"""Consent-gated auto-discovery and import of prompt history from harnesses."""

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .analyzer import Analysis
from .profile import get_profile
from .memory import log_interaction, _find_memory

# Known harness log locations (relative to user home)
HARNESS_PATHS = {
    "Claude Code": ["~/.claude/logs", "~/.claude/projects"],
    "Cursor": ["~/.cursor/logs", "~/.cursor/sessions"],
    "Windsurf": ["~/.windsurf/logs"],
    "opencode": ["~/.config/opencode/logs"],
    "Cline": ["~/.config/cline/logs"],
    "Roo": ["~/.config/roo/logs"],
    "Gemini CLI": ["~/.gemini/logs"],
    "Grok CLI": ["~/.grok/logs"],
}

# Split patterns — look for common prompt-like text
PROMPT_PATTERNS = [
    re.compile(r'\b(write|implement|create|build|make|generate|add|fix|refactor|update|delete|remove|change|modify|convert|transform|analyze|explain|describe|summarize|find|search|show|list|help|how|what|why)\b', re.IGNORECASE),
    re.compile(r'.{20,200}'),  # reasonable prompt length
]

CONVERSATION_PATTERNS = [
    re.compile(r'"role"\s*:\s*"user"', re.IGNORECASE),
    re.compile(r'"content"\s*:', re.IGNORECASE),
    re.compile(r'<\|im_start\|>user', re.IGNORECASE),
]


@dataclass
class DiscoveredPrompt:
    source: str
    harness: str
    prompt: str
    hash: str = ""
    analyzed: bool = False
    score: float = 0.0
    band: str = ""

    def __post_init__(self):
        import hashlib
        self.hash = hashlib.sha256(self.prompt.encode("utf-8")).hexdigest()[:8]


@dataclass
class ImportResult:
    sources_scanned: int = 0
    files_found: int = 0
    prompts_found: int = 0
    prompts_imported: int = 0
    by_harness: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    sample_prompts: list[DiscoveredPrompt] = field(default_factory=list)
    memory_path: str = ""


def _expand_path(p: str) -> Path | None:
    expanded = os.path.expanduser(p)
    path = Path(expanded)
    return path if path.exists() else None


def _scan_json_file(fp: Path, harness: str) -> list[str]:
    """Extract user messages from a JSON conversation log."""
    prompts: list[str] = []
    try:
        data = json.loads(fp.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, UnicodeDecodeError, PermissionError):
        return prompts

    # Handle both list-of-messages and object-with-messages formats
    messages = data if isinstance(data, list) else (
        data.get("messages", data.get("conversation", data.get("chat", [])))
    )
    if not isinstance(messages, list):
        return prompts

    for msg in messages:
        if isinstance(msg, dict):
            role = str(msg.get("role", "")).lower()
            content = msg.get("content", "")
            if role == "user" and content and isinstance(content, str) and len(content) > 10:
                prompts.append(content)
            # Handle content blocks (Anthropic format)
            elif role == "user" and isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = block.get("text", "")
                        if len(text) > 10:
                            prompts.append(text)
            # Handle OpenAI format
            elif "role" in msg and msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str) and len(content) > 10:
                    prompts.append(content)
    return prompts


def _scan_text_file(fp: Path, harness: str) -> list[str]:
    """Extract prompt-like lines from a text/markdown file."""
    prompts: list[str] = []
    try:
        text = fp.read_text(encoding="utf-8", errors="replace")
    except (PermissionError, UnicodeDecodeError):
        return prompts

    lines = text.split("\n")
    current: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "//", "--", "=", "*")):
            if current and PROMPT_PATTERNS[0].search(" ".join(current)):
                candidate = " ".join(current)
                if 10 < len(candidate) < 2000:
                    prompts.append(candidate)
            current = []
            continue
        current.append(stripped)
    if current:
        candidate = " ".join(current)
        if 10 < len(candidate) < 2000 and PROMPT_PATTERNS[0].search(candidate):
            prompts.append(candidate)
    return prompts


def _is_conversation_file(fp: Path) -> bool:
    """Quick check if a file looks like a conversation log (by extension + peek)."""
    if fp.suffix not in (".json", ".jsonl", ".ndjson", ".txt", ".md", ".log"):
        return False
    if fp.stat().st_size > 5_000_000:  # skip files > 5MB
        return False
    try:
        head = fp.read_bytes()[:2048].decode("utf-8", errors="replace")
        return bool(CONVERSATION_PATTERNS[0].search(head) or CONVERSATION_PATTERNS[1].search(head))
    except Exception:
        return False


def discover(consent: bool = False, dry_run: bool = True) -> ImportResult:
    """Scan known harness paths for prompt history.

    Args:
        consent: User has explicitly opted in
        dry_run: If True, report what would be imported without importing

    Returns:
        ImportResult with discovered prompts and per-harness counts
    """
    result = ImportResult()

    if not consent:
        result.errors.append("Consent not given — no paths scanned")
        return result

    seen_hashes: set[str] = set()
    all_prompts: list[DiscoveredPrompt] = []

    for harness, paths in HARNESS_PATHS.items():
        for p in paths:
            resolved = _expand_path(p)
            if not resolved:
                continue
            result.sources_scanned += 1

            # Scan JSON conversation files
            json_files = list(resolved.rglob("*.json")) + list(resolved.rglob("*.jsonl")) + list(resolved.rglob("*.ndjson"))
            for fp in json_files:
                result.files_found += 1
                if _is_conversation_file(fp):
                    prompts = _scan_json_file(fp, harness)
                    for prompt_text in prompts:
                        dp = DiscoveredPrompt(
                            source=str(fp.relative_to(resolved.parent) if fp.parent != resolved else fp.name),
                            harness=harness,
                            prompt=prompt_text,
                        )
                        if dp.hash not in seen_hashes:
                            seen_hashes.add(dp.hash)
                            all_prompts.append(dp)
                            result.prompts_found += 1

            # Scan text/markdown files for prompt-like content
            text_files = list(resolved.rglob("*.md")) + list(resolved.rglob("*.txt")) + list(resolved.rglob("*.log"))
            for fp in text_files:
                if fp.stat().st_size > 200_000:  # skip large files
                    continue
                result.files_found += 1
                prompts = _scan_text_file(fp, harness)
                for prompt_text in prompts:
                    dp = DiscoveredPrompt(
                        source=str(fp.relative_to(resolved.parent) if fp.parent != resolved else fp.name),
                        harness=harness,
                        prompt=prompt_text,
                    )
                    if dp.hash not in seen_hashes:
                        seen_hashes.add(dp.hash)
                        all_prompts.append(dp)
                        result.prompts_found += 1

    # Tally by harness
    for dp in all_prompts:
        result.by_harness[dp.harness] = result.by_harness.get(dp.harness, 0) + 1

    # Store a few samples for display
    result.sample_prompts = all_prompts[:5]

    if not dry_run and all_prompts:
        result.prompts_imported = _import_prompts(all_prompts)
        mem = _find_memory()
        if mem:
            result.memory_path = str(mem)

    return result


def _import_prompts(prompts: list[DiscoveredPrompt]) -> int:
    """Batch-analyze and log discovered prompts."""
    profile = get_profile()
    count = 0
    for dp in prompts[:100]:  # cap at 100 per import to keep it fast
        try:
            analysis = Analysis(dp.prompt)
            dp.score = analysis.score.total
            dp.band = analysis.score.band
            dp.analyzed = True

            # Record in profile for threshold calibration
            from .advisory import advisory
            adv = advisory(analysis.result, analysis.score)
            profile.record(analysis.result, analysis.score, adv)

            # Log to memory.md
            log_interaction(dp.prompt, action="import", outcome="accepted", note=f"auto-imported from {dp.harness}")
            count += 1
        except Exception:
            continue

    profile.save()
    return count


def render_import_report(result: ImportResult) -> str:
    sep = "=" * 56
    lines = [sep]
    lines.append("  ambiguity import — prompt history discovery")
    lines.append(sep)
    lines.append("")

    if not result.sources_scanned:
        lines.append("  No consent given. Run with --consent to scan.")
        lines.append(sep)
        return "\n".join(lines)

    lines.append(f"  Harness directories scanned: {result.sources_scanned}")
    lines.append(f"  Files examined:              {result.files_found}")
    lines.append(f"  Unique prompts found:        {result.prompts_found}")
    lines.append(f"  Prompts imported:            {result.prompts_imported}")
    lines.append("")
    if result.by_harness:
        lines.append("  By harness:")
        for harness, count in sorted(result.by_harness.items(), key=lambda x: -x[1]):
            lines.append(f"    {harness}: {count}")
    lines.append("")

    if result.sample_prompts:
        lines.append("  Sample prompts found:")
        for dp in result.sample_prompts[:3]:
            short = dp.prompt[:60].replace("\n", " ")
            lines.append(f"    [{dp.harness}] {short}...")
    lines.append("")

    if result.errors:
        lines.append("  Warnings:")
        for e in result.errors[:3]:
            lines.append(f"    ! {e}")
    lines.append("")

    if result.prompts_imported:
        lines.append(f"  Imported to memory.md ({result.memory_path})")
    lines.append(sep)
    return "\n".join(lines)


def render_import_json(result: ImportResult) -> dict[str, Any]:
    return {
        "command": "import",
        "sources_scanned": result.sources_scanned,
        "files_found": result.files_found,
        "prompts_found": result.prompts_found,
        "prompts_imported": result.prompts_imported,
        "by_harness": result.by_harness,
        "errors": result.errors,
        "sample_prompts": [
            {"source": dp.source, "harness": dp.harness, "prompt": dp.prompt[:100]}
            for dp in result.sample_prompts[:5]
        ],
    }
