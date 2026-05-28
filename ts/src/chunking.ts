const PHRASAL_VERBS: Record<string, string[]> = {
  set: ["up", "down", "out", "forth", "aside"],
  tear: ["down", "apart", "up"],
  break: ["down", "up", "apart", "out", "into"],
  carry: ["out", "on", "through", "forward"],
  take: ["on", "over", "up", "out", "apart"],
  put: ["together", "aside", "off", "on", "forward"],
  turn: ["on", "off", "up", "down", "into"],
  bring: ["up", "in", "on", "together", "about"],
  come: ["up", "in", "on", "across", "apart"],
  go: ["through", "over", "ahead", "forward", "back"],
  look: ["into", "over", "up", "through", "for"],
  point: ["out", "to", "at"],
  figure: ["out"],
  find: ["out", "a way"],
  run: ["through", "on", "over"],
  move: ["forward", "on", "ahead"],
  back: ["up", "off", "away", "out"],
  call: ["out", "up", "on", "for"],
  map: ["out", "to"],
  scope: ["out", "down"],
  roll: ["out", "up", "back"],
  reach: ["out", "in"],
  follow: ["up", "through", "on"],
  wire: ["up", "together"],
  hook: ["up", "in", "together"],
  build: ["out", "up", "on", "upon"],
  clean: ["up", "out", "off"],
  cut: ["down", "off", "out", "up"],
  phase: ["out", "in"],
  scale: ["up", "down", "out"],
  spin: ["up", "out", "off"],
  stand: ["up", "by"],
  start: ["up", "out", "over"],
  step: ["up", "back", "through", "aside"],
  strip: ["out", "down"],
  sum: ["up"],
  tie: ["together", "in", "into"],
  try: ["out", "on"],
  use: ["up"],
  write: ["out", "up", "down", "off"],
  zero: ["in"],
}

const CLAUSE_BOUNDARIES: string[] = [
  "\\band\\b(?!\\s+then\\b)",
  "\\bbut\\b",
  "\\bor\\b",
  "\\bso that\\b",
  "\\bsuch that\\b",
  "\\bprovided that\\b",
  "\\bhowever\\b",
  "\\btherefore\\b",
  "\\bthen\\b",
  "\\bnext\\b",
  "\\bafterwards\\b",
  "\\bmeanwhile\\b",
  "\\badditionally\\b",
  "\\bfurthermore\\b",
  "\\bmoreover\\b",
  "\\balso\\b",
  "\\bconversely\\b",
  "\\balternatively\\b",
  "\\botherwise\\b",
  "\\bfinally\\b",
  "\\bsubsequently\\b",
  "\\bconsequently\\b",
  "\\bas a result\\b",
]

const TOPIC_SHIFT_MARKERS: string[] = [
  "\\bnow\\b",
  "\\bok[ay]*,?\\s",
  "\\balright,?\\s",
  "\\bso,?\\s",
  "\\bright,?\\s",
  "\\bfirst(ly)?\\b",
  "\\bsecond(ly)?\\b",
  "\\bthird(ly)?\\b",
  "\\bfinally\\b",
  "\\blast(ly)?\\b",
  "\\bin addition\\b",
  "\\bon the other hand\\b",
  "\\bmeanwhile\\b",
  "\\bmoving on\\b",
  "\\bnext up\\b",
]

const CONTRADICTION_MARKERS: RegExp[] = [
  /\b(but|however|although|though|while|whereas|conversely|nevertheless|on the other hand)\b/i,
  /\b(yet|still|instead|rather|otherwise|alternatively)\b/i,
  /\b(must|required|essential)\b.*\b(but|however|although)\b/i,
  /\b(only|exactly|strictly)\b.*\b(also|additionally|furthermore)\b/i,
]

export interface Clause {
  text: string
  verbs: string[]
  constraints: string[]
  has_negation: boolean
  has_hedging: boolean
  has_emphasis: boolean
}

export interface CompoundVerb {
  verb: string
  particle: string
  full: string
  position: number
}

export interface ChunkResult {
  text: string
  clauses: Clause[]
  compound_verbs: CompoundVerb[]
  topic_shifts: number
  contradiction_hits: string[]
  clause_indicators: string[]
}

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
}

function _splitClauses(text: string): string[] {
  const sentences = text.split(/[.!?]+/)
  const result: string[] = []
  const boundaryPattern = "(" + CLAUSE_BOUNDARIES.join("|") + ")"
  const re = new RegExp(boundaryPattern)

  for (let raw of sentences) {
    raw = raw.trim()
    if (!raw) continue
    const parts = raw.split(new RegExp(boundaryPattern))
    let current = ""
    for (const part of parts) {
      if (part && part.trim()) {
        current += part + " "
        if (CLAUSE_BOUNDARIES.some((p) => new RegExp(p).test(part.trim()))) {
          if (current.trim()) {
            result.push(current.trim())
          }
          current = ""
        }
      }
    }
    if (current.trim()) {
      result.push(current.trim())
    }
  }
  return result
}

function _detectCompoundVerbs(tokens: string[]): CompoundVerb[] {
  const found: CompoundVerb[] = []
  for (let i = 0; i < tokens.length; i++) {
    const low = tokens[i].toLowerCase()
    const particles = PHRASAL_VERBS[low]
    if (particles && i + 1 < tokens.length) {
      const nextToken = tokens[i + 1].toLowerCase().replace(/[.!;,]+$/, "")
      if (particles.includes(nextToken)) {
        found.push({
          verb: low,
          particle: nextToken,
          full: `${low}_${nextToken}`,
          position: i,
        })
      }
    }
  }
  return found
}

