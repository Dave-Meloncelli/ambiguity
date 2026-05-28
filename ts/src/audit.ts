import { readdirSync, statSync } from "node:fs"
import { resolve, relative } from "node:path"

const FILE_REF_PATTERN = /(?:^|\s)(?:`)?((?:[\w.-]+\/)*[\w.-]+\.\w+)(?:`)?(?=\s|$|[.,;!?])/gm
const EXTRA_IGNORE = new Set([".git", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"])

export interface NearMatch {
  claimed: string
  found: string
  similarity: number
}

export interface AuditResult {
  prompt: string
  claimedFiles: string[]
  actualFiles: string[]
  missingFiles: string[]
  extraFiles: string[]
  matchedFiles: string[]
  nearMatches: NearMatch[]
  permissionIssues: string[]
  summary: Record<string, number>
  error?: string
  precision: number
  recall: number
  f1: number
}

function normalise(path: string): string {
  return path.replace(/\\/g, "/").toLowerCase()
}

function levenshteinRatio(a: string, b: string): number {
  if (!a || !b) return 0
  a = a.toLowerCase()
  b = b.toLowerCase()
  const n = a.length
  const m = b.length
  const dp: number[][] = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0))
  for (let i = 0; i <= n; i++) dp[i][0] = i
  for (let j = 0; j <= m; j++) dp[0][j] = j
  for (let i = 1; i <= n; i++) {
    for (let j = 1; j <= m; j++) {
      dp[i][j] = Math.min(
        dp[i - 1][j] + 1,
        dp[i][j - 1] + 1,
        dp[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1),
      )
    }
  }
  return 1 - dp[n][m] / Math.max(n, m)
}

function extractClaimedFiles(prompt: string): string[] {
  const seen = new Set<string>()
  const files: string[] = []
  let m: RegExpExecArray | null
  FILE_REF_PATTERN.lastIndex = 0
  while ((m = FILE_REF_PATTERN.exec(prompt)) !== null) {
    const p = m[1]
    if (!seen.has(p) && !p.startsWith("http://") && !p.startsWith("https://") && !p.startsWith("www.")) {
      seen.add(p)
      files.push(p)
    }
  }
  return files
}

function scanActualFiles(directory: string): string[] {
  const base = resolve(directory)
  const files: string[] = []

  function walk(dir: string): void {
    let entries: string[]
    try {
      entries = readdirSync(dir)
    } catch {
      return
    }
    for (const entry of entries) {
      const abs = resolve(dir, entry)
      try {
        const s = statSync(abs)
        const rel = relative(base, abs).replace(/\\/g, "/")
        const parts = rel.split("/")
        if (parts.some((p) => EXTRA_IGNORE.has(p))) continue
        if (s.isFile()) {
          files.push(rel)
        } else if (s.isDirectory()) {
          walk(abs)
        }
      } catch {
        // skip unreadable
      }
    }
  }

  walk(base)
  return files.sort()
}

