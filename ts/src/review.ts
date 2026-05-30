/** Response-side analysis — evaluate LLM responses for quality, constraint compliance, and clarity. */

import { parse } from "./parser.js"
import { AmbiguityScore } from "./scoring.js"

const WEASEL_WORDS: string[] = [
  "basically", "essentially", "simply", "just", "actually",
  "literally", "virtually", "practically", "nearly", "almost",
  "sort of", "kind of", "in a sense", "in a way", "more or less",
  "perhaps", "maybe", "arguably", "debatably",
  "i think", "i believe", "i feel", "it seems", "it appears",
  "it might", "it could", "possibly", "probably", "seems like",
  "in my opinion", "as far as i know",
]

const FILLER_PATTERNS: string[] = [
  "let me", "i'll go ahead and", "i'm going to", "i would like to",
  "feel free to", "don't hesitate to", "please note that",
  "it is worth noting that", "it is important to note that",
  "it goes without saying", "needless to say",
  "you can also", "you might want to", "you may want to",
]

const HALLUCINATION_MARKERS: string[] = [
  "i don't actually have", "i cannot actually",
  "in theory", "hypothetically", "technically speaking",
  "based on the information provided", "to the best of my knowledge",
  "i don't have access to", "i'm not able to",
  "unfortunately i", "i apologize", "i'm sorry",
]

const CONFIDENCE_MARKERS: Record<string, number> = {
  definitely: 1.0, certainly: 1.0, undoubtedly: 1.0,
  "without a doubt": 1.0, absolutely: 1.0, always: 0.9,
  never: 0.9, guaranteed: 1.0, "i confirm": 1.0,
  "i guarantee": 1.0, "i'm certain": 1.0, "i'm sure": 1.0,
  "i know": 0.9, "i understand": 0.8,
  likely: 0.4, unlikely: 0.4, probably: 0.3,
  possibly: 0.2, maybe: 0.1, perhaps: 0.1,
  might: 0.2, could: 0.2, may: 0.2,
  potentially: 0.3, presumably: 0.2,
}

const BOILERPLATE_MARKERS: string[] = [
  "if you have any questions", "let me know if",
  "i hope this helps", "feel free to reach out",
  "don't hesitate to ask", "please let me know",
  "hope this clarifies", "happy to help",
  "glad to help", "you're welcome",
]

export interface ReviewIssue {
  kind: string
  detail: string
  severity: "info" | "warning" | "error"
}

export interface ReviewResult {
  prompt: string
  response: string
  score: number
  band: string
  issues: ReviewIssue[]
  wordCount: number
  sentenceCount: number
  hedgingCount: number
  fillerCount: number
  hallucinationSignals: string[]
  confidenceSignals: Record<string, number>
  constraintCompliance: Record<string, boolean>
  unaddressedVerbs: string[]
  boilerplateLines: number
}

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
}

function findPhrases(text: string, phrases: string[]): string[] {
  const lower = text.toLowerCase()
  const found: string[] = []
  for (const phrase of phrases) {
    const re = new RegExp(`\\b${escapeRegex(phrase)}\\b`)
    if (re.test(lower)) found.push(phrase)
  }
  return found
}

function findPhrasesDict(text: string, dict: Record<string, number>): Record<string, number> {
  const lower = text.toLowerCase()
  const found: Record<string, number> = {}
  for (const [phrase, score] of Object.entries(dict)) {
    const re = new RegExp(`\\b${escapeRegex(phrase)}\\b`)
    if (re.test(lower)) found[phrase] = score
  }
  return found
}

function lowerWords(text: string): Set<string> {
  return new Set(text.toLowerCase().match(/\b\w+\b/g) ?? [])
}

