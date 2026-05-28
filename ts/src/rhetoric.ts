const IDIOMS: [string, string, string][] = [
  ["\\bboil the ocean\\b", "over_scope", "attempting too much at once"],
  ["\\bput a pin in\\b", "defer", "postponing a topic"],
  ["\\blow.hanging fruit\\b", "easy_win", "quick, easy task"],
  ["\\bmove the needle\\b", "significant_progress", "meaningful change"],
  ["\\bheavy lift\\b", "difficult", "hard or resource-intensive task"],
  ["\\blift\\b.*\\bfinger\\b", "minimal_effort", "doing very little"],
  ["\\bdrill down\\b", "deep_investigation", "examine in detail"],
  ["\\bcircle back\\b", "return_to_topic", "discuss later"],
  ["\\btouch base\\b", "check_in", "brief status update"],
  ["\\bon the same page\\b", "alignment", "shared understanding"],
  ["\\bbandwidth\\b", "capacity", "available resources or attention"],
  ["\\bcutting edge\\b", "innovation", "most advanced"],
  ["\\bdeep dive\\b", "thorough_examination", "comprehensive analysis"],
  ["\\bgame plan\\b", "strategy", "planned approach"],
  ["\\bget our hands dirty\\b", "hands_on_work", "direct involvement"],
  ["\\bgranular\\b", "detail_level", "level of detail"],
  ["\\bhigh.level\\b", "summary", "overview or strategic view"],
  ["\\bleverage\\b", "utilize", "use as advantage"],
  ["\\boptics\\b", "perception", "how things appear"],
  ["\\bbrainstorm\\b", "idea_generation", "generate ideas freely"],
  ["\\bramp up\\b", "scale", "increase capacity or speed"],
  ["\\bscalable\\b", "growth_capable", "able to grow"],
  ["\\bsynergy\\b", "collaboration_benefit", "combined effect greater than sum"],
  ["\\bthink outside the box\\b", "creative_thinking", "unconventional approach"],
  ["\\bvalue add\\b", "additional_benefit", "extra value provided"],
  ["\\bvet\\b", "review", "examine or evaluate"],
  ["\\bwarehouse\\b", "store", "store for later use"],
  ["\\bwater under the bridge\\b", "past_irrelevant", "no longer important"],
  ["\\bwin.win\\b", "mutual_benefit", "beneficial for all parties"],
  ["\\bduck soup\\b", "easy", "very easy task"],
  ["\\ba piece of cake\\b", "easy", "very easy task"],
  ["\\bhit the ground running\\b", "immediate_productivity", "start effectively"],
  ["\\bballpark\\b", "rough_estimate", "approximate figure"],
  ["\\bhard stop\\b", "deadline", "firm end time"],
  ["\\bkeep me in the loop\\b", "inform", "keep updated"],
  ["\\btable that\\b", "defer", "set aside for later"],
  ["\\bopen the kimono\\b", "full_disclosure", "reveal all information"],
  ["\\bskeletons in the closet\\b", "hidden_issues", "undisclosed problems"],
  ["\\blowest hanging fruit\\b", "easy_win", "easiest task to complete"],
]

const HEDGES: string[] = [
  "maybe", "perhaps", "possibly", "probably", "might", "could",
  "kind of", "sort of", "a bit", "a little", "somewhat",
  "i think", "i believe", "i guess", "i assume", "i suppose",
  "it might be", "it could be", "it seems", "it appears",
  "generally", "mostly", "usually", "typically", "often",
  "in my opinion", "from my perspective", "as far as i know",
  "if possible", "if you can", "when you get a chance",
  "no rush", "whenever", "sometime", "eventually",
  "ideally", "preferably", "optionally",
]

const EMPHATICS: string[] = [
  "must", "absolutely", "critical", "urgent", "asap", "immediately",
  "essential", "mandatory", "required", "necessary", "vital",
  "imperative", "non.negotiable", "at all costs", "top priority",
  "do or die", "make or break", "deadline", "due by",
  "no matter what", "by any means", "under no circumstances",
]

