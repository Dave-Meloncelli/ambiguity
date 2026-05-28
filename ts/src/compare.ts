import * as fs from "fs"
import * as path from "path"
import { advisory } from "./advisory.js"
import { AmbiguityScore } from "./scoring.js"
import { parse, type ParseResult } from "./parser.js"
import { translate } from "./translate.js"

export interface CompareResult {
  controlPrompt: string
  treatmentPrompt: string
  controlScore: number
  treatmentScore: number
  controlWordCount: number
  treatmentWordCount: number
  vocabOverlap: number
  metrics: Record<string, unknown>
  band: string
  advisory: string | null
  controlResponse: string | null
  treatmentResponse: string | null
  error: string | null
}

function buildEnrichedPrompt(prompt: string): string {
  const result = parse(prompt)
  const score = new AmbiguityScore(result)
  const adv = advisory(result, score)
  const indicators = score.entropyIndicators
  const verbs = result.verbs
  const constraints = result.constraints

  const parts: string[] = ["## Ambiguity Pre-Flight Analysis\n"]
  parts.push(`Score: ${score.total.toFixed(1)}/10 (${score.band})`)
  if (adv) parts.push(`Advisory: ${adv}`)
  if (indicators.length > 0) {
    parts.push("\nIssues to address:\n" + indicators.map((i) => `- ${i}`).join("\n"))
  }
  if (verbs.length > 0) parts.push(`\nDetected verbs: ${verbs.join(", ")}`)
  if (constraints.length > 0) parts.push(`Constraints: ${constraints.join(", ")}`)
  parts.push("\n---\n\n## Original Request\n\n" + prompt)
  parts.push("\n\n## Response Requirements\n")
  parts.push("Please address all issues flagged above in your response.")
  return parts.join("\n")
}

function compareResponses(control: string, treatment: string): Record<string, unknown> {
  const controlLen = control.split(/\s+/).length
  const treatmentLen = treatment.split(/\s+/).length
  const metrics: Record<string, unknown> = {
    control_word_count: controlLen,
    treatment_word_count: treatmentLen,
    length_ratio: Math.round((treatmentLen / Math.max(controlLen, 1)) * 100) / 100,
  }
  const controlWords = new Set(control.toLowerCase().split(/\s+/))
  const treatmentWords = new Set(treatment.toLowerCase().split(/\s+/))
  const common = new Set([...controlWords].filter((w) => treatmentWords.has(w)))
  metrics.vocab_overlap_ratio =
    Math.round((common.size / Math.max(treatmentWords.size, 1)) * 100) / 100
  return metrics
}

export function compare(prompt: string): CompareResult {
  const result = parse(prompt)
  const score = new AmbiguityScore(result)
  const adv = advisory(result, score)
  const enriched = buildEnrichedPrompt(prompt)

  const resultEnriched = parse(enriched)
  const scoreEnriched = new AmbiguityScore(resultEnriched)

  return {
    controlPrompt: prompt,
    treatmentPrompt: enriched,
    controlScore: score.total,
    treatmentScore: scoreEnriched.total,
    controlWordCount: 0,
    treatmentWordCount: 0,
    vocabOverlap: 0,
    metrics: {},
    band: score.band,
    advisory: adv,
    controlResponse: null,
    treatmentResponse: null,
    error: null,
  }
}

export function renderCompareReport(result: CompareResult): string {
  const width = 64
  const lines: string[] = [
    "=".repeat(width),
    "  ambiguity compare — pre-flight experiment",
    "=".repeat(width),
    `  Score: ${result.controlScore.toFixed(1)}/10 (${result.band})`,
  ]
  if (result.advisory) lines.push(`  Advisory: ${result.advisory}`)
  lines.push("")

  if (result.error) {
    lines.push(`  [SKIP] ${result.error}`, "")
    lines.push("  To run the full experiment, set:")
    lines.push("    ANTHROPIC_API_KEY=sk-...  or  OPENAI_API_KEY=sk-...", "")
    lines.push('  Or use --no-llm to output prompt files for manual testing:')
    lines.push('    ambiguity compare "your prompt" --no-llm --output-dir ./experiment')
    lines.push("=".repeat(width))
    return lines.join("\n")
  }

  if (result.controlResponse && result.treatmentResponse) {
    lines.push("  Control (raw prompt):")
    const cLines = result.controlResponse.trim().split("\n")
    for (const line of cLines.slice(0, 6)) {
      lines.push(`    | ${line.slice(0, width - 6)}`)
    }
    if (cLines.length > 6) {
      lines.push(`    | ... (${cLines.length - 6} more lines)`)
    }
    lines.push("")
    lines.push("  Treatment (with ambiguity pre-flight):")
    const tLines = result.treatmentResponse.trim().split("\n")
    for (const line of tLines.slice(0, 6)) {
      lines.push(`    | ${line.slice(0, width - 6)}`)
    }
    if (tLines.length > 6) {
      lines.push(`    | ... (${tLines.length - 6} more lines)`)
    }
    lines.push("")
    if (Object.keys(result.metrics).length > 0) {
      lines.push("  Metrics:")
      for (const [k, v] of Object.entries(result.metrics)) {
        lines.push(`    ${k}: ${v}`)
      }
    }
  }

  lines.push("=".repeat(width))
  return lines.join("\n")
}

export function writeExperimentFiles(result: CompareResult, outputDir: string): string {
  const out = path.resolve(outputDir)
  fs.mkdirSync(out, { recursive: true })
  const stamp = new Date().toISOString().replace(/[:.]/g, "").replace(/T/, "T").slice(0, 15) + "Z"
  fs.writeFileSync(path.join(out, `original_prompt_${stamp}.txt`), result.controlPrompt, "utf-8")
  fs.writeFileSync(path.join(out, `enriched_prompt_${stamp}.txt`), result.treatmentPrompt, "utf-8")
  if (result.controlResponse) {
    fs.writeFileSync(path.join(out, `control_response_${stamp}.txt`), result.controlResponse, "utf-8")
  }
  if (result.treatmentResponse) {
    fs.writeFileSync(path.join(out, `treatment_response_${stamp}.txt`), result.treatmentResponse, "utf-8")
  }
  const report = {
    command: "compare",
    generated_at: new Date().toISOString(),
    prompt: result.controlPrompt,
    ambiguity_score: Math.round(result.controlScore * 10) / 10,
    band: result.band,
    advisory: result.advisory,
    enriched_prompt: result.treatmentPrompt,
    control_response: result.controlResponse,
    treatment_response: result.treatmentResponse,
    metrics: result.metrics,
    error: result.error,
  }
  fs.writeFileSync(path.join(out, `compare_report_${stamp}.json`), JSON.stringify(report, null, 2), "utf-8")
  return out
}
