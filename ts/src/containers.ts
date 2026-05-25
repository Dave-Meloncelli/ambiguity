/** Verb taxonomy, keyword maps, and container definitions. */

export interface ContainerInfo {
  name: string
  description: string
  specificity: number
}

export interface VerbEntry {
  containers: string[]
  specificity: number
}

export interface KeywordEntry {
  containers: string[]
  collision?: string[]
}

export const CONTAINERS: Record<string, ContainerInfo> = {
  code_generation: {
    name: "code_generation",
    description: "Producing new code artifacts",
    specificity: 0.6,
  },
  explanation: {
    name: "explanation",
    description: "Tutorial or expository content",
    specificity: 0.7,
  },
  analysis: { name: "analysis", description: "Decomposition or assessment", specificity: 0.7 },
  transformation: {
    name: "transformation",
    description: "Converting or refactoring existing things",
    specificity: 0.7,
  },
  retrieval: { name: "retrieval", description: "Factual or informational query", specificity: 0.6 },
  ordering: { name: "ordering", description: "Sorting, ranking, or sequencing", specificity: 0.8 },
  reasoning: { name: "reasoning", description: "Step-by-step logical deduction", specificity: 0.8 },
  general_processing: {
    name: "general_processing",
    description: "Non-specific processing action",
    specificity: 0.2,
  },
  function_definition: {
    name: "function_definition",
    description: "Declaring or defining a function",
    specificity: 0.8,
  },
  python_syntax: {
    name: "python_syntax",
    description: "Python-specific language features",
    specificity: 0.6,
  },
  error_handling: {
    name: "error_handling",
    description: "Edge cases, exceptions, robustness",
    specificity: 0.8,
  },
  performance: {
    name: "performance",
    description: "Efficiency, speed, optimization",
    specificity: 0.8,
  },
  verification: {
    name: "verification",
    description: "Checking, validating, confirming",
    specificity: 0.7,
  },
  query: {
    name: "query",
    description: "Asking for information or clarification",
    specificity: 0.5,
  },
  creation: { name: "creation", description: "Generating novel content", specificity: 0.5 },
  constraint: {
    name: "constraint",
    description: "Boundary or limitation on scope",
    specificity: 0.9,
  },
}

export const KNOWN_ACRONYMS: Record<string, string> = {
  UDL: "Unified Data Layer",
  CHAP: "Cross-Harness Alignment Protocol",
  LLM: "Large Language Model",
  API: "Application Programming Interface",
  JSON: "JavaScript Object Notation",
  YAML: "YAML Ain't Markup Language",
  CSV: "Comma-Separated Values",
  HTML: "HyperText Markup Language",
  CSS: "Cascading Style Sheets",
  JS: "JavaScript",
  TS: "TypeScript",
  CLI: "Command Line Interface",
  TUI: "Terminal User Interface",
  SDK: "Software Development Kit",
  IDE: "Integrated Development Environment",
  DB: "Database",
  SQL: "Structured Query Language",
  ORM: "Object-Relational Mapping",
  REST: "Representational State Transfer",
  URL: "Uniform Resource Locator",
}

