import { VERB_TAXONOMY } from "./containers.js"
import { AmbiguityScore } from "./scoring.js"
import { parse, type ParseResult } from "./parser.js"

export interface ClarificationQuestion {
  indicator: string
  question: string
}

export interface Clarification {
  prompt: string
  score: number
  band: string
  questions: ClarificationQuestion[]
}

const QUESTION_TEMPLATES: Record<string, string> = {
  vague_verb: "What specific action should '{value}' map to? (e.g. implement, convert, verify, generate)",
  no_verb: "What should this prompt do? No action verb detected.",
  no_constraints: "What boundaries apply? (language, dependencies, format, or performance constraints)",
  acronym: "What does '{value}' stand for?",
  unqualified_ref: "What does '{value}' refer to? Be specific.",
  vocab_scope: "What domain does '{value}' belong to? (ecosystem, technical, or metaphor)",
  multi_instruction: "Which instruction should take priority? This prompt has multiple requests.",
  typo: "Did you mean '{corrected}' instead of '{original}'?",
}

function extractClarification(indicator: string): string | null {
  for (const [key, template] of Object.entries(QUESTION_TEMPLATES)) {
    if (indicator.includes(key)) return template
  }
  return null
}

export function generateClarification(prompt: string): Clarification {
  const result = parse(prompt)
  const score = new AmbiguityScore(result)
  const questions: ClarificationQuestion[] = []

  for (const indicator of score.entropyIndicators) {
    const template = extractClarification(indicator)
    if (template) {
      const colonIdx = indicator.indexOf(":")
      const raw = colonIdx >= 0 ? indicator.slice(colonIdx + 1).trim() : indicator
      const value = raw.replace(/\)$/, "").trim()
      questions.push({
        indicator,
        question: template
          .replace(/\{value\}/g, value)
          .replace(/\{original\}/g, indicator)
          .replace(/\{corrected\}/g, ""),
      })
    }
  }

  for (const verb of result.verbs) {
    const entry = VERB_TAXONOMY[verb]
    if (entry && entry.specificity < 0.3) {
      const exists = questions.some((q) => q.indicator.includes("vague_verb"))
      if (!exists) {
        questions.push({
          indicator: `vague_verb: ${verb}`,
          question: QUESTION_TEMPLATES["vague_verb"].replace(/\{value\}/g, verb),
        })
      }
    }
  }

  for (const [acronym, expansion] of result.acronyms) {
    if (expansion === "unknown") {
      questions.push({
        indicator: `acronym: ${acronym}`,
        question: QUESTION_TEMPLATES["acronym"].replace(/\{value\}/g, acronym),
      })
    }
  }

  return {
    prompt,
    score: score.total,
    band: score.band,
    questions,
  }
}

export function renderClarifyReport(c: Clarification): string {
  const sep = "=".repeat(56)
  const lines: string[] = [
    sep,
    "  ambiguity clarify — request clarification",
    sep,
    "",
    `  Score: ${c.score.toFixed(1)}/10 (${c.band})`,
  ]

  if (c.questions.length === 0) {
    lines.push("  No clarification needed.", sep)
    return lines.join("\n")
  }

  lines.push("", `  ${c.questions.length} clarification question(s):`, "")
  for (let i = 0; i < c.questions.length; i++) {
    lines.push(`  ${i + 1}. ${c.questions[i].question}`)
  }
  lines.push("", `  ${sep}`, "  How to use: answer each question, then re-run the prompt", `  ${sep}`)
  return lines.join("\n")
}
