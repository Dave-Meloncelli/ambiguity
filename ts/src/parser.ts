/** Deterministic prompt parser — extracts verbs, keywords, constraints, references. */

import {
  KEYWORD_MAP,
  KNOWN_ACRONYMS,
  SPELLING_CORRECTIONS,
  VERB_TAXONOMY,
  fuzzyVerbMatch,
  levenshteinDistance,
} from "./containers.js"

// augment COMMON_WORDS with all known verbs and keywords for better space-split detection
const VERB_SET = new Set(Object.keys(VERB_TAXONOMY))
const KEYWORD_SET = new Set(Object.keys(KEYWORD_MAP))

export interface FuzzyMatch {
  original: string
  corrected: string
  distance: number
}

export interface StutterPair {
  word: string
  occurrences: number
}

export interface MissingSpace {
  combined: string
  split: [string, string]
}

export interface ParseResult {
  text: string
  verbs: string[]
  fuzzyVerbs: FuzzyMatch[]
  keywords: string[]
  constraints: string[]
  acronyms: [string, string][]
  unqualifiedRefs: string[]
  typoWords: FuzzyMatch[]
  stutterWords: StutterPair[]
  missingSpaces: MissingSpace[]
  repeatedChars: string[]
  hasTerminalPunctuation: boolean
  wordCount: number
  sentenceCount: number
  instructionCount: number
}

const VERB_PATTERN = new RegExp(`\\b(${Object.keys(VERB_TAXONOMY).join("|")})\\b`, "gi")

