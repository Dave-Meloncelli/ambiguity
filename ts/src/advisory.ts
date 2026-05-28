import { containersForVerb } from "./containers.js"
import type { ParseResult } from "./parser.js"
import type { AmbiguityScore } from "./scoring.js"

let _suppressed = new Set<string>()

export function setSuppressed(flags: Set<string>): void {
  _suppressed = flags
}

export function advisory(result: ParseResult, score: AmbiguityScore): string | null {
  const candidates: [number, string, string][] = []

  const vagueVerbs = result.verbs.filter((v) => containersForVerb(v)[1] < 0.3)
  if (vagueVerbs.length > 0 && !_suppressed.has("vague_verb")) {
    const v = vagueVerbs[0]
    candidates.push([
      1,
      "vague_verb",
      `replace vague verb '${v}' with a specific action (implement, convert, verify)`,
    ])
  }

  if (result.verbs.length === 0 && result.wordCount > 2 && !_suppressed.has("no_verb")) {
    candidates.push([2, "no_verb", "start with an action verb - 'write', 'explain', 'convert'"])
  }

  if (
    result.constraints.length === 0 &&
    result.wordCount > 3 &&
    result.verbs.length > 0 &&
    !_suppressed.has("no_constraints")
  ) {
    candidates.push([
      3,
      "no_constraints",
      "add at least one constraint - boundaries guide the model",
    ])
  }

  if (result.fuzzyVerbs.length > 0 && !_suppressed.has("fuzzy_verb")) {
    const fv = result.fuzzyVerbs[0]
    candidates.push([
      4,
      "fuzzy_verb",
      `guessing you meant '${fv.corrected}' for '${fv.original}' — close enough, I matched it`,
    ])
  }

  if (result.acronyms.length > 0 && !_suppressed.has("acronym")) {
    const [a, e] = result.acronyms[0]
    candidates.push([5, "acronym", `expand '${a}' to '${e}' on first use for consistent reception`])
  }

  if (result.vocabScope.length > 0 && !_suppressed.has("vocab_scope")) {
    const vs = result.vocabScope
      .slice(0, 3)
      .map((v) => `'${v.term}'`)
      .join(", ")
    const extra = result.vocabScope.length > 3 ? ` and ${result.vocabScope.length - 3} more` : ""
    candidates.push([
      6,
      "vocab_scope",
      `define domain terms before use: ${vs}${extra} may be ambiguous to unfamiliar readers`,
    ])
  }

  if (result.instructionCount > 3 && !_suppressed.has("multi_instruction")) {
    candidates.push([
      7,
      "multi_instruction",
      `split into separate turns - ${result.instructionCount} instructions overload reception`,
    ])
  }

  if (result.unqualifiedRefs.length > 0 && !_suppressed.has("unqualified_ref")) {
    const ref = result.unqualifiedRefs[0]
    candidates.push([8, "unqualified_ref", `replace '${ref}' with a concrete reference`])
  }

  if (result.typoWords.length > 0 && !_suppressed.has("typo")) {
    const tw = result.typoWords[0]
    candidates.push([
      9,
      "typo",
      `'${tw.original}' looks like '${tw.corrected}' — no worries, just flagging in case`,
    ])
  }

  if (
    !result.hasTerminalPunctuation &&
    result.wordCount > 3 &&
    !_suppressed.has("no_terminal_punct")
  ) {
    candidates.push([
      10,
      "no_terminal_punct",
      "add a period or question mark at the end to signal completeness",
    ])
  }

  if (result.missingSpaces.length > 0 && !_suppressed.has("missing_space")) {
    const ms = result.missingSpaces[0]
    candidates.push([
      11,
      "missing_space",
      `'${ms.combined}' might be two words: '${ms.split[0]} ${ms.split[1]}'`,
    ])
  }

  if (result.stutterWords.length > 0 && !_suppressed.has("stutter")) {
    const sw = result.stutterWords[0]
    candidates.push([12, "stutter", `'${sw.word}' repeated ${sw.occurrences}x — likely a typo`])
  }

  if (result.repeatedChars.length > 0 && !_suppressed.has("repeated_char")) {
    const rc = result.repeatedChars[0]
    candidates.push([13, "repeated_char", `'${rc}' has characters repeated 3+ times`])
  }

  if (candidates.length === 0) return null

  candidates.sort((a, b) => a[0] - b[0])
  return candidates[0][2]
}
