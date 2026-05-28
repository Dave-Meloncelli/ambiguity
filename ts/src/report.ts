import { advisory } from "./advisory.js"
import { containersForVerb, specificityBand } from "./containers.js"
import type { ParseResult } from "./parser.js"
import type { AmbiguityScore } from "./scoring.js"

const BOX = "="
const V = "|"
const TL = "+"
const TR = "+"
const BL = "+"
const BR = "+"
const TE = "+"
const BE = "+"
const DOT = "*"
const OK = "[OK]"
const WARN = "[!]"
const BAD = "[X]"

export function terminalReport(
  result: ParseResult,
  score: AmbiguityScore,
  udlInfo?: string,
): string {
  const lines: string[] = []
  const width = 64

  const header = "ambiguity analyze v0.1"
  lines.push(`${TL}${BOX.repeat(width - 2)}${TR}`)
  lines.push(`${V} ${header}${" ".repeat(width - header.length - 2)}${V}`)
  lines.push(`${TE}${BOX.repeat(width - 2)}${BE}`)

  const row = (label: string, value: string) => {
    const content = `${label}: ${value}`.slice(0, width - 4)
    lines.push(`${V}  ${content.padEnd(width - 4)}${V}`)
  }

  row("Language", "English")
  row("Ambiguity Score", `${score.total.toFixed(1)}/10 (${score.band})`)

  const sym = score.band === "low" ? OK : score.band === "very high" ? BAD : WARN
  row("", `  ${sym} ${score.band.toUpperCase()}`)

  const adv = advisory(result, score)
  if (adv) {
    row("Tip", adv.slice(0, width - 10))
  }

  lines.push(`${TE}${BOX.repeat(width - 2)}${BE}`)

  for (const verb of result.verbs) {
    const [containers, spec] = containersForVerb(verb)
    const band = specificityBand(spec)
    const cStr = containers.length > 0 ? containers.join(", ") : "(none)"
    const fuzzy = result.fuzzyVerbs.find((fv) => fv.corrected === verb)
    const verbLabel = fuzzy
      ? `${verb} (from '${fuzzy.original}', edit-dist ${fuzzy.distance})`
      : verb
    row(`  Verb: ${verbLabel}`, `${band} (spec: ${spec.toFixed(2)})`)
    row("", `  containers: ${cStr}`)
  }

  if (result.typoWords.length > 0) {
    row("Typos", result.typoWords.map((t) => `${t.original}->${t.corrected}`).join(", "))
  }
  if (result.missingSpaces.length > 0) {
    row(
      "Misspaces",
      result.missingSpaces.map((m) => `${m.combined}->${m.split.join(" ")}`).join(", "),
    )
  }
  if (result.stutterWords.length > 0) {
    row("Stutter", result.stutterWords.map((s) => `${s.word}x${s.occurrences}`).join(", "))
  }
  if (result.repeatedChars.length > 0) {
    row("RepeatCh", result.repeatedChars.join(", "))
  }
  if (!result.hasTerminalPunctuation && result.wordCount > 3) {
    row("Punct", "no terminal punctuation")
  }

  lines.push(`${TE}${BOX.repeat(width - 2)}${BE}`)

  row("Keywords", result.keywords.length > 0 ? result.keywords.slice(0, 6).join(", ") : "(none)")
  row("Constraints", result.constraints.length > 0 ? result.constraints.join(", ") : "(none)")
  row(
    "Acronyms",
    result.acronyms.length > 0
      ? result.acronyms.map((a) => `${a[0]}->${a[1]}`).join(", ")
      : "(none)",
  )
  row("Instructions", String(result.instructionCount))
  row("Words", String(result.wordCount))

  lines.push(`${TE}${BOX.repeat(width - 2)}${BE}`)

  if (score.entropyIndicators.length > 0) {
    row("Issues", "")
    for (const indicator of score.entropyIndicators.slice(0, 5)) {
      row(`  ${DOT}`, indicator.slice(0, width - 8))
    }
  }

  if (udlInfo) {
    lines.push(`${TE}${BOX.repeat(width - 2)}${BE}`)
    row("UDL Envelope", udlInfo)
  }

  lines.push(`${BL}${BOX.repeat(width - 2)}${BR}`)
  return lines.join("\n")
}

export function jsonReport(result: ParseResult, score: AmbiguityScore): Record<string, unknown> {
  return {
    version: "0.1.0",
    language: "English",
    ambiguity_score: {
      total: Math.round(score.total * 10) / 10,
      band: score.band,
      verb_specificity: Math.round(score.verbSpecificity * 100) / 100,
      container_overlap: score.containerOverlap,
      unqualified_refs: score.unqualifiedRefs,
      constraint_count: score.constraintCount,
      instruction_density: Math.round(score.instructionDensity * 100) / 100,
      entropy_indicators: score.entropyIndicators,
    },
    advisory: advisory(result, score),
    analysis: {
      verbs: result.verbs.map((v) => {
        const [containers, spec] = containersForVerb(v)
        return { word: v, containers, specificity: spec, band: specificityBand(spec) }
      }),
      keywords: result.keywords.map((kw) => ({ word: kw })),
      constraints: result.constraints,
      acronyms: result.acronyms.map(([a, e]) => ({ abbreviation: a, expansion: e })),
      unqualified_refs: result.unqualifiedRefs,
      vocabulary_scope: result.vocabScope,
      fuzzy_verbs: result.fuzzyVerbs,
      typo_words: result.typoWords,
      stutter_words: result.stutterWords,
      missing_spaces: result.missingSpaces,
      repeated_chars: result.repeatedChars,
      has_terminal_punctuation: result.hasTerminalPunctuation,
      word_count: result.wordCount,
      sentence_count: result.sentenceCount,
      instruction_count: result.instructionCount,
    },
  }
}
