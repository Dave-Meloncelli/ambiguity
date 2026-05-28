import * as fs from "fs"
import * as path from "path"
import * as crypto from "crypto"

export interface FlowIssue {
  type: string
  file: string
  detail: string
}

export interface FlowTestResult {
  issues: FlowIssue[]
  passed: boolean
  summary: string
}

const INTENTIONAL_DUPLICATE_HASHES = new Set<string>()

const INTENTIONAL_PARAS = [
  "## Pre-flight hook\nBefore processing any user request:\n1. `echo \"<request>\" | ambiguity analyze --pipe --json` → parse score, band, issues\n2. **score > 8.0**: refuse, explain ambiguity issues, request restructuring\n3. **score > 6.0**: flag specific issues, ask for clarification\n4. **score <= 6.0**: proceed, noting any advisories",
  "## Pre-flight hook\nBefore processing any user request:\n1. `echo \"<request>\" | ambiguity analyze --pipe --json` → parse score, band, issues\n2. **score > 8.0**: refuse, explain ambiguity issues, request restructuring\n3. **score > 6.0**: flag specific issues, ask for clarification before proceeding\n4. **score <= 6.0**: proceed, noting any advisories",
  "## Pre-flight self-assessment\nWhen you receive a coding request, self-evaluate against this ambiguity rubric before responding:\n- **Action verb**: specific (implement/convert/verify) or vague (do/make/handle)?\n- **Constraints present**: language, framework, boundaries, exclusions?\n- **Unqualified refs**: \"it\", \"the thing\", \"as we discussed\" without anchor?\n- **Acronyms**: expanded on first use?\n- **Instruction count**: 3+ instructions in one prompt = overloaded\n- **Domain jargon**: technical terms without definition?\nScore 0-10: 0-3 proceed, 3-6 flag issues, 6-8 ask clarification, 8-10 request restructuring.",
  "## Pre-flight self-assessment\nWhen receiving a request, evaluate against this ambiguity rubric before coding:\n- **Action verb**: specific (implement/convert) or vague (do/make)?\n- **Explicit constraints**: boundaries, language, framework?\n- **Unqualified refs**: \"it\", \"the thing\" without concrete anchor?\n- **Acronyms**: expanded on first use?\n- **Instruction load**: 3+ instructions in one prompt?\n- **Domain jargon**: undefined technical terms?\nScore 0-10: 0-3 proceed, 3-6 flag, 6-8 clarify, 8-10 restructure.",
]

for (const p of INTENTIONAL_PARAS) {
  INTENTIONAL_DUPLICATE_HASHES.add(crypto.createHash("md5").update(p).digest("hex"))
}

const STANDARD_DOCS: Record<string, string> = {
  "README.md": "Project overview and entry point",
  "LICENSE": "License terms",
  "CONTRIBUTING.md": "Contribution guide",
  "SECURITY.md": "Security policy",
  "CODE_OF_CONDUCT.md": "Code of conduct",
  "SUPPORT.md": "Support channels",
  "docs/CHANGELOG.md": "Version history",
  "AUTHORS.md": "Authors list",
}

const SURFACE_MAP: Record<string, string> = {
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

function collectMdFiles(root: string): string[] {
  const files: string[] = []
  function walk(dir: string): void {
    let entries: fs.Dirent[]
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true })
    } catch {
      return
    }
    for (const entry of entries) {
      if (entry.name.startsWith(".")) continue
      const full = path.join(dir, entry.name)
      if (entry.isDirectory()) {
        if (entry.name === "node_modules" || entry.name === ".venv" || entry.name === "site-packages") continue
        walk(full)
      } else if (entry.name.endsWith(".md")) {
        files.push(full)
      }
    }
  }
  walk(root)
  return files.sort()
}

function detectDuplicateParagraphs(mdFiles: string[]): FlowIssue[] {
  const paragraphMap = new Map<string, string[]>()
  for (const fp of mdFiles) {
    let text: string
    try {
      text = fs.readFileSync(fp, "utf-8")
    } catch {
      continue
    }
    const paragraphs = text.split(/\n\n/).filter(p => p.trim().length > 60)
    for (const para of paragraphs) {
      const h = crypto.createHash("md5").update(para.trim()).digest("hex")
      if (!paragraphMap.has(h)) {
        paragraphMap.set(h, [])
      }
      paragraphMap.get(h)!.push(fp)
    }
  }
  const issues: FlowIssue[] = []
  for (const [h, sources] of paragraphMap) {
    if (INTENTIONAL_DUPLICATE_HASHES.has(h)) continue
    if (sources.length > 1) {
      issues.push({
        type: "duplicate",
        file: sources[0],
        detail: `paragraph found in ${sources.length} files: ${sources.slice(0, 5).join(", ")}`,
      })
    }
  }
  return issues
}

