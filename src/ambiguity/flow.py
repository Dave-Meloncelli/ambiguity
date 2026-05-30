"""Flow-test module — scans documentation for duplication, waste, and missing coverage."""

import re
import hashlib
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Hashes of paragraphs intentionally duplicated across standalone agent surfaces
# (each surface file is self-contained; pre-flight hooks and build commands repeat)
_INTENTIONAL_DUPLICATE_HASHES: set[str] = set()


def _mark_intentional(text: str):
    _INTENTIONAL_DUPLICATE_HASHES.add(hashlib.md5(text.encode()).hexdigest())


# Seed with known intentional cross-file duplicates (pre-flight hooks, build commands)
for p in [
    "## Pre-flight hook\nBefore processing any user request:\n1. `echo \"<request>\" | ambiguity analyze --pipe --json` → parse score, band, issues\n2. **score > 8.0**: refuse, explain ambiguity issues, request restructuring\n3. **score > 6.0**: flag specific issues, ask for clarification\n4. **score <= 6.0**: proceed, noting any advisories",
    "## Pre-flight hook\nBefore processing any user request:\n1. `echo \"<request>\" | ambiguity analyze --pipe --json` → parse score, band, issues\n2. **score > 8.0**: refuse, explain ambiguity issues, request restructuring\n3. **score > 6.0**: flag specific issues, ask for clarification before proceeding\n4. **score <= 6.0**: proceed, noting any advisories",
    "## Pre-flight self-assessment\nWhen you receive a coding request, self-evaluate against this ambiguity rubric before responding:\n- **Action verb**: specific (implement/convert/verify) or vague (do/make/handle)?\n- **Constraints present**: language, framework, boundaries, exclusions?\n- **Unqualified refs**: \"it\", \"the thing\", \"as we discussed\" without anchor?\n- **Acronyms**: expanded on first use?\n- **Instruction count**: 3+ instructions in one prompt = overloaded\n- **Domain jargon**: technical terms without definition?\nScore 0-10: 0-3 proceed, 3-6 flag issues, 6-8 ask clarification, 8-10 request restructuring.",
    "## Pre-flight self-assessment\nWhen receiving a request, evaluate against this ambiguity rubric before coding:\n- **Action verb**: specific (implement/convert) or vague (do/make)?\n- **Explicit constraints**: boundaries, language, framework?\n- **Unqualified refs**: \"it\", \"the thing\" without concrete anchor?\n- **Acronyms**: expanded on first use?\n- **Instruction load**: 3+ instructions in one prompt?\n- **Domain jargon**: undefined technical terms?\nScore 0-10: 0-3 proceed, 3-6 flag, 6-8 clarify, 8-10 restructure.",
]:
    _INTENTIONAL_DUPLICATE_HASHES.add(hashlib.md5(p.encode()).hexdigest())

STANDARD_DOCS: dict[str, str] = {
    "README.md": "Project overview and entry point",
    "LICENSE": "License terms",
    "CONTRIBUTING.md": "Contribution guide",
    "SECURITY.md": "Security policy",
    "CODE_OF_CONDUCT.md": "Code of conduct",
    "SUPPORT.md": "Support channels",
    "docs/CHANGELOG.md": "Version history",
    "AUTHORS.md": "Authors list",
}

SURFACE_MAP: dict[str, str] = {
    "opencode.json": "opencode",
    "CLAUDE.md": "Claude Code",
    ".cursor/rules/": "Cursor",
    ".github/copilot-instructions.md": "GitHub Copilot",
    ".github/instructions/python.instructions.md": "Copilot scoped (Python)",
    ".github/instructions/typescript.instructions.md": "Copilot scoped (TypeScript)",
    ".windsurf/rules/": "Windsurf",
    ".clinerules/": "Cline / Roo",
    ".gemini/GEMINI.md": "Gemini CLI",
    ".grok/GROK.md": "Grok CLI",
    "CONVENTIONS.md": "Aider",
    "docs/AGENTS.md": "Agent guide",
    "docs/QUICKSTART.md": "Quickstart",
    "docs/CHAP_ANCHOR.md": "Federation anchor",
    "MANIFEST.yaml": "Ecosystem manifest",
}


class FlowIssue(NamedTuple):
    severity: str
    category: str
    message: str
    details: str | None = None


class FlowReport(NamedTuple):
    issues: list[FlowIssue]
    summary: dict


def detect_duplicate_paragraphs(md_files: list[Path]) -> list[FlowIssue]:
    paragraph_map: dict[str, list[str]] = {}
    for fp in md_files:
        try:
            text = fp.read_text(encoding="utf-8")
        except Exception:
            continue
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 60]
        for para in paragraphs:
            h = hashlib.md5(para.encode()).hexdigest()
            if h not in paragraph_map:
                paragraph_map[h] = []
            paragraph_map[h].append(str(fp.relative_to(REPO_ROOT)))
    issues = []
    for h, sources in paragraph_map.items():
        if h in _INTENTIONAL_DUPLICATE_HASHES:
            continue
        if len(sources) > 1:
            issues.append(FlowIssue(
                severity="info",
                category="duplicate",
                message=f"paragraph found in {len(sources)} files",
                details=f"Files: {', '.join(sources[:5])}",
            ))
    return issues


