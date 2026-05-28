export interface DependencyEdge {
  token: string
  pos: string
  dep: string
  head: string | null
  children: string[]
}

export interface ParseTree {
  root: string | null
  tokens: DependencyEdge[]
}

export interface NlpResult {
  has_spacy: boolean
  pos_tags: Record<string, string>
  dependency_tree: ParseTree | null
  named_entities: Array<[string, string]>
  subject_verb_pairs: Array<[string, string]>
  verb_objects: Array<[string, string]>
}

export function analyze(_text: string): NlpResult {
  return {
    has_spacy: false,
    pos_tags: {},
    dependency_tree: null,
    named_entities: [],
    subject_verb_pairs: [],
    verb_objects: [],
  }
}

export function detectSemanticAmbiguity(_result: NlpResult): string[] {
  return []
}

export function detectImplicitRelations(_result: NlpResult): string[] {
  return []
}

export function renderNlpReport(result: NlpResult): string {
  const sep = "=".repeat(60)
  if (!result.has_spacy) {
    return [
      sep,
      "  NLP bridge: spaCy not available (falling back to regex)",
      "  Install: pip install spacy && python -m spacy download en_core_web_sm",
      sep,
    ].join("\n")
  }

  const lines: string[] = [sep, "  NLP deep parse (spaCy)", sep]
  if (result.subject_verb_pairs.length > 0) {
    const pairs = result.subject_verb_pairs.slice(0, 5).map(([s, v]) => `${s} → ${v}`)
    lines.push(`  Subject→Verb: ${pairs.join(", ")}`)
  }
  if (result.verb_objects.length > 0) {
    const pairs = result.verb_objects.slice(0, 5).map(([v, o]) => `${v} → ${o}`)
    lines.push(`  Verb→Object: ${pairs.join(", ")}`)
  }
  if (result.named_entities.length > 0) {
    const entities = result.named_entities.slice(0, 5).map(([e, l]) => `${e} (${l})`)
    lines.push(`  Entities: ${entities.join(", ")}`)
  }
  if (result.dependency_tree?.root) {
    lines.push(`  Root: ${result.dependency_tree.root}`)
  }

  const semantic = detectSemanticAmbiguity(result)
  for (const w of semantic) {
    lines.push(`  ! ${w}`)
  }
  const implicit = detectImplicitRelations(result)
  for (const s of implicit) {
    lines.push(`  ! ${s}`)
  }
  lines.push(sep)
  return lines.join("\n")
}