const CONSTRAINT_PATTERNS: [RegExp, string][] = [
  [/\b(only|exactly|specifically|strictly)\b/i, "exact"],
  [/\b(must|need to|have to|required)\b/i, "requirement"],
  [/\b(don't|do not|without|avoid|never|no |not)\b/i, "negation"],
  [/\b(import|require|dependency|library)\b/i, "dependency"],
]

const ACRONYM_PATTERN = /\b([A-Z]{2,})\b/g

// only flag as unqualified when there's NO preceding qualifier word
const UNQUALIFIED_PATTERNS = [
  /\bthe (thing|file|solution)\b/i,
  /\bit\b/i,
  /\b(as we discussed|as i said|as mentioned|as we know)\b/i,
]

const SENTENCE_SPLIT = /[.!?]+/
const INSTRUCTION_SPLIT = /[,;]|(?:\band\b|\bthen\b|\bnext\b|\bafter that\b)/i

// common words used to detect missing spaces in concatenated tokens
// seeded with frequent English words + all known verbs + all known keywords
function buildCommonWords(): Set<string> {
  const base = new Set([
    "the",
    "be",
    "to",
    "of",
    "and",
    "a",
    "in",
    "that",
    "have",
    "it",
    "for",
    "not",
    "on",
    "with",
    "he",
    "as",
    "you",
    "do",
    "at",
    "this",
    "but",
    "his",
    "by",
    "from",
    "they",
    "we",
    "say",
    "her",
    "she",
    "or",
    "an",
    "will",
    "my",
    "one",
    "all",
    "would",
    "there",
    "their",
    "what",
    "so",
    "up",
    "out",
    "if",
    "about",
    "who",
    "get",
    "which",
    "go",
    "me",
    "when",
    "make",
    "can",
    "like",
    "time",
    "no",
    "just",
    "him",
    "know",
    "take",
    "people",
    "into",
    "year",
    "your",
    "good",
    "some",
    "could",
    "them",
    "see",
    "other",
    "than",
    "then",
    "now",
    "look",
    "only",
    "come",
    "its",
    "over",
    "think",
    "also",
    "back",
    "after",
    "use",
    "two",
    "how",
    "our",
    "work",
    "first",
    "well",
    "way",
    "even",
    "new",
    "want",
    "because",
    "any",
    "these",
    "give",
    "day",
    "most",
    "us",
    "need",
    "should",
    "does",
    "code",
    "file",
    "test",
    "data",
    "function",
    "class",
    "method",
    "module",
    "app",
    "api",
    "ui",
    "fix",
    "add",
    "remove",
    "change",
    "update",
    "read",
    "write",
    "run",
    "set",
    "get",
    "show",
    "help",
    "info",
    "list",
    "sort",
    "implement",
    "convert",
    "verify",
    "explain",
    "create",
    "describe",
    "feature",
    "system",
    "config",
    "schema",
    "query",
    "route",
    "view",
    "page",
    "link",
    "path",
    "name",
    "type",
    "mode",
    "role",
    "flag",
    "user",
    "admin",
    "guest",
    "owner",
    "table",
    "field",
    "form",
    "item",
    "list",
    "log",
    "map",
    "key",
    "doc",
    "row",
    "col",
  ])
  for (const v of VERB_SET) base.add(v)
  for (const k of KEYWORD_SET) base.add(k)
  return base
}
const COMMON_WORDS = buildCommonWords()

function detectMissingSpaces(wordTokens: string[]): MissingSpace[] {
  const found: MissingSpace[] = []
  const seen = new Set<string>()
  for (const token of wordTokens) {
    if (token.length < 8 || seen.has(token)) continue
    // try splits at positions 3..len-3 so each half is at least 3 chars
    for (let i = 3; i < token.length - 3; i++) {
      const left = token.slice(0, i)
      const right = token.slice(i)
      if (COMMON_WORDS.has(left) && COMMON_WORDS.has(right)) {
        found.push({ combined: token, split: [left, right] })
        seen.add(token)
        break
      }
    }
  }
  return found
}

function detectStutter(wordTokens: string[]): StutterPair[] {
  const found: StutterPair[] = []
  const seen = new Set<string>()
  for (let i = 1; i < wordTokens.length; i++) {
    if (wordTokens[i] === wordTokens[i - 1] && !seen.has(wordTokens[i])) {
      seen.add(wordTokens[i])
      let count = 2
      while (i + count - 1 < wordTokens.length && wordTokens[i + count - 1] === wordTokens[i]) {
        count++
      }
      found.push({ word: wordTokens[i], occurrences: count })
    }
  }
  return found
}

function detectRepeatedChars(wordTokens: string[]): string[] {
  const found: string[] = []
  const seen = new Set<string>()
  const repeatPattern = /(.)\1{2,}/ // 3+ same chars in a row
  for (const token of wordTokens) {
    if (token.length > 3 && repeatPattern.test(token) && !seen.has(token)) {
      seen.add(token)
      found.push(token)
    }
  }
  return found
}

export function parse(text: string): ParseResult {
  const wordTokens = text.toLowerCase().match(/\b[a-z]+\b/g) ?? []
  const verbs: string[] = []
  const fuzzyVerbs: FuzzyMatch[] = []
  const typoWords: FuzzyMatch[] = []
  const seenVerbs = new Set<string>()
  const seenFuzzy = new Set<string>()
  const seenTypo = new Set<string>()

  for (const token of wordTokens) {
    const fuzzy = fuzzyVerbMatch(token)
    if (fuzzy && fuzzy.distance === 0 && !seenVerbs.has(fuzzy.verb)) {
      seenVerbs.add(fuzzy.verb)
      verbs.push(fuzzy.verb)
    } else if (fuzzy && fuzzy.distance > 0 && !seenFuzzy.has(fuzzy.verb)) {
      seenFuzzy.add(fuzzy.verb)
      verbs.push(fuzzy.verb)
      fuzzyVerbs.push({ original: token, corrected: fuzzy.verb, distance: fuzzy.distance })
    } else if (!fuzzy) {
      const correction = SPELLING_CORRECTIONS[token]
      if (correction && !seenTypo.has(token)) {
        seenTypo.add(token)
        typoWords.push({
          original: token,
          corrected: correction,
          distance: levenshteinDistance(token, correction),
        })
      }
    }
  }

  // fallback if no verbs found by token scan, try the all-at-once regex
  if (verbs.length === 0) {
    const verbMatches = text.match(VERB_PATTERN)
    const regexVerbs = [...new Set((verbMatches ?? []).map((v) => v.toLowerCase()))]
    for (const v of regexVerbs) {
      if (!seenVerbs.has(v)) {
        seenVerbs.add(v)
        verbs.push(v)
      }
    }
  }

  const keywords: string[] = []
  const kwSet = new Set<string>()
  for (const kw of Object.keys(KEYWORD_MAP)) {
    const re = new RegExp(`\\b${kw.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "i")
    if (re.test(text) && !kwSet.has(kw)) {
      kwSet.add(kw)
      keywords.push(kw)
    }
  }

  const constraints: string[] = []
  for (const [pattern, kind] of CONSTRAINT_PATTERNS) {
    if (pattern.test(text)) constraints.push(kind)
  }

  const acronyms: [string, string][] = []
  const acrSeen = new Set<string>()
  const matches = text.matchAll(ACRONYM_PATTERN)
  for (const match of matches) {
    const word = match[1]
    const expansion = KNOWN_ACRONYMS[word]
    if (expansion && !acrSeen.has(word)) {
      acrSeen.add(word)
      acronyms.push([word, expansion])
    }
  }

  const unqualifiedRefs: string[] = []
  for (const pattern of UNQUALIFIED_PATTERNS) {
    const matches = text.match(pattern)
    if (matches) {
      for (const m of matches) {
        const trimmed = m.toLowerCase().trim()
        if (trimmed && !unqualifiedRefs.includes(trimmed)) {
          unqualifiedRefs.push(trimmed)
        }
      }
    }
  }

  const wordCount = (text.match(/\b\w+\b/g) ?? []).length

  const sentences = text.split(SENTENCE_SPLIT).filter((s) => s.trim().length > 0)
  const sentenceCount = sentences.length

  const instructions = text.split(INSTRUCTION_SPLIT).filter((s) => s.trim().length > 0)
  const instructionCount = instructions.length

  const missingSpaces = detectMissingSpaces(wordTokens)

  const stutterWords = detectStutter(wordTokens)

  const repeatedChars = detectRepeatedChars(wordTokens)

  const trimmed = text.trim()
  const hasTerminalPunctuation = trimmed.length > 0 && /[.!?]/.test(trimmed[trimmed.length - 1])

  return {
    text,
    verbs,
    fuzzyVerbs,
    keywords,
    constraints,
    acronyms,
    unqualifiedRefs,
    typoWords,
    stutterWords,
    missingSpaces,
    repeatedChars,
    hasTerminalPunctuation,
    wordCount,
    sentenceCount,
    instructionCount,
  }
}
