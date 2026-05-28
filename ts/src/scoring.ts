import { containersForKey, containersForVerb } from "./containers.js"
import type { ParseResult } from "./parser.js"
import type { RhetoricResult } from "./rhetoric.js"
import type { ChunkResult } from "./chunking.js"

export class AmbiguityScore {
  verbSpecificity: number
  containerOverlap: number
  entropyIndicators: string[]
  unqualifiedRefs: number
  constraintCount: number
  instructionDensity: number
  total: number
  band: string

  constructor(result: ParseResult, rhetoric?: RhetoricResult, chunking?: ChunkResult) {
    this.verbSpecificity = verbSpecificityScore(result.verbs)
    this.containerOverlap = containerOverlapCount(result.verbs, result.keywords)
    this.entropyIndicators = entropyIndicators(result, rhetoric, chunking)
    this.unqualifiedRefs = result.unqualifiedRefs.length
    this.constraintCount = result.constraints.length
    this.instructionDensity = instructionDensity(result)
    this.total = totalScore(this, result, rhetoric, chunking)
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

function entropyIndicators(result: ParseResult, rhetoric?: RhetoricResult, chunking?: ChunkResult): string[] {
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
  if (result.vocabScope.length > 0) {
    const terms = result.vocabScope.map((v) => `'${v.term}'`).join(", ")
    indicators.push(`domain-specific vocabulary used without definition: ${terms}`)
  }
  if (rhetoric?.rhetoric_indicators.length) {
    indicators.push(...rhetoric.rhetoric_indicators)
  }
  if (chunking?.clause_indicators.length) {
    indicators.push(...chunking.clause_indicators)
  }
  return indicators
}

function instructionDensity(result: ParseResult): number {
  if (result.wordCount === 0) return 0.0
  return result.instructionCount / (result.wordCount / 10)
}

function rhetoricPenalty(rhetoric?: RhetoricResult): number {
  if (!rhetoric) return 0
  const hedgeScore = Math.min(rhetoric.hedges.length * 0.3, 1.0)
  const urgencyScore = Math.min(rhetoric.emphatics.length * 0.3, 1.0)
  const metaphorDensity = Math.min(rhetoric.metaphors.length * 0.1, 1.0)
  const idiomWeight = Math.min(rhetoric.idioms.length * 0.2, 1.0)
  return Math.min(hedgeScore + urgencyScore * 0.5 + metaphorDensity * 0.3 + idiomWeight, 2.0)
}

function chunkingPenalty(chunking?: ChunkResult): number {
  if (!chunking) return 0
  let p = 0
  p += Math.min(chunking.clause_indicators.length * 0.3, 1.5)
  p += Math.min(chunking.contradiction_hits.length * 0.5, 1.0)
  p += Math.max(0, chunking.topic_shifts - 2) * 0.3
  return Math.min(p, 2.0)
}

function totalScore(s: AmbiguityScore, result?: ParseResult, rhetoric?: RhetoricResult, chunking?: ChunkResult): number {
  let base = 5.0
  base -= s.verbSpecificity * 2.0
  base += Math.min(s.containerOverlap * 0.5, 2.0)
  base += s.entropyIndicators.length * 0.5
  base += s.unqualifiedRefs * 0.5
  base -= Math.min(s.constraintCount * 0.5, 2.0)
  // vocabulary scope: each undefined domain term adds 0.3, capped at 1.5
  if (result?.vocabScope) {
    base += Math.min(result.vocabScope.length * 0.3, 1.5)
  }
  base += rhetoricPenalty(rhetoric)
  base += chunkingPenalty(chunking)
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