export const VERB_TAXONOMY: Record<string, VerbEntry> = {
  write: { containers: ["code_generation", "creation"], specificity: 0.6 },
  create: { containers: ["code_generation", "creation"], specificity: 0.5 },
  generate: { containers: ["code_generation", "creation"], specificity: 0.5 },
  build: { containers: ["code_generation"], specificity: 0.6 },
  implement: { containers: ["code_generation"], specificity: 0.7 },
  produce: { containers: ["code_generation", "creation"], specificity: 0.5 },
  explain: { containers: ["explanation", "reasoning"], specificity: 0.7 },
  describe: { containers: ["explanation"], specificity: 0.6 },
  clarify: { containers: ["explanation"], specificity: 0.7 },
  elaborate: { containers: ["explanation"], specificity: 0.7 },
  analyze: { containers: ["analysis"], specificity: 0.7 },
  compare: { containers: ["analysis"], specificity: 0.8 },
  evaluate: { containers: ["analysis"], specificity: 0.8 },
  diagnose: { containers: ["analysis"], specificity: 0.8 },
  audit: { containers: ["analysis", "verification"], specificity: 0.8 },
  convert: { containers: ["transformation"], specificity: 0.8 },
  translate: { containers: ["transformation"], specificity: 0.8 },
  refactor: { containers: ["transformation", "code_generation"], specificity: 0.8 },
  rewrite: { containers: ["transformation"], specificity: 0.7 },
  adapt: { containers: ["transformation"], specificity: 0.7 },
  sort: { containers: ["ordering", "code_generation"], specificity: 0.8 },
  sorts: { containers: ["ordering", "code_generation"], specificity: 0.8 },
  sorted: { containers: ["ordering", "code_generation"], specificity: 0.8 },
  sorting: { containers: ["ordering", "code_generation"], specificity: 0.8 },
  order: { containers: ["ordering"], specificity: 0.7 },
  rank: { containers: ["ordering", "analysis"], specificity: 0.8 },
  handle: { containers: ["general_processing"], specificity: 0.2 },
  do: { containers: [], specificity: 0.1 },
  deal: { containers: ["general_processing"], specificity: 0.2 },
  make: { containers: ["creation"], specificity: 0.3 },
  get: { containers: ["retrieval"], specificity: 0.3 },
  find: { containers: ["retrieval"], specificity: 0.4 },
  tell: { containers: ["explanation"], specificity: 0.4 },
  give: { containers: ["retrieval", "creation"], specificity: 0.3 },
  check: { containers: ["verification"], specificity: 0.6 },
  verify: { containers: ["verification"], specificity: 0.8 },
  validate: { containers: ["verification"], specificity: 0.8 },
  confirm: { containers: ["verification"], specificity: 0.7 },
  review: { containers: ["verification", "analysis"], specificity: 0.7 },
  think: { containers: ["reasoning"], specificity: 0.5 },
  reason: { containers: ["reasoning"], specificity: 0.7 },
  fix: { containers: ["code_generation", "transformation"], specificity: 0.7 },
  debug: { containers: ["analysis", "code_generation"], specificity: 0.8 },
  test: { containers: ["verification"], specificity: 0.7 },
  improve: { containers: ["code_generation", "transformation"], specificity: 0.6 },
  optimise: { containers: ["performance", "code_generation"], specificity: 0.8 },
  enhance: { containers: ["code_generation", "creation"], specificity: 0.5 },
  uplift: { containers: ["transformation", "creation"], specificity: 0.5 },
  expand: { containers: ["creation", "explanation"], specificity: 0.5 },
  upgrade: { containers: ["transformation"], specificity: 0.7 },
  migrate: { containers: ["transformation"], specificity: 0.8 },
  integrate: { containers: ["code_generation", "transformation"], specificity: 0.7 },
  automate: { containers: ["code_generation"], specificity: 0.8 },
  deploy: { containers: ["code_generation"], specificity: 0.8 },
  monitor: { containers: ["analysis", "verification"], specificity: 0.7 },
  log: { containers: ["analysis"], specificity: 0.6 },
  notify: { containers: ["explanation"], specificity: 0.6 },
  render: { containers: ["code_generation", "creation"], specificity: 0.7 },
  parse: { containers: ["analysis", "transformation"], specificity: 0.8 },
  extract: { containers: ["analysis", "transformation"], specificity: 0.7 },
  merge: { containers: ["transformation"], specificity: 0.8 },
  split: { containers: ["transformation", "analysis"], specificity: 0.7 },
  remove: { containers: ["transformation"], specificity: 0.7 },
  add: { containers: ["code_generation"], specificity: 0.5 },
  update: { containers: ["code_generation", "transformation"], specificity: 0.5 },
  register: { containers: ["code_generation", "creation"], specificity: 0.6 },
  process: { containers: ["general_processing"], specificity: 0.3 },
  configure: { containers: ["code_generation"], specificity: 0.6 },
  install: { containers: ["code_generation"], specificity: 0.7 },
  uninstall: { containers: ["code_generation"], specificity: 0.8 },
  start: { containers: ["code_generation", "explanation"], specificity: 0.4 },
  stop: { containers: ["code_generation"], specificity: 0.6 },
  restart: { containers: ["code_generation"], specificity: 0.6 },
  include: { containers: ["code_generation", "creation"], specificity: 0.4 },
  consider: { containers: ["reasoning"], specificity: 0.6 },
  cite: { containers: ["explanation", "verification"], specificity: 0.7 },
  follow: { containers: ["general_processing"], specificity: 0.4 },
  provide: { containers: ["creation", "explanation"], specificity: 0.4 },
  perform: { containers: ["general_processing"], specificity: 0.3 },
  require: { containers: [], specificity: 0.2 },
  assume: { containers: ["reasoning"], specificity: 0.5 },
  search: { containers: ["retrieval"], specificity: 0.7 },
  mention: { containers: ["explanation"], specificity: 0.4 },
  apply: { containers: ["code_generation", "transformation"], specificity: 0.5 },
  support: { containers: ["verification", "explanation"], specificity: 0.5 },
  reference: { containers: ["explanation", "verification"], specificity: 0.6 },
  respond: { containers: ["explanation", "creation"], specificity: 0.3 },
  replace: { containers: ["transformation"], specificity: 0.7 },
  return: { containers: ["code_generation", "explanation"], specificity: 0.5 },
  execute: { containers: ["code_generation", "general_processing"], specificity: 0.6 },
  call: { containers: ["code_generation", "retrieval"], specificity: 0.5 },
  modify: { containers: ["code_generation", "transformation"], specificity: 0.5 },
  output: { containers: ["code_generation", "creation"], specificity: 0.4 },
  select: { containers: ["retrieval", "analysis"], specificity: 0.6 },
  specify: { containers: ["explanation", "code_generation"], specificity: 0.5 },
  match: { containers: ["verification", "analysis"], specificity: 0.6 },
  note: { containers: ["explanation"], specificity: 0.4 },
  help: { containers: ["explanation", "code_generation"], specificity: 0.3 },
  answer: { containers: ["explanation", "creation"], specificity: 0.4 },
  discuss: { containers: ["reasoning", "explanation"], specificity: 0.5 },
  block: { containers: ["code_generation", "general_processing"], specificity: 0.5 },
  limit: { containers: ["code_generation", "transformation"], specificity: 0.5 },
  commit: { containers: ["code_generation"], specificity: 0.7 },
  print: { containers: ["code_generation", "creation"], specificity: 0.5 },
  quote: { containers: ["explanation", "verification"], specificity: 0.6 },

  optimize: { containers: ["performance", "code_generation"], specificity: 0.8 },
  refine: { containers: ["code_generation", "transformation"], specificity: 0.7 },
  clean: { containers: ["code_generation"], specificity: 0.5 },
  document: { containers: ["creation", "explanation"], specificity: 0.7 },
  summarize: { containers: ["analysis", "creation"], specificity: 0.7 },
}