export function audit(prompt: string, directory = "."): AuditResult {
  const claimed = extractClaimedFiles(prompt)
  const actual = scanActualFiles(directory)

  const normalisedClaimed = claimed.map(normalise)
  const normalisedClaimedSet = new Set(normalisedClaimed)
  const normalisedActualSet = new Set(actual.map(normalise))

  const matched: string[] = []
  const missing: string[] = []
  for (let i = 0; i < claimed.length; i++) {
    if (normalisedActualSet.has(normalisedClaimed[i])) {
      matched.push(claimed[i])
    } else {
      missing.push(claimed[i])
    }
  }

  const nearMatches: NearMatch[] = []
  for (const m of missing) {
    for (const a of actual) {
      const r = levenshteinRatio(m, a)
      if (r >= 0.5 && r < 1.0) {
        nearMatches.push({ claimed: m, found: a, similarity: Math.round(r * 100) / 100 })
      }
    }
  }
  nearMatches.sort((a, b) => b.similarity - a.similarity)

  const nearActuals = new Set(nearMatches.map((nm) => normalise(nm.found)))
  const extra = actual.filter((a) => !normalisedClaimedSet.has(normalise(a)) && !nearActuals.has(normalise(a)))

  const claimedCount = claimed.length || 1
  const actualCount = actual.length || 1
  const precision = matched.length / claimedCount
  const recall = matched.length / actualCount
  const f1 = (2 * precision * recall) / Math.max(precision + recall, 0.001)

  const rPrecision = Math.round(precision * 1000) / 1000
  const rRecall = Math.round(recall * 1000) / 1000
  const rF1 = Math.round(f1 * 1000) / 1000

  return {
    prompt,
    claimedFiles: claimed,
    actualFiles: actual,
    missingFiles: missing,
    extraFiles: extra,
    matchedFiles: matched,
    nearMatches,
    permissionIssues: [],
    summary: {
      claimed: claimed.length,
      actual: actual.length,
      matched: matched.length,
      missing: missing.length,
      extra: extra.length,
      nearMatches: nearMatches.length,
      permissionIssues: 0,
      precision: rPrecision,
      recall: rRecall,
      f1: rF1,
    },
    precision: rPrecision,
    recall: rRecall,
    f1: rF1,
  }
}

export function renderAuditReport(result: AuditResult): string {
  const CHECK = "\u2713"
  const CROSS = "\u2717"
  const ARROW = "\u2192"
  const ELLIPSIS = "\u2026"
  const TILDE = "~"
  const sep = "=".repeat(56)

  const lines: string[] = []
  const total = result.summary.claimed
  const matched = result.summary.matched
  const missing = result.summary.missing
  const extra = result.summary.extra

  let verdict: string
  if (!missing && result.permissionIssues.length === 0) {
    verdict = `  ${CHECK}  All ${total} claimed files found.`
  } else {
    verdict = `  ${CROSS}  ${matched} of ${total} claimed files found  (${missing} missing${extra ? ", " + extra + " extra" : ""})`
  }

  lines.push(sep)
  lines.push("  ambiguity audit \u2014 file creation verification")
  lines.push(sep)
  lines.push("")
  lines.push(verdict)
  lines.push("")

  if (missing > 0) {
    lines.push("  Missing files:")
    for (const f of result.missingFiles.slice(0, 15)) {
      lines.push(`    ${CROSS}  ${f}`)
    }
    if (result.missingFiles.length > 15) {
      lines.push(`    ${ELLIPSIS} and ${result.missingFiles.length - 15} more`)
    }
    lines.push(`  ${ARROW}  Check for typos in the file path or name`)
    lines.push("")
  }

  if (result.nearMatches.length > 0) {
    lines.push("  Possible name mismatches:")
    for (const nm of result.nearMatches.slice(0, 5)) {
      lines.push(`    ${TILDE}  claimed: ${nm.claimed}  ${ARROW}  actual: ${nm.found}`)
    }
    lines.push(`  ${ARROW}  Rename the actual file to match the claimed name, or update the prompt`)
    lines.push("")
  }

  if (extra > 0) {
    lines.push(`  Extra files (${extra}):`)
    for (const f of result.extraFiles.slice(0, 15)) {
      lines.push(`    +  ${f}`)
    }
    if (result.extraFiles.length > 15) {
      lines.push(`    ${ELLIPSIS} and ${result.extraFiles.length - 15} more`)
    }
    lines.push(`  ${ARROW}  Verify these were intentionally created`)
    lines.push("")
  }

  if (result.permissionIssues.length > 0) {
    lines.push("  Permission issues:")
    for (const i of result.permissionIssues) {
      lines.push(`    !  ${i}`)
    }
    lines.push(`  ${ARROW}  Check file permissions and directory write access`)
    lines.push("")
  }

  lines.push(sep)
  if (missing || extra || result.permissionIssues.length) {
    lines.push(`  precision: ${result.precision.toFixed(3)}  recall: ${result.recall.toFixed(3)}  f1: ${result.f1.toFixed(3)}`)
  }
  lines.push(sep)
  return lines.join("\n")
}