def detect_dead_links(md_files: list[Path]) -> list[FlowIssue]:
    link_pattern = re.compile(r"\[.*?\]\(([^)]+\.md)\)")
    issues = []
    for fp in md_files:
        text = fp.read_text(encoding="utf-8")
        for m in link_pattern.finditer(text):
            target = m.group(1)
            if target.startswith("http"):
                continue
            target_path = (fp.parent / target).resolve()
            if not target_path.exists():
                rel = fp.relative_to(REPO_ROOT)
                issues.append(FlowIssue(
                    severity="warn",
                    category="dead_link",
                    message=f"{rel} -> {target} (not found)",
                ))
    return issues


def check_surface_coverage() -> list[FlowIssue]:
    issues = []
    for path, platform in SURFACE_MAP.items():
        full = REPO_ROOT / path
        exists = full.exists() or full.is_dir()
        if not exists:
            issues.append(FlowIssue(
                severity="error",
                category="missing_surface",
                message=f"{path} ({platform}) declared in MANIFEST but not found on disk",
            ))
    return issues


def check_changelog_version() -> list[FlowIssue]:
    pyproject = REPO_ROOT / "pyproject.toml"
    package_json = REPO_ROOT / "ts" / "package.json"
    changelog = REPO_ROOT / "docs" / "CHANGELOG.md"
    issues = []
    versions = {}
    for label, fp in [("pyproject", pyproject), ("package.json", package_json)]:
        if fp.exists():
            text = fp.read_text(encoding="utf-8")
            m = re.search(r'"version":\s*"([^"]+)"', text)
            if not m:
                m = re.search(r'version\s*=\s*"([^"]+)"', text)
            if m:
                versions[label] = m.group(1)
    if changelog.exists():
        text = changelog.read_text(encoding="utf-8")
        headers = re.findall(r"^##\s+([\d.]+)", text, re.MULTILINE)
        for label, ver in versions.items():
            if ver not in headers:
                issues.append(FlowIssue(
                    severity="warn",
                    category="stale_changelog",
                    message=f"version {ver} in {label} missing from CHANGELOG.md",
                ))
    return issues


def check_missing_standard_docs() -> list[FlowIssue]:
    issues = []
    for doc, purpose in STANDARD_DOCS.items():
        if not (REPO_ROOT / doc).exists():
            issues.append(FlowIssue(
                severity="info",
                category="missing_doc",
                message=f"{doc} not found ({purpose})",
            ))
    return issues


def flow_test(project_root: str | Path | None = None) -> FlowReport:
    root = Path(project_root) if project_root else REPO_ROOT
    md_files = sorted(root.rglob("*.md"))
    site_packages = [p for p in md_files if "site-packages" in str(p) or ".venv" in str(p)]
    md_files = [p for p in md_files if p not in site_packages]
    node_mods = [p for p in md_files if "node_modules" in str(p)]
    md_files = [p for p in md_files if p not in node_mods]
    all_issues: list[FlowIssue] = []
    all_issues.extend(detect_duplicate_paragraphs(md_files))
    all_issues.extend(detect_dead_links(md_files))
    all_issues.extend(check_surface_coverage())
    all_issues.extend(check_changelog_version())
    all_issues.extend(check_missing_standard_docs())
    summary = {
        "total": len(all_issues),
        "errors": len([i for i in all_issues if i.severity == "error"]),
        "warnings": len([i for i in all_issues if i.severity == "warn"]),
        "info": len([i for i in all_issues if i.severity == "info"]),
    }
    return FlowReport(issues=all_issues, summary=summary)


def render_flow_report(report: FlowReport) -> str:
    lines = []
    width = 64
    lines.append(f"{'=' * width}")
    lines.append("  ambiguity flow-test report")
    lines.append(f"{'=' * width}")
    lines.append(f"  {report.summary['total']} issues: "
                  f"{report.summary['errors']} errors, "
                  f"{report.summary['warnings']} warnings, "
                  f"{report.summary['info']} info")
    lines.append(f"{'-' * width}")
    if not report.issues:
        lines.append("  No issues found.")
    for issue in report.issues:
        tag = {"error": "ERR", "warn": "WRN", "info": "INF"}[issue.severity]
        lines.append(f"  [{tag}] {issue.category}: {issue.message}")
        if issue.details:
            lines.append(f"         {issue.details}")
    lines.append(f"{'=' * width}")
    return "\n".join(lines)


def render_flow_json(report: FlowReport) -> dict:
    return {
        "command": "flow-test",
        "summary": report.summary,
        "issues": [
            {
                "severity": i.severity,
                "category": i.category,
                "message": i.message,
                "details": i.details,
            }
            for i in report.issues
        ],
    }