export const KEYWORD_MAP: Record<string, KeywordEntry> = {
  function: { containers: ["code_generation", "function_definition"] },
  def: { containers: ["function_definition"] },
  python: { containers: ["python_syntax"] },
  list: { containers: ["code_generation"], collision: ["data_structure", "shopping_list"] },
  error: { containers: ["error_handling"] },
  exception: { containers: ["error_handling"] },
  "edge case": { containers: ["error_handling"] },
  efficient: { containers: ["performance"] },
  fast: { containers: ["performance"] },

  import: { containers: ["constraint"] },
  only: { containers: ["constraint"] },
  exactly: { containers: ["constraint"] },
  must: { containers: ["constraint"] },
  specifically: { containers: ["constraint"] },
  dont: { containers: ["constraint"] },
  "do not": { containers: ["constraint"] },
  avoid: { containers: ["constraint"] },
  never: { containers: ["constraint"] },
  without: { containers: ["constraint"] },
  no: { containers: ["constraint"] },
  why: { containers: ["explanation", "analysis"] },
  how: { containers: ["explanation"] },
  what: { containers: ["retrieval", "explanation"] },
  "step by step": { containers: ["reasoning"] },
}

const SPECIFICITY_BANDS: [number, number, string][] = [
  [0.0, 0.3, "vague"],
  [0.3, 0.6, "moderate"],
  [0.6, 0.8, "specific"],
  [0.8, 1.0, "precise"],
]

export function specificityBand(score: number): string {
  for (const [lo, hi, label] of SPECIFICITY_BANDS) {
    if (lo <= score && score < hi) return label
  }
  return "precise"
}

export function containersForVerb(verb: string): [string[], number] {
  const entry = VERB_TAXONOMY[verb.toLowerCase()]
  if (entry) return [entry.containers, entry.specificity]
  return [[], 0.0]
}

export function containersForKey(keyword: string): string[] {
  const entry = KEYWORD_MAP[keyword.toLowerCase()]
  if (entry) return entry.containers
  return []
}

export function collisionsForKey(keyword: string): string[] {
  const entry = KEYWORD_MAP[keyword.toLowerCase()]
  if (entry?.collision) return entry.collision
  return []
}

export function resolveAcronym(word: string): string | undefined {
  return KNOWN_ACRONYMS[word.toUpperCase()]
}

export function levenshteinDistance(a: string, b: string): number {
  const aLen = a.length
  const bLen = b.length
  const matrix: number[][] = []
  for (let i = 0; i <= aLen; i++) {
    matrix[i] = [i]
  }
  for (let j = 0; j <= bLen; j++) {
    matrix[0][j] = j
  }
  for (let i = 1; i <= aLen; i++) {
    for (let j = 1; j <= bLen; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1
      matrix[i][j] = Math.min(
        matrix[i - 1][j] + 1,
        matrix[i][j - 1] + 1,
        matrix[i - 1][j - 1] + cost,
      )
    }
  }
  return matrix[aLen][bLen]
}

