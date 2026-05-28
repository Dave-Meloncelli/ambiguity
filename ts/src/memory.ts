import { createHash } from "node:crypto"
import { existsSync, readFileSync, writeFileSync } from "node:fs"
import { resolve } from "node:path"

const MEMORY_PATH = "docs/memory.md"

export interface ChangeRecord {
  type: string
  original: string
  replacement: string
}

export interface MemoryEntry {
  date: string
  prompt: string
  hash: string
  score: number
  band: string
  action: string
  changes?: ChangeRecord[]
  outcome: string
  note?: string
}

function findMemory(): string | null {
  let dir = process.cwd()
  for (;;) {
    const candidate = resolve(dir, MEMORY_PATH)
    if (existsSync(candidate)) return candidate
    const parent = resolve(dir, "..")
    if (parent === dir) return null
    dir = parent
  }
}

function promptHash(prompt: string): string {
  return createHash("md5").update(prompt, "utf-8").digest("hex").slice(0, 8)
}

function formatEntry(
  prompt: string,
  hash: string,
  score: number,
  band: string,
  action: string,
  outcome: string,
  note: string,
  changes?: ChangeRecord[],
): string {
  const date = new Date().toISOString().replace(/\.\d{3}Z$/, "Z")

  let changesStr = ""
  if (changes && changes.length > 0) {
    const items = changes.map((c) => {
      const orig = c.original.replace(/"/g, "'")
      const repl = c.replacement.replace(/\n/g, " ").replace(/"/g, "'").slice(0, 60)
      return `      - type: ${c.type}\n        original: "${orig}"\n        replacement: "${repl}"`
    })
    changesStr = "    changes:\n" + items.join("\n") + "\n"
  }

  const noteStr = note ? `    note: "${note}"\n` : ""

  return (
    `- date: ${date}\n` +
    `  prompt: "${prompt.slice(0, 80)}"\n` +
    `  hash: ${hash}\n` +
    `  score: ${score.toFixed(1)}\n` +
    `  band: ${band}\n` +
    `  action: ${action}\n` +
    changesStr +
    `  outcome: ${outcome}\n` +
    noteStr
  )
}

export function writeEntry(
  prompt: string,
  action = "none",
  changes?: ChangeRecord[],
  outcome = "accepted",
  note = "",
  score = 0,
  band = "",
): string | null {
  const memPath = findMemory()
  if (!memPath) return null

  const hash = promptHash(prompt)
  const entry = formatEntry(prompt, hash, score, band, action, outcome, note, changes)

  let existing = ""
  try {
    existing = readFileSync(memPath, "utf-8")
  } catch {
    // file doesn't exist yet
  }

  if (!existing.includes("## Entries")) {
    existing += "\n## Entries\n\n"
  }

  const marker = "## Entries"
  const idx = existing.lastIndexOf(marker)
  if (idx === -1) {
    existing += entry + "\n"
  } else {
    existing = existing.slice(0, idx) + marker + "\n\n" + entry + existing.slice(idx + marker.length)
  }

  writeFileSync(memPath, existing, "utf-8")
  return memPath
}

export function readEntries(count = 5): MemoryEntry[] {
  const memPath = findMemory()
  if (!memPath) return []

  let text: string
  try {
    text = readFileSync(memPath, "utf-8")
  } catch {
    return []
  }

  const marker = "## Entries"
  let idx = text.indexOf(marker)
  if (idx === -1) return []
  text = text.slice(idx + marker.length)

  const entries: MemoryEntry[] = []
  let current: Partial<MemoryEntry> = {}

  for (const raw of text.split("\n")) {
    const line = raw.trim()
    if (line.startsWith("- date:")) {
      if (current.date) entries.push(current as MemoryEntry)
      current = { date: line.split(":").slice(1).join(":").trim(), score: 0, band: "" }
    } else if (line.startsWith("prompt:") && current.date) {
      current.prompt = line.split(":").slice(1).join(":").trim().replace(/^"/, "").replace(/"$/, "")
    } else if (line.startsWith("hash:") && current.date) {
      current.hash = line.split(":").slice(1).join(":").trim()
    } else if (line.startsWith("score:") && current.date) {
      current.score = parseFloat(line.split(":").slice(1).join(":").trim()) || 0
    } else if (line.startsWith("band:") && current.date) {
      current.band = line.split(":").slice(1).join(":").trim()
    } else if (line.startsWith("action:") && current.date) {
      current.action = line.split(":").slice(1).join(":").trim()
    } else if (line.startsWith("outcome:") && current.date) {
      current.outcome = line.split(":").slice(1).join(":").trim()
    } else if (line.startsWith("note:") && current.date) {
      current.note = line.split(":").slice(1).join(":").trim().replace(/^"/, "").replace(/"$/, "")
    }
  }
  if (current.date) entries.push(current as MemoryEntry)

  return entries.slice(-count)
}

export function summary(): string {
  const entries = readEntries(20)
  if (entries.length === 0) return "No interactions logged yet."

  const lines = [`Last ${entries.length} interaction(s):`]
  for (const e of entries) {
    const score = e.score
    const action = e.action ?? "?"
    const prompt = (e.prompt ?? "?").slice(0, 50)
    lines.push(`  [${score}/10] ${action}: ${prompt}`)
  }
  return lines.join("\n")
}