function _detectContradictions(clauses: Clause[]): string[] {
  const hits = new Set<string>()
  for (let i = 0; i < clauses.length; i++) {
    for (const pattern of CONTRADICTION_MARKERS) {
      if (pattern.test(clauses[i].text)) {
        for (let j = i + 1; j < clauses.length; j++) {
          if (clauses[i].has_negation && clauses[j].has_emphasis) {
            hits.add(`clause ${i + 1} (negation) vs clause ${j + 1} (emphasis)`)
          } else if (clauses[i].has_emphasis && clauses[j].has_negation) {
            hits.add(`clause ${i + 1} (emphasis) vs clause ${j + 1} (negation)`)
          }
        }
      }
    }
  }
  return [...hits]
}

function _countTopicShifts(clauses: Clause[]): number {
  let count = 0
  for (const clause of clauses) {
    for (const marker of TOPIC_SHIFT_MARKERS) {
      if (new RegExp(marker, "i").test(clause.text)) {
        count++
      }
    }
  }
  return count
}

function _detectVerbsInClause(clauseText: string, knownVerbs: Set<string>): string[] {
  const lower = clauseText.toLowerCase()
  const found: string[] = []
  for (const v of knownVerbs) {
    if (new RegExp(`\\b${escapeRegex(v)}\\b`).test(lower)) {
      found.push(v)
    }
  }
  return found
}

function _detectConstraintsInClause(clauseText: string): string[] {
  const lower = clauseText.toLowerCase()
  const constraints: string[] = []
  if (/\b(without|avoid|never|no |not|don't|do not|except|excluding)\b/.test(lower)) {
    constraints.push("negation")
  }
  if (/\b(must|need to|have to|required|essential)\b/.test(lower)) {
    constraints.push("requirement")
  }
  if (/\b(only|exactly|strictly|specifically|precisely)\b/.test(lower)) {
    constraints.push("exact")
  }
  if (/\b(using|with|via|through|by|import|require|dependency|library)\b/.test(lower)) {
    constraints.push("dependency")
  }
  return constraints
}

export function chunk(text: string, knownVerbs?: Set<string>): ChunkResult {
  const tokens = text.match(/\b\w+\b/g) ?? []
  const verbSet = knownVerbs ?? new Set<string>()
  const compound_verbs = _detectCompoundVerbs(tokens)
  const clauseTexts = _splitClauses(text)

  const clauses: Clause[] = []
  for (const ct of clauseTexts) {
    const verbsIn = _detectVerbsInClause(ct, verbSet)
    const constraintsIn = _detectConstraintsInClause(ct)
    const hasNeg = constraintsIn.includes("negation")
    const hasHedge = /\b(maybe|perhaps|possibly|probably|might|could|i think|i believe)\b/i.test(ct)
    const hasEmp = /\b(must|absolutely|critical|urgent|essential|required|vital)\b/i.test(ct)
    clauses.push({
      text: ct.trim(),
      verbs: verbsIn,
      constraints: constraintsIn,
      has_negation: hasNeg,
      has_hedging: hasHedge,
      has_emphasis: hasEmp,
    })
  }

  const contradiction_hits = _detectContradictions(clauses)
  const topic_shifts = _countTopicShifts(clauses)

  const clause_indicators: string[] = []
  if (clauses.length > 3) {
    clause_indicators.push(`${clauses.length} clauses detected (may indicate multi-instruction)`)
  }
  if (contradiction_hits.length > 0) {
    clause_indicators.push(`contradictory markers: ${contradiction_hits.slice(0, 2).join(", ")}`)
  }
  if (compound_verbs.length > 0) {
    clause_indicators.push(`phrasal verbs: ${compound_verbs.slice(0, 3).map((cv) => cv.full).join(", ")}`)
  }
  if (topic_shifts > 2) {
    clause_indicators.push(`${topic_shifts} topic shifts (may indicate scope creep)`)
  }

  return {
    text,
    clauses,
    compound_verbs,
    topic_shifts,
    contradiction_hits,
    clause_indicators,
  }
}

export function renderChunkReport(cr: ChunkResult): string {
  const sep = "=".repeat(56)
  const lines: string[] = [sep, "  Chunk analysis", sep, ""]

  if (cr.compound_verbs.length > 0) {
    lines.push(`  Phrasal verbs: ${cr.compound_verbs.map((cv) => cv.full).join(", ")}`)
    lines.push("")
  }

  lines.push(`  Clauses (${cr.clauses.length}):`)
  for (let i = 0; i < cr.clauses.length; i++) {
    const clause = cr.clauses[i]
    const parts: string[] = []
    if (clause.has_negation) parts.push("NEG")
    if (clause.has_emphasis) parts.push("EMP")
    if (clause.has_hedging) parts.push("HEDGE")
    const tags = parts.length > 0 ? `  [${parts.join(", ")}]` : ""
    const short = clause.text.slice(0, 55)
    lines.push(`    ${i + 1}. ${short}${tags}`)
    if (clause.verbs.length > 0) {
      lines.push(`       verbs: ${clause.verbs.join(", ")}`)
    }
    if (clause.constraints.length > 0) {
      lines.push(`       constraints: ${clause.constraints.join(", ")}`)
    }
  }

  if (cr.contradiction_hits.length > 0) {
    lines.push("")
    lines.push("  Potential contradictions:")
    for (const h of cr.contradiction_hits) {
      lines.push(`    ! ${h}`)
    }
  }

  if (cr.topic_shifts > 2) {
    lines.push("")
    lines.push(`  Topic shifts: ${cr.topic_shifts} (possible scope creep)`)
  }

  lines.push(sep)
  return lines.join("\n")
}