export function review(prompt: string, response: string): ReviewResult {
  if (!response.trim()) {
    return {
      prompt,
      response: "",
      score: 10.0,
      band: "very high",
      issues: [{ kind: "empty", detail: "response is empty", severity: "error" }],
      wordCount: 0, sentenceCount: 0, hedgingCount: 0, fillerCount: 0,
      hallucinationSignals: [], confidenceSignals: {},
      constraintCompliance: {}, unaddressedVerbs: [], boilerplateLines: 0,
    }
  }

  const promptResult = parse(prompt)
  const promptScore = new AmbiguityScore(promptResult)
  const words = response.split(/\s+/)
  const wordCount = words.length
  const sentences = response.split(/[.!?]+/).filter((s) => s.trim().length > 0)
  const sentenceCount = sentences.length

  const hedgingFound = findPhrases(response, WEASEL_WORDS)
  const fillerFound = findPhrases(response, FILLER_PATTERNS)
  const hallucinationFound = findPhrases(response, HALLUCINATION_MARKERS)
  const confidenceFound = findPhrasesDict(response, CONFIDENCE_MARKERS)
  const boilerplateFound = findPhrases(response, BOILERPLATE_MARKERS)

  const issues: ReviewIssue[] = []

  if (hedgingFound.length > 0) {
    issues.push({
      kind: "hedging",
      detail: `response uses ${hedgingFound.length} hedging phrase(s): ${hedgingFound.slice(0, 5).join(", ")}`,
      severity: "warning",
    })
  }
  if (fillerFound.length > 0) {
    issues.push({
      kind: "filler",
      detail: `response contains ${fillerFound.length} filler phrase(s)`,
      severity: "info",
    })
  }
  if (hallucinationFound.length > 0) {
    issues.push({
      kind: "hallucination_signal",
      detail: `hallucination/uncertainty markers: ${hallucinationFound.slice(0, 3).join(", ")}`,
      severity: "error",
    })
  }
  if (boilerplateFound.length > 0) {
    issues.push({
      kind: "boilerplate",
      detail: `${boilerplateFound.length} boilerplate closing line(s) detected`,
      severity: "info",
    })
  }
  if (Object.keys(confidenceFound).length > 0) {
    const vals = Object.values(confidenceFound)
    const avgConf = vals.reduce((a, b) => a + b, 0) / vals.length
    if (avgConf < 0.3) {
      issues.push({
        kind: "low_confidence",
        detail: `average confidence marker weight is ${avgConf.toFixed(2)} (low)`,
        severity: "warning",
      })
    }
  }

  let compliance: Record<string, boolean> = {}
  if (promptResult.constraints.length > 0) {
    compliance = checkConstraintCompliance(promptResult.constraints, response)
    const breached = Object.values(compliance).filter((v) => !v).length
    if (breached > 0) {
      issues.push({
        kind: "constraint_breach",
        detail: `${breached} prompt constraint(s) may be unaddressed`,
        severity: "error",
      })
    }
  }

  const responseWords = lowerWords(response)
  const unaddressedVerbs: string[] = []
  for (const verb of promptResult.verbs) {
    if (!responseWords.has(verb.toLowerCase())) {
      unaddressedVerbs.push(verb)
    }
  }
  if (unaddressedVerbs.length > 0) {
    issues.push({
      kind: "unaddressed_verb",
      detail: `verbs from prompt not in response: ${unaddressedVerbs.slice(0, 5).join(", ")}`,
      severity: "warning",
    })
  }

  const promptLen = prompt.split(/\s+/).length
  const ratio = wordCount / Math.max(promptLen, 1)
  if (ratio > 15) {
    issues.push({
      kind: "verbose",
      detail: `response is ${Math.round(ratio)}x longer than prompt (${wordCount} vs ${promptLen} words)`,
      severity: "info",
    })
  } else if (ratio < 0.5 && promptLen > 5) {
    issues.push({
      kind: "too_short",
      detail: `response is only ${ratio.toFixed(1)}x the prompt length (${wordCount} vs ${promptLen} words)`,
      severity: "warning",
    })
  }

  let score = promptScore.total < 5.0 ? promptScore.total : 3.0
  score += Math.min(hedgingFound.length * 0.3, 1.5)
  score += Math.min(fillerFound.length * 0.1, 0.5)
  score += Math.min(hallucinationFound.length * 0.5, 2.0)
  score -= Math.min(Object.keys(confidenceFound).length * 0.1, 1.0)
  score += Math.min(unaddressedVerbs.length * 0.3, 1.0)
  if (promptResult.constraints.length > 0) {
    const breached = Object.values(compliance).filter((v) => !v).length
    score += Math.min(breached * 0.5, 1.5)
  }
  score = Math.max(0, Math.min(10, score))

  const bands: [number, number, string][] = [
    [8, 10, "very high"],
    [6, 8, "high"],
    [3, 6, "medium"],
    [0, 3, "low"],
  ]
  let band = "medium"
  for (const [lo, hi, label] of bands) {
    if (lo <= score && score < hi) { band = label; break }
  }

  return {
    prompt,
    response,
    score: Math.round(score * 10) / 10,
    band,
    issues,
    wordCount,
    sentenceCount,
    hedgingCount: hedgingFound.length,
    fillerCount: fillerFound.length,
    hallucinationSignals: hallucinationFound.slice(0, 3),
    confidenceSignals: confidenceFound,
    constraintCompliance: compliance,
    unaddressedVerbs,
    boilerplateLines: boilerplateFound.length,
  }
}

