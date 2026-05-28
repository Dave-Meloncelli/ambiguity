import { VERB_TAXONOMY, KNOWN_ACRONYMS, VOCABULARY_SCOPE, SPELLING_CORRECTIONS, containersForVerb } from "./containers.js"
import { AmbiguityScore } from "./scoring.js"
import { parse, type ParseResult } from "./parser.js"

export interface Change {
  type: string
  original?: string
  replacement?: string
}

export interface Translation {
  original: string
  translated: string
  changes: Change[]
  beforeScore: number
  afterScore: number
  bandBefore: string
  bandAfter: string
}

function expandAcronyms(text: string, result: ParseResult): Change[] {
  const changes: Change[] = []
  for (const [acronym, expansion] of result.acronyms) {
    if (expansion && expansion !== "unknown") {
      const replacement = `${acronym} (${expansion})`
      if (text.includes(acronym)) {
        changes.push({ type: "acronym", original: acronym, replacement })
      }
    }
  }
  return changes
}

function replaceVagueVerbs(text: string, result: ParseResult): Change[] {
  const changes: Change[] = []
  for (const verb of result.verbs) {
    const entry = VERB_TAXONOMY[verb]
    if (entry && entry.specificity < 0.3 && entry.containers.length > 0) {
      changes.push({ type: "vague_verb", original: verb, replacement: `${entry.containers[0]} (${verb})` })
    }
  }
  return changes
}

function flagUnqualifiedRefs(text: string, result: ParseResult): Change[] {
  const changes: Change[] = []
  for (const ref of result.unqualifiedRefs) {
    if (["it", "thing", "stuff", "something", "that"].includes(ref.toLowerCase())) {
      changes.push({ type: "unqualified_ref", original: ref, replacement: `<<${ref}>>` })
    }
  }
  return changes
}

function addConstraintReminder(text: string, result: ParseResult, score: AmbiguityScore): Change[] {
  const changes: Change[] = []
  if (result.constraints.length === 0 && score.total > 4.0) {
    const reminder = "\n\n[NOTE: Add explicit constraints — languages, dependencies, boundaries, or format requirements]"
    changes.push({ type: "constraint_reminder", replacement: reminder })
  }
  return changes
}

function addVocabHint(text: string, result: ParseResult): Change[] {
  const changes: Change[] = []
  for (const vt of result.vocabScope) {
    const hint = ` (${vt.domain} term)`
    changes.push({ type: "vocab_scope", original: vt.term, replacement: `${vt.term}${hint}` })
  }
  return changes
}

function applyChanges(changes: Change[], text: string): string {
  for (const c of changes) {
    if (c.type === "constraint_reminder" && c.replacement) {
      text += c.replacement
    } else if (c.original !== undefined && c.replacement !== undefined) {
      text = text.replaceAll(c.original, c.replacement)
    }
  }
  return text
}

export function translate(prompt: string): Translation {
  const resultBefore = parse(prompt)
  const scoreBefore = new AmbiguityScore(resultBefore)

  const changes: Change[] = []
  let text = prompt

  let c = expandAcronyms(text, resultBefore)
  changes.push(...c)
  text = applyChanges(c, text)

  c = replaceVagueVerbs(text, resultBefore)
  changes.push(...c)
  text = applyChanges(c, text)

  c = flagUnqualifiedRefs(text, resultBefore)
  changes.push(...c)
  text = applyChanges(c, text)

  c = addVocabHint(text, resultBefore)
  changes.push(...c)
  text = applyChanges(c, text)

  c = addConstraintReminder(text, resultBefore, scoreBefore)
  changes.push(...c)
  text = applyChanges(c, text)

  const resultAfter = parse(text)
  const scoreAfter = new AmbiguityScore(resultAfter)

  return {
    original: prompt,
    translated: text,
    changes,
    beforeScore: scoreBefore.total,
    afterScore: scoreAfter.total,
    bandBefore: scoreBefore.band,
    bandAfter: scoreAfter.band,
  }
}

export function renderTranslateReport(t: Translation): string {
  const sep = "=".repeat(56)
  const lines: string[] = [
    sep,
    "  ambiguity translate — prompt de-ambiguation",
    sep,
    "",
    `  Score: ${t.beforeScore.toFixed(1)}/10 (${t.bandBefore})`,
  ]

  if (t.changes.length === 0) {
    lines.push("  No changes needed.", sep)
    return lines.join("\n")
  }

  lines.push("", "  Changes applied:")
  const symMap: Record<string, string> = {
    acronym: "A", vague_verb: "V", unqualified_ref: "?",
    vocab_scope: "S", constraint_reminder: "C",
  }
  for (const c of t.changes) {
    const sym = symMap[c.type] ?? "*"
    if (c.type === "constraint_reminder") {
      lines.push(`    [${sym}] Added constraint reminder`)
    } else {
      lines.push(`    [${sym}] ${c.original}  ->  ${c.replacement}`)
    }
  }

  lines.push("", "  Translated prompt:")
  for (const line of t.translated.split("\n")) {
    lines.push(`    | ${line}`)
  }

  lines.push("", `  New score: ${t.afterScore.toFixed(1)}/10 (${t.bandAfter})`, sep)
  return lines.join("\n")
}
