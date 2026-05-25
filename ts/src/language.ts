/** Language detection and per-language configuration. */

export interface LanguageProfile {
  code: string
  name: string
  rtl: boolean
  tokenizationNotes: string
}

const LANGUAGE_PROFILES: Record<string, LanguageProfile> = {
  en: {
    code: "en",
    name: "English",
    rtl: false,
    tokenizationNotes: "BPE splits common words; 'I'll' may be 1-2 tokens",
  },
  zh: {
    code: "zh",
    name: "Chinese",
    rtl: false,
    tokenizationNotes: "Each character is typically 1 token; high token density",
  },
  ja: {
    code: "ja",
    name: "Japanese",
    rtl: false,
    tokenizationNotes: "Mixed script; kanji compounds may split unexpectedly",
  },
  ko: {
    code: "ko",
    name: "Korean",
    rtl: false,
    tokenizationNotes: "Each hangul syllable block is 1-2 tokens",
  },
  ar: {
    code: "ar",
    name: "Arabic",
    rtl: true,
    tokenizationNotes: "RTL; prefix/suffix morphology creates variable token splits",
  },
  he: {
    code: "he",
    name: "Hebrew",
    rtl: true,
    tokenizationNotes: "RTL; prefix chains increase token count",
  },
  fr: {
    code: "fr",
    name: "French",
    rtl: false,
    tokenizationNotes: "Article+noun contractions may fuse tokens",
  },
  de: {
    code: "de",
    name: "German",
    rtl: false,
    tokenizationNotes: "Compound nouns split into multiple tokens",
  },
  es: {
    code: "es",
    name: "Spanish",
    rtl: false,
    tokenizationNotes: "Verb conjugation produces longer token sequences",
  },
  pt: {
    code: "pt",
    name: "Portuguese",
    rtl: false,
    tokenizationNotes: "Similar token profile to Spanish",
  },
  ru: {
    code: "ru",
    name: "Russian",
    rtl: false,
    tokenizationNotes: "Cyrillic; rich morphology creates variable token splits",
  },
  hi: {
    code: "hi",
    name: "Hindi",
    rtl: false,
    tokenizationNotes: "Devanagari script; matra combinations affect tokenization",
  },
}

const COMMON_EN_WORDS = new Set([
  "the",
  "be",
  "to",
  "of",
  "and",
  "a",
  "in",
  "that",
  "have",
  "i",
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
  "write",
  "function",
  "list",
  "code",
  "data",
  "file",
  "string",
  "number",
  "value",
  "return",
  "class",
  "import",
  "print",
  "input",
  "output",
  "error",
  "test",
  "sort",
  "python",
  "javascript",
  "typescript",
  "html",
  "css",
])

function hasScript(text: string, ranges: [number, number][]): boolean {
  for (const [lo, hi] of ranges) {
    for (let i = 0; i < text.length; i++) {
      const cp = text.codePointAt(i)
      if (cp !== undefined && cp >= lo && cp <= hi) return true
    }
  }
  return false
}

export function detectLanguage(text: string): LanguageProfile {
  if (!text.trim()) return LANGUAGE_PROFILES.en

  if (
    hasScript(text, [
      [0x4e00, 0x9fff],
      [0x3400, 0x4dbf],
    ])
  )
    return LANGUAGE_PROFILES.zh
  if (
    hasScript(text, [
      [0x3040, 0x309f],
      [0x30a0, 0x30ff],
    ])
  )
    return LANGUAGE_PROFILES.ja
  if (hasScript(text, [[0xac00, 0xd7af]])) return LANGUAGE_PROFILES.ko
  if (
    hasScript(text, [
      [0x0600, 0x06ff],
      [0x0750, 0x077f],
    ])
  )
    return LANGUAGE_PROFILES.ar
  if (hasScript(text, [[0x0590, 0x05ff]])) return LANGUAGE_PROFILES.he
  if (hasScript(text, [[0x0400, 0x04ff]])) return LANGUAGE_PROFILES.ru
  if (hasScript(text, [[0x0900, 0x097f]])) return LANGUAGE_PROFILES.hi

  const words = text.match(/[a-zA-Z]+/g)
  if (!words) return LANGUAGE_PROFILES.en

  const lowerWords = new Set(words.map((w) => w.toLowerCase()))
  let enCount = 0
  for (const w of lowerWords) {
    if (COMMON_EN_WORDS.has(w)) enCount++
  }
  const enRatio = enCount / lowerWords.size

  return enRatio > 0.15 ? LANGUAGE_PROFILES.en : LANGUAGE_PROFILES.en
}

export function tokenizationWarning(text: string, profile: LanguageProfile): string | undefined {
  if (profile.code === "en") {
    const contractions = text.match(/\b\w+'\w+\b/g)
    if (contractions?.length)
      return `Contains ${contractions.length} contraction(s); may split into unexpected tokens`
    return undefined
  }
  return `${profile.name} tokenization: ${profile.tokenizationNotes}`
}
