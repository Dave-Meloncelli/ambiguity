"""Audit claimed file creations against actual filesystem state."""

import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_USE_UNICODE = sys.stdout.encoding and sys.stdout.encoding.lower() in ("utf-8", "utf8")
CHECK = "\u2713" if _USE_UNICODE else "[OK]"
CROSS = "\u2717" if _USE_UNICODE else "[X]"
ARROW = "\u2192" if _USE_UNICODE else "->"
ELLIPSIS = "\u2026" if _USE_UNICODE else "..."
TILDE = "~"


FILE_REF_PATTERN = re.compile(
    r'(?:^|\s)(?:`)?'
    r'((?:[\w.-]+/)*[\w.-]+\.\w+)'
    r'(?:`)?(?=\s|$|[.,;!?])',
    re.MULTILINE,
)

EXTRA_IGNORE = {".git", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}


@dataclass
class AuditResult:
    prompt: str
    claimed_files: list[str]
    actual_files: list[str]
    missing_files: list[str] = field(default_factory=list)
    extra_files: list[str] = field(default_factory=list)
    matched_files: list[str] = field(default_factory=list)
    near_matches: list[tuple[str, str, float]] = field(default_factory=list)
    permission_issues: list[str] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0


def _normalise(path: str) -> str:
    return path.replace("\\", "/").lower()


def _levenshtein_ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    a, b = a.lower(), b.lower()
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost,
            )
    return 1.0 - dp[n][m] / max(n, m)


def _extract_claimed_files(prompt: str) -> list[str]:
    seen: set[str] = set()
    files: list[str] = []
    for m in FILE_REF_PATTERN.finditer(prompt):
        path = m.group(1)
        if path not in seen and not path.startswith(("http://", "https://", "www.")):
            seen.add(path)
            files.append(path)
    return files


def _scan_actual_files(directory: str) -> list[str]:
    base = Path(directory).resolve()
    files: list[str] = []
    for fp in base.rglob("*"):
        rel = fp.relative_to(base)
        parts = set(rel.parts)
        if EXTRA_IGNORE & parts:
            continue
        if fp.is_file():
            files.append(str(rel.as_posix()))
    return sorted(files)


def _check_permissions(claimed: list[str], directory: str) -> list[str]:
    issues: list[str] = []
    for path in claimed:
        fp = Path(directory) / path
        if fp.exists() or fp.parent.exists():
            if fp.exists() and not os.access(str(fp), os.R_OK):
                issues.append(f"{path}: no read permission")
            parent = fp.parent
            while parent != parent.parent:
                if parent.exists() and not os.access(str(parent), os.W_OK):
                    issues.append(f"{path}: parent {parent} not writable")
                    break
                parent = parent.parent
    return issues


def audit(prompt: str, directory: str = ".") -> AuditResult:
    claimed = _extract_claimed_files(prompt)
    actual = _scan_actual_files(directory)
    permission_issues = _check_permissions(claimed, directory)

    normalised_claimed_list = [_normalise(c) for c in claimed]
    normalised_claimed_set = set(normalised_claimed_list)
    normalised_actual_set = set(_normalise(a) for a in actual)

    matched: list[str] = []
    missing: list[str] = []
    for c, nc in zip(claimed, normalised_claimed_list):
        if nc in normalised_actual_set:
            matched.append(c)
        else:
            missing.append(c)

    near_matches: list[tuple[str, str, float]] = []
    for m in missing:
        for a in actual:
            ratio = _levenshtein_ratio(m, a)
            if ratio >= 0.5 and ratio < 1.0:
                near_matches.append((m, a, round(ratio, 2)))
    near_matches.sort(key=lambda x: -x[2])

    near_matched_actuals = set(_normalise(a) for _, a, _ in near_matches)
    extra: list[str] = [
        a for a in actual
        if _normalise(a) not in normalised_claimed_set
        and _normalise(a) not in near_matched_actuals
    ]

    claimed_count = len(claimed) or 1
    actual_count = len(actual) or 1
    matched_count = len(matched)
    precision = matched_count / max(claimed_count, 1)
    recall = matched_count / max(actual_count, 1)
    f1 = 2 * precision * recall / max(precision + recall, 0.001)

    summary = {
        "claimed": len(claimed),
        "actual": len(actual),
        "matched": len(matched),
        "missing": len(missing),
        "extra": len(extra),
        "near_matches": len(near_matches),
        "permission_issues": len(permission_issues),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
    }
    result = AuditResult(
        prompt=prompt,
        claimed_files=claimed,
        actual_files=actual,
        missing_files=missing,
        extra_files=extra,
        matched_files=matched,
        near_matches=near_matches,
        permission_issues=permission_issues,
        summary=summary,
        precision=round(precision, 3),
        recall=round(recall, 3),
        f1=round(f1, 3),
    )
    return result