function detectDeadLinks(mdFiles: string[]): FlowIssue[] {
  const linkPattern = /\[.*?\]\(([^)]+\.md)\)/g
  const issues: FlowIssue[] = []
  for (const fp of mdFiles) {
    let text: string
    try {
      text = fs.readFileSync(fp, "utf-8")
    } catch {
      continue
    }
    let m: RegExpExecArray | null
    while ((m = linkPattern.exec(text)) !== null) {
      const target = m[1]
      if (target.startsWith("http")) continue
      const targetPath = path.resolve(path.dirname(fp), target)
      if (!fs.existsSync(targetPath)) {
        issues.push({
          type: "dead_link",
          file: fp,
          detail: `${fp} -> ${target} (not found)`,
        })
      }
    }
  }
  return issues
}

function checkSurfaceCoverage(root: string): FlowIssue[] {
  const issues: FlowIssue[] = []
  for (const [p, platform] of Object.entries(SURFACE_MAP)) {
    const full = path.join(root, p)
    if (!fs.existsSync(full)) {
      issues.push({
        type: "missing_surface",
        file: p,
        detail: `${p} (${platform}) declared but not found on disk`,
      })
    }
  }
  return issues
}

function checkChangelogVersion(root: string): FlowIssue[] {
  const changelog = path.join(root, "docs", "CHANGELOG.md")
  const issues: FlowIssue[] = []
  const versions: Record<string, string> = {}

  const pyproject = path.join(root, "pyproject.toml")
  if (fs.existsSync(pyproject)) {
    const text = fs.readFileSync(pyproject, "utf-8")
    const m = text.match(/version\s*=\s*"([^"]+)"/)
    if (m) versions["pyproject"] = m[1]
  }

  const tsPackage = path.join(root, "ts", "package.json")
  if (fs.existsSync(tsPackage)) {
    const text = fs.readFileSync(tsPackage, "utf-8")
    const m = text.match(/"version":\s*"([^"]+)"/)
    if (m) versions["package.json"] = m[1]
  }

  if (fs.existsSync(changelog)) {
    const text = fs.readFileSync(changelog, "utf-8")
    const headers = text.match(/^##\s+([\d.]+)/gm) ?? []
    for (const [label, ver] of Object.entries(versions)) {
      if (!headers.some(h => h.includes(ver))) {
        issues.push({
          type: "stale_changelog",
          file: label,
          detail: `version ${ver} in ${label} missing from CHANGELOG.md`,
        })
      }
    }
  }
  return issues
}

function checkMissingStandardDocs(root: string): FlowIssue[] {
  const issues: FlowIssue[] = []
  for (const [doc, purpose] of Object.entries(STANDARD_DOCS)) {
    if (!fs.existsSync(path.join(root, doc))) {
      issues.push({
        type: "missing_doc",
        file: doc,
        detail: `${doc} not found (${purpose})`,
      })
    }
  }
  return issues
}

export function flowTest(projectRoot?: string): FlowTestResult {
  const root = projectRoot ?? process.cwd()
  const allIssues: FlowIssue[] = []
  const mdFiles = collectMdFiles(root)
  allIssues.push(...detectDuplicateParagraphs(mdFiles))
  allIssues.push(...detectDeadLinks(mdFiles))
  allIssues.push(...checkSurfaceCoverage(root))
  allIssues.push(...checkChangelogVersion(root))
  allIssues.push(...checkMissingStandardDocs(root))
  const passed = allIssues.length === 0
  return { issues: allIssues, passed, summary: `${allIssues.length} issues found` }
}

export function renderFlowReport(result: FlowTestResult): string {
  const width = 64
  const lines: string[] = []
  lines.push("=".repeat(width))
  lines.push("  ambiguity flow-test report")
  lines.push("=".repeat(width))
  lines.push(`  ${result.issues.length} issues`)
  lines.push("-".repeat(width))
  if (result.issues.length === 0) {
    lines.push("  No issues found.")
  }
  for (const issue of result.issues) {
    lines.push(`  [${issue.type}] ${issue.detail}`)
  }
  lines.push("=".repeat(width))
  return lines.join("\n")
}