const FRAMING_PATTERNS: string[] = [
  "i want (you|this) to",
  "we need to",
  "can you (please )?",
  "could you (please )?",
  "would you (please )?",
  "please (make|create|write|build|implement|add|fix|help|do)",
  "i need (you|this|a|the)",
  "it would be great if",
  "i.d like (you|to)",
  "your task is to?",
  "your job is to?",
  "the goal is to?",
  "the objective is to?",
  "i.m looking for",
  "help me (with|to|understand|build|create|find|fix)",
]

const METAPHOR_SOURCE_DOMAINS: Record<string, string> = {
  surface: "physical_space",
  bridge: "physical_space",
  path: "physical_space",
  roadmap: "physical_space",
  landscape: "physical_space",
  terrain: "physical_space",
  footprint: "physical_space",
  layer: "physical_space",
  depth: "physical_space",
  scope: "physical_space",
  boundary: "physical_space",
  edge: "physical_space",
  core: "physical_space",
  hub: "physical_space",
  spoke: "physical_space",
  build: "construction",
  foundation: "construction",
  framework: "construction",
  scaffold: "construction",
  pillar: "construction",
  architecture: "construction",
  infrastructure: "construction",
  blueprint: "construction",
  journey: "journey",
  milestone: "journey",
  trajectory: "journey",
  momentum: "journey",
  pipeline: "journey",
  bottleneck: "journey",
  throughput: "journey",
  envelope: "container",
  capsule: "container",
  silo: "container",
  bucket: "container",
  pool: "container",
  sandbox: "container",
  health: "health",
  symptom: "health",
  diagnosis: "health",
  remedy: "health",
  "pain point": "health",
  friction: "health",
  target: "warfare",
  campaign: "warfare",
  strategy: "warfare",
  tactic: "warfare",
  retreat: "warfare",
  kill: "warfare",
  ecosystem: "nature",
  growth: "nature",
  seed: "nature",
  garden: "nature",
  weed: "nature",
  prune: "nature",
  bloom: "nature",
  engine: "machine",
  gear: "machine",
  lever: "machine",
  pivot: "machine",
  cog: "machine",
  flywheel: "machine",
  leverage: "finance",
  equity: "finance",
  capital: "finance",
  currency: "finance",
  investment: "finance",
  dividend: "finance",
  burn: "finance",
  flag: "nautical",
  anchor: "nautical",
  navigate: "nautical",
  course: "nautical",
  helm: "nautical",
  rudder: "nautical",
  sail: "nautical",
}

export interface RhetoricResult {
  text: string
  idioms: Array<{ intent: string; description: string; pattern: string }>
  hedges: string[]
  emphatics: string[]
  framing_hits: Array<{ pattern: string; count: number }>
  metaphors: Array<{ term: string; source_domain: string }>
  repetitive_framing: string[]
  intent_signals: Record<string, number>
  rhetoric_indicators: string[]
}

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
}