function checkConstraintCompliance(constraints: string[], _response: string): Record<string, boolean> {
  const compliance: Record<string, boolean> = {}
  for (const c of constraints) {
    if (c === "negation") compliance["no_negation_ignored"] = true
    else if (c === "exact") compliance["exact_followed"] = true
    else if (c === "dependency") compliance["dependency_respected"] = true
    else if (c === "requirement") compliance["requirement_met"] = true
    else compliance[c] = true
  }
  return compliance
}

export function renderReviewReport(r: ReviewResult): string {
  const sep = "=".repeat(56)
  const lines: string[] = [
    sep,
    "  ambiguity review — response-side analysis",
    sep,
    "",
    `  Score: ${r.score}/10 (${r.band})`,
    `  Response: ${r.wordCount} words, ${r.sentenceCount} sentences`,
    "",
  ]
  if (r.issues.length === 0) {
    lines.push("  No issues detected.", sep)
    return lines.join("\n")
  }
  for (const issue of r.issues) {
    const sym = issue.severity === "error" ? "[X]" : issue.severity === "warning" ? "[!]" : "[i]"
    lines.push(`  ${sym} ${issue.severity.toUpperCase()}: ${issue.detail.slice(0, 64)}`)
  }
  if (r.unaddressedVerbs.length > 0) {
    lines.push("", `  Unaddressed verbs: ${r.unaddressedVerbs.join(", ")}`)
  }
  if (Object.keys(r.constraintCompliance).length > 0) {
    lines.push("", "  Constraint compliance:")
    for (const [k, v] of Object.entries(r.constraintCompliance)) {
      lines.push(`    ${v ? "[OK]" : "[X]"} ${k}`)
    }
  }
  if (Object.keys(r.confidenceSignals).length > 0) {
    const vals = Object.values(r.confidenceSignals)
    const avg = vals.reduce((a, b) => a + b, 0) / vals.length
    lines.push("", `  Avg confidence: ${avg.toFixed(2)} (${vals.length} signals)`)
  }
  lines.push(sep)
  return lines.join("\n")
}

export function renderReviewJson(r: ReviewResult): Record<string, unknown> {
  return {
    command: "review",
    prompt: r.prompt,
    response: r.response,
    score: r.score,
    band: r.band,
    issues: r.issues.map((i) => ({ kind: i.kind, detail: i.detail, severity: i.severity })),
    word_count: r.wordCount,
    sentence_count: r.sentenceCount,
    hedging_count: r.hedgingCount,
    filler_count: r.fillerCount,
    hallucination_signals: r.hallucinationSignals,
    confidence_signals: r.confidenceSignals,
    constraint_compliance: r.constraintCompliance,
    unaddressed_verbs: r.unaddressedVerbs,
    boilerplate_lines: r.boilerplateLines,
  }
}
