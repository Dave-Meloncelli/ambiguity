import { createHash } from "node:crypto"
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs"
import { extname, resolve } from "node:path"

const HARNESS_PATHS: Record<string, string[]> = {
  "Claude Code": ["~/.claude/logs", "~/.claude/projects"],
  Cursor: ["~/.cursor/logs", "~/.cursor/sessions"],
  Windsurf: ["~/.windsurf/logs"],
  opencode: ["~/.config/opencode/logs"],
  Cline: ["~/.config/cline/logs"],
  Roo: ["~/.config/roo/logs"],
  "Gemini CLI": ["~/.gemini/logs"],
  "Grok CLI": ["~/.grok/logs"],
}

export interface SamplePrompt {
  harness: string
  preview: string
}

export interface ImportResult {
  sourcesScanned: number
  promptsFound: number
  samplePrompts: SamplePrompt[]
  errors: string[]
}

function expandPath(p: string): string | null {
  const home = process.env.HOME || process.env.USERPROFILE || ""
  const expanded = p.replace(/^~/, home)
  return existsSync(expanded) ? expanded : null
}

function scanJsonFile(fp: string): string[] {
  const prompts: string[] = []
  let data: unknown
  try {
    const raw = readFileSync(fp, "utf-8")
    data = JSON.parse(raw)
  } catch {
    return prompts
  }

  const obj = data as Record<string, unknown> | undefined
  const messages: unknown[] = Array.isArray(data)
    ? data
    : ((obj?.messages ?? obj?.conversation ?? obj?.chat) ?? []) as unknown[]

  if (!Array.isArray(messages)) return prompts

  for (const msg of messages) {
    if (typeof msg !== "object" || msg === null) continue
    const record = msg as Record<string, unknown>

    const role = String(record.role ?? "").toLowerCase()
    if (role !== "user") continue

    const content = record.content
    if (typeof content === "string" && content.length > 10) {
      prompts.push(content)
    } else if (Array.isArray(content)) {
      for (const block of content) {
        if (typeof block === "object" && block !== null) {
          const b = block as Record<string, unknown>
          if (b.type === "text" && typeof b.text === "string" && b.text.length > 10) {
            prompts.push(b.text)
          }
        }
      }
    }
  }

  return prompts
}

function walkJsonFiles(dir: string): string[] {
  const files: string[] = []
  let entries: string[]
  try {
    entries = readdirSync(dir)
  } catch {
    return files
  }
  for (const entry of entries) {
    const full = resolve(dir, entry)
    try {
      const s = statSync(full)
      if (s.isDirectory()) {
        files.push(...walkJsonFiles(full))
      } else if (s.isFile()) {
        const ext = extname(full).toLowerCase()
        if (ext === ".json" || ext === ".jsonl" || ext === ".ndjson") {
          files.push(full)
        }
      }
    } catch {
      // skip
    }
  }
  return files
}

export function renderImportReport(result: ImportResult): string {
  const sep = "=".repeat(56)
  const lines: string[] = [sep]
  lines.push("  ambiguity import — prompt history discovery")
  lines.push(sep)
  lines.push("")

  if (result.sourcesScanned === 0) {
    lines.push("  No consent given. Run with --consent to scan.")
    lines.push(sep)
    return lines.join("\n")
  }

  lines.push(`  Harness directories scanned: ${result.sourcesScanned}`)
  lines.push(`  Unique prompts found:        ${result.promptsFound}`)
  lines.push("")

  if (result.samplePrompts.length > 0) {
    lines.push("  Sample prompts found:")
    for (const sp of result.samplePrompts.slice(0, 3)) {
      const short = sp.preview.slice(0, 60)
      lines.push(`    [${sp.harness}] ${short}...`)
    }
    lines.push("")
  }

  if (result.errors.length > 0) {
    lines.push("  Warnings:")
    for (const e of result.errors.slice(0, 3)) {
      lines.push(`    ! ${e}`)
    }
    lines.push("")
  }

  lines.push(sep)
  return lines.join("\n")
}

export function renderImportJson(result: ImportResult): Record<string, unknown> {
  return {
    command: "import",
    sources_scanned: result.sourcesScanned,
    prompts_found: result.promptsFound,
    errors: result.errors,
    sample_prompts: result.samplePrompts.slice(0, 5).map((sp) => ({
      harness: sp.harness,
      preview: sp.preview,
    })),
  }
}

export function discover(consent = false, dryRun = true): ImportResult {
  const result: ImportResult = { sourcesScanned: 0, promptsFound: 0, samplePrompts: [], errors: [] }

  if (!consent) {
    result.errors.push("Consent not given — no paths scanned")
    return result
  }

  const seenHashes = new Set<string>()
  const allPrompts: { harness: string; text: string }[] = []

  for (const [harness, paths] of Object.entries(HARNESS_PATHS)) {
    for (const p of paths) {
      const resolved = expandPath(p)
      if (!resolved) continue
      result.sourcesScanned++

      const jsonFiles = walkJsonFiles(resolved)
      for (const fp of jsonFiles) {
        try {
          if (statSync(fp).size > 5_000_000) continue
        } catch {
          continue
        }
        const prompts = scanJsonFile(fp)
        for (const text of prompts) {
          const h = createHash("md5").update(text, "utf-8").digest("hex").slice(0, 8)
          if (seenHashes.has(h)) continue
          seenHashes.add(h)
          allPrompts.push({ harness, text })
          result.promptsFound++
        }
      }
    }
  }

  result.samplePrompts = allPrompts.slice(0, 5).map((p) => ({
    harness: p.harness,
    preview: p.text.replace(/\n/g, " ").slice(0, 100),
  }))

  return result
}
