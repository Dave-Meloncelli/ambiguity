import { containersForKey, containersForVerb } from "./containers.js"
import type { ParseResult } from "./parser.js"

export class AmbiguityScore {
  verbSpecificity: number
  containerOverlap: number
  entropyIndicators: string[]
  unqualifiedRefs: number
  constraintCount: number
  instructionDensity: number
  total: number
  band: string

  constructor(result: ParseResult) {
    this.verbSpecificity = verbSpecificityScore(result.verbs)
    this.containerOverlap = containerOverlapCount(result.verbs, result.keywords)
    this.entropyIndicators = entropyIndicators(result)
    this.unqualifiedRefs = result.unqualifiedRefs.length
    this.constraintCount = result.constraints.length
    this.instructionDensity = instructionDensity(result)
    this.total = totalScore(this)
    this.band = scoreBand(this.total)
  }
}

function verbSpecificityScore(verbs: string[]): number {
  if (verbs.length === 0) return 0.0
  const scores = verbs.map((v) => containersForVerb(v)[1])
  return scores.reduce((a, b) => a + b, 0) / scores.length
}

function containerOverlapCount(verbs: string[], keywords: string[]): number {
  const all = new Set<string>()
  for (const v of verbs) {
    const [cs] = containersForVerb(v)
    for (const c of cs) all.add(c)
  }
  for (const kw of keywords) {
    for (const c of containersForKey(kw)) all.add(c)
  }
  return all.size
}

function entropyIndicators(result: ParseResult): string[] {
  const indicators: string[] = []
  if (result.instructionCount > 3)
    indicators.push(`${result.instructionCount} instructions in one prompt`)
  if (result.verbs.length === 0) indicators.push("no action verb detected")
  if (result.unqualifiedRefs.length > 0)
    indicators.push(`unqualified references: ${result.unqualifiedRefs.slice(0, 3).join(", ")}`)
  const verbSpec = verbSpecificityScore(result.verbs)
  if (verbSpec < 0.3 && result.verbs.length > 0)
    indicators.push(`vague verb(s): ${result.verbs.join(", ")}`)
  if (result.constraints.length === 0) indicators.push("no explicit constraints")
  if (result.acronyms.length > 0)
    indicators.push(`acronyms (expand: ${result.acronyms.map((a) => a[0]).join(", ")})`)
  return indicators
}

function instructionDensity(result: ParseResult): number {
  if (result.wordCount === 0) return 0.0
  return result.instructionCount / (result.wordCount / 10)
}

function totalScore(s: AmbiguityScore): number {
  let base = 5.0
  base -= s.verbSpecificity * 2.0
  base += Math.min(s.containerOverlap * 0.5, 2.0)
  base += s.entropyIndicators.length * 0.5
  base += s.unqualifiedRefs * 0.5
  base -= Math.min(s.constraintCount * 0.5, 2.0)
  return Math.max(0.0, Math.min(10.0, base))
}

const SCORE_BANDS: [number, number, string][] = [
  [0.0, 3.0, "low"],
  [3.0, 6.0, "medium"],
  [6.0, 8.0, "high"],
  [8.0, 10.0, "very high"],
]

function scoreBand(total: number): string {
  for (const [lo, hi, label] of SCORE_BANDS) {
    if (lo <= total && total < hi) return label
  }
  return "very high"
}