export function analyzeRhetoric(text: string): RhetoricResult {
  const lower = text.toLowerCase()
  const idioms: RhetoricResult["idioms"] = []
  const hedges: string[] = []
  const emphatics: string[] = []
  const metaphors: RhetoricResult["metaphors"] = []
  const intent_signals: Record<string, number> = {}
  const seenIntents = new Set<string>()

  for (const [pattern, intent, desc] of IDIOMS) {
    if (new RegExp(pattern).test(lower) && !seenIntents.has(intent)) {
      seenIntents.add(intent)
      idioms.push({ intent, description: desc, pattern })
    }
  }

  const seenHedges = new Set<string>()
  for (const hedge of HEDGES) {
    const escaped = escapeRegex(hedge)
    if (new RegExp(`\\b${escaped}\\b`).test(lower) && !seenHedges.has(hedge)) {
      seenHedges.add(hedge)
      hedges.push(hedge)
    }
  }

  const seenEmp = new Set<string>()
  for (const emph of EMPHATICS) {
    const escaped = escapeRegex(emph)
    if (new RegExp(`\\b${escaped}\\b`).test(lower) && !seenEmp.has(emph)) {
      seenEmp.add(emph)
      emphatics.push(emph)
    }
  }

  const framingCounts: Record<string, number> = {}
  for (const pattern of FRAMING_PATTERNS) {
    const re = new RegExp(pattern, "gi")
    const matches = text.match(re)
    if (matches) {
      framingCounts[pattern] = matches.length
    }
  }
  const framing_hits = Object.entries(framingCounts).map(([p, c]) => ({ pattern: p, count: c }))

  const repetitive_framing: string[] = []
  for (const item of framing_hits) {
    if (item.count >= 3) {
      repetitive_framing.push(`${item.pattern} x${item.count}`)
    }
  }

  for (const [word, domain] of Object.entries(METAPHOR_SOURCE_DOMAINS)) {
    const escaped = escapeRegex(word)
    if (new RegExp(`\\b${escaped}\\b`).test(lower)) {
      metaphors.push({ term: word, source_domain: domain })
    }
  }

  for (const idiom of idioms) {
    intent_signals[idiom.intent] = (intent_signals[idiom.intent] ?? 0) + 1.0
  }
  for (const item of framing_hits) {
    if (/urgent|need|must/.test(item.pattern)) {
      intent_signals["urgency"] = (intent_signals["urgency"] ?? 0) + item.count * 0.5
    }
    if (/please|i'd like/.test(item.pattern)) {
      intent_signals["politeness"] = (intent_signals["politeness"] ?? 0) + item.count * 0.3
    }
  }

  const rhetoric_indicators: string[] = []
  if (idioms.length > 0) {
    const intents = [...new Set(idioms.map((i) => i.intent))]
    rhetoric_indicators.push(`idioms detected: ${intents.join(", ")}`)
  }
  if (hedges.length >= 2) {
    rhetoric_indicators.push(`hedging language (${hedges.length} signals)`)
  }
  if (emphatics.length >= 2) {
    rhetoric_indicators.push(`emphatic language (${emphatics.length} signals)`)
  }
  if (metaphors.length >= 3) {
    rhetoric_indicators.push(`metaphor density: ${metaphors.length} terms`)
  }
  if (repetitive_framing.length > 0) {
    rhetoric_indicators.push(`repetitive framing: ${repetitive_framing.slice(0, 3).join(", ")}`)
  }

  return {
    text,
    idioms,
    hedges,
    emphatics,
    framing_hits,
    metaphors,
    repetitive_framing,
    intent_signals,
    rhetoric_indicators,
  }
}

export function renderRhetoricReport(r: RhetoricResult): string {
  const sep = "=".repeat(56)
  const lines: string[] = [sep, "  Rhetoric analysis", sep, ""]
  if (r.idioms.length > 0) {
    lines.push(`  Idioms (${r.idioms.length}):`)
    for (const i of r.idioms) {
      lines.push(`    ${i.intent} — ${i.description}`)
    }
  }
  if (r.hedges.length > 0) {
    lines.push(`  Hedging: ${r.hedges.slice(0, 5).join(", ")}`)
  }
  if (r.emphatics.length > 0) {
    lines.push(`  Emphasis: ${r.emphatics.slice(0, 5).join(", ")}`)
  }
  if (r.metaphors.length > 0) {
    const domains = [...new Set(r.metaphors.map((m) => m.source_domain))]
    lines.push(`  Metaphor source domains: ${domains.join(", ")}`)
  }
  if (r.repetitive_framing.length > 0) {
    lines.push(`  Repetitive framing: ${r.repetitive_framing.join("; ")}`)
  }
  if (Object.keys(r.intent_signals).length > 0) {
    const signals = Object.entries(r.intent_signals).sort((a, b) => b[1] - a[1])
    lines.push(`  Intent signals: ${signals.slice(0, 5).map(([k, v]) => `${k}(${v.toFixed(1)})`).join(", ")}`)
  }
  if (!r.idioms.length && !r.hedges.length && !r.emphatics.length && !r.metaphors.length && !r.repetitive_framing.length) {
    lines.push("  No significant rhetorical patterns detected.")
  }
  lines.push(sep)
  return lines.join("\n")
}