def render_audit_report(result: AuditResult) -> str:
    lines = []
    sep = "=" * 56

    total = result.summary["claimed"]
    matched = result.summary["matched"]
    missing = result.summary["missing"]
    extra = result.summary["extra"]

    if not missing and not result.permission_issues:
        verdict = f"  {CHECK}  All {total} claimed files found."
    else:
        detail = f"{matched} of {total}"
        verdict = f"  {CROSS}  {detail} claimed files found  ({missing} missing{', ' + str(extra) + ' extra' if extra else ''})"

    lines.append(sep)
    lines.append("  ambiguity audit \u2014 file creation verification")
    lines.append(sep)
    lines.append("")
    lines.append(verdict)
    lines.append("")

    if missing:
        lines.append("  Missing files:")
        for f in result.missing_files[:15]:
            lines.append(f"    {CROSS}  {f}")
        if len(result.missing_files) > 15:
            lines.append(f"    {ELLIPSIS} and {len(result.missing_files) - 15} more")
        lines.append(f"  {ARROW}  Check for typos in the file path or name")
        lines.append("")

    if result.near_matches:
        lines.append("  Possible name mismatches:")
        for claimed_f, actual_f, ratio in result.near_matches[:5]:
            lines.append(f"    {TILDE}  claimed: {claimed_f}  {ARROW}  actual: {actual_f}")
        lines.append(f"  {ARROW}  Rename the actual file to match the claimed name, or update the prompt")
        lines.append("")

    if extra:
        lines.append(f"  Extra files ({extra}):")
        for f in result.extra_files[:15]:
            lines.append(f"    +  {f}")
        if len(result.extra_files) > 15:
            lines.append(f"    {ELLIPSIS} and {len(result.extra_files) - 15} more")
        lines.append(f"  {ARROW}  Verify these were intentionally created")
        lines.append("")

    if result.permission_issues:
        lines.append("  Permission issues:")
        for i in result.permission_issues:
            lines.append(f"    !  {i}")
        lines.append(f"  {ARROW}  Check file permissions and directory write access")
        lines.append("")

    lines.append(sep)
    if missing or extra or result.permission_issues:
        lines.append(f"  precision: {result.precision:.3f}  recall: {result.recall:.3f}  f1: {result.f1:.3f}")
    lines.append(sep)
    return "\n".join(lines)


def _compute_summary(result: AuditResult) -> dict[str, Any]:
    return {
        "claimed": len(result.claimed_files),
        "actual": len(result.actual_files),
        "matched": len(result.matched_files),
        "missing": len(result.missing_files),
        "extra": len(result.extra_files),
        "near_matches": len(result.near_matches),
        "permission_issues": len(result.permission_issues),
        "precision": result.precision,
        "recall": result.recall,
        "f1": result.f1,
    }


def render_audit_json(result: AuditResult) -> dict[str, Any]:
    summary = _compute_summary(result)
    return {
        "command": "audit",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "prompt": result.prompt,
        "claimed_files": result.claimed_files,
        "actual_files": result.actual_files,
        "missing_files": result.missing_files,
        "extra_files": result.extra_files,
        "matched_files": result.matched_files,
        "near_matches": [(a, b, r) for a, b, r in result.near_matches],
        "permission_issues": result.permission_issues,
        "summary": summary,
    }