const FUZZY_IGNORE = new Set([
  "and",
  "the",
  "for",
  "with",
  "from",
  "this",
  "that",
  "these",
  "those",
  "to",
  "in",
  "of",
  "at",
  "by",
  "on",
  "as",
  "a",
  "an",
  "or",
  "but",
  "nor",
  "asap",
  "aka",
  "etc",
  "ie",
  "eg",
  "via",
  "vs",
  "per",
  "about",
  "above",
  "after",
  "before",
  "between",
  "through",
  "during",
  "because",
  "while",
  "until",
  "since",
  "although",
  "though",
  "into",
  "onto",
  "upon",
  "within",
  "without",
  "across",
  "against",
  "under",
  "over",
  "out",
  "off",
  "down",
  "up",
  "all",
  "any",
  "each",
  "every",
  "both",
  "few",
  "many",
  "some",
  "much",
  "very",
  "too",
  "also",
  "just",
  "then",
  "now",
  "here",
  "there",
  "than",
  "else",
  "their",
  "your",
  "our",
  "its",
  "his",
  "her",
  "my",
  "working",
  "looking",
  "making",
  "taking",
  "giving",
  "coming",
  "going",
  "doing",
  "having",
  "being",
  "saying",
  "seeing",
  "using",
  "calling",
  "trying",
  "asking",
  "telling",
  "showing",
  "running",
  "putting",
  "setting",
  "letting",
  "getting",
  "thing",
  "things",
  "stuff",
  "something",
  "anything",
  "nothing",
  "people",
  "person",
  "place",
  "time",
  "way",
  "number",
  "world",
  "life",
  "hand",
  "part",
  "child",
  "eye",
  "woman",
  "man",
  "men",
  "work",
  "study",
  "family",
  "point",
  "city",
  "state",
  "area",
  "water",
  "group",
  "country",
  "problem",
  "system",
  "program",
  "already",
  "always",
  "never",
  "often",
  "sometimes",
  "usually",
  "today",
  "tomorrow",
  "yesterday",
  "morning",
  "evening",
  "night",
  "please",
  "thanks",
  "sorry",
  "hello",
  "goodbye",
  "welcome",
  "so",
  "long",
  "text",
  "top",
  "set",
  "short",
  "fit",
  "real",
  "kind",
  "well",
  "move",
  "old",
  "new",
  "big",
  "small",
  "high",
  "low",
  "end",
  "next",
  "last",
  "first",
  "second",
  "third",
  "left",
  "right",
  "top",
  "bottom",
  "front",
  "back",
  "side",
  "still",
  "yet",
  "already",
  "quite",
  "rather",
  "pretty",
  "might",
  "must",
  "shall",
  "should",
  "could",
  "would",
  "may",
  "can",
  "say",
  "says",
  "said",
  "want",
  "need",
  "like",
  "love",
  "hate",
  "one",
  "two",
  "three",
  "four",
  "five",
  "six",
  "seven",
  "eight",
  "nine",
  "ten",
])

export function fuzzyVerbMatch(word: string): { verb: string; distance: number } | null {
  const lower = word.toLowerCase()
  if (FUZZY_IGNORE.has(lower)) return null
  if (VERB_TAXONOMY[lower]) return { verb: lower, distance: 0 }
  let best: { verb: string; distance: number } | null = null
  const knownVerbs = Object.keys(VERB_TAXONOMY)
  for (const known of knownVerbs) {
    const d = levenshteinDistance(lower, known)
    if (d === 0) return { verb: known, distance: 0 }
    const maxDist = 1 // distance 2 produces too many false positives from common nouns
    if (d <= maxDist) {
      if (!best || d < best.distance) {
        best = { verb: known, distance: d }
      }
    }
  }
  return best
}

export const SPELLING_CORRECTIONS: Record<string, string> = {
  allign: "align",
  alligns: "aligns",
  alligned: "aligned",
  allignment: "alignment",
  recieve: "receive",
  recieved: "received",
  seperate: "separate",
  definately: "definitely",
  occured: "occurred",
  occuring: "occurring",
  ocur: "occur",
  wierd: "weird",
  acheive: "achieve",
  acheiving: "achieving",
  beleive: "believe",
  beleived: "believed",
  writting: "writing",
  writen: "written",
  untill: "until",
  enviroment: "environment",
  enviromental: "environmental",
  dependancy: "dependency",
  dependancies: "dependencies",
  maintenence: "maintenance",
  maintanance: "maintenance",
  impliment: "implement",
  implimentation: "implementation",
  implimented: "implemented",
  optimise: "optimize",
  optimised: "optimized",
  optimising: "optimizing",
  normalise: "normalize",
  normalised: "normalized",
  normalising: "normalizing",
  customise: "customize",
  customised: "customized",
  customising: "customizing",
  initialise: "initialize",
  initialised: "initialized",
  initialising: "initializing",
  finalise: "finalize",
  finalised: "finalized",
  finalising: "finalizing",
  utilises: "utilize",
  utilised: "utilized",
  utilising: "utilizing",
  orginize: "organize",
  orginised: "organized",
  orginising: "organizing",
}
