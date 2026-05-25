import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs"
import { homedir } from "node:os"
import { join } from "node:path"
import { KEYWORD_MAP, KNOWN_ACRONYMS, VERB_TAXONOMY } from "./containers.js"
import type { ParseResult } from "./parser.js"
import type { AmbiguityScore } from "./scoring.js"

const PROFILE_DIR = join(homedir(), ".ambiguity")
const PROFILE_PATH = join(PROFILE_DIR, "profile.json")
const HISTORY_MAX = 500

export interface ProfileEntry {
  prompt: string
  score: number
  band: string
  verbSpecificity: number
  containerCount: number
  constraintCount: number
  advisory: string | null
  wordCount: number
  instructionCount: number
  verbs: string[]
  acronyms: string[]
  timestamp: string
}

interface ProfileData {
  entries: ProfileEntry[]
  dismissed: Record<string, number>
  learnedVerbs: Record<string, { containers: string[]; specificity: number; learnedAt: string }>
  learnedAcronyms: Record<string, string>
  learnedKeywords: Record<string, { containers: string[]; learnedAt: string }>
  scoreBaseline: number
  scoreStd: number | null
  threshold: number
}

export class Profile {
  entries: ProfileEntry[] = []
  dismissed: Record<string, number> = {}
  learnedVerbs: Record<string, { containers: string[]; specificity: number; learnedAt: string }> =
    {}
  learnedAcronyms: Record<string, string> = {}
  learnedKeywords: Record<string, { containers: string[]; learnedAt: string }> = {}
  scoreBaseline = 5.0
  scoreStd: number | null = null
  threshold = 4.0

  constructor() {
    this.load()
  }

  private load(): void {
    if (!existsSync(PROFILE_PATH)) return
    try {
      const raw = readFileSync(PROFILE_PATH, "utf-8")
      const data: ProfileData = JSON.parse(raw)
      this.entries = data.entries ?? []
      this.dismissed = data.dismissed ?? {}
      this.learnedVerbs = data.learnedVerbs ?? {}
      this.learnedAcronyms = data.learnedAcronyms ?? {}
      this.learnedKeywords = data.learnedKeywords ?? {}
      this.scoreBaseline = data.scoreBaseline ?? 5.0
      this.scoreStd = data.scoreStd ?? null
      this.threshold = data.threshold ?? 4.0
      this.recalibrate()
    } catch {
      // corrupt profile, start fresh
    }
  }

  private save(): void {
    if (!existsSync(PROFILE_DIR)) mkdirSync(PROFILE_DIR, { recursive: true })
    const data: ProfileData = {
      entries: this.entries.slice(-HISTORY_MAX),
      dismissed: this.dismissed,
      learnedVerbs: this.learnedVerbs,
      learnedAcronyms: this.learnedAcronyms,
      learnedKeywords: this.learnedKeywords,
      scoreBaseline: this.scoreBaseline,
      scoreStd: this.scoreStd,
      threshold: this.threshold,
    }
    writeFileSync(PROFILE_PATH, JSON.stringify(data, null, 2), "utf-8")
  }

  record(result: ParseResult, score: AmbiguityScore, adv: string | null): void {
    this.entries.push({
      prompt: result.text.slice(0, 200),
      score: Math.round(score.total * 10) / 10,
      band: score.band,
      verbSpecificity: Math.round(score.verbSpecificity * 100) / 100,
      containerCount: score.containerOverlap,
      constraintCount: score.constraintCount,
      advisory: adv,
      wordCount: result.wordCount,
      instructionCount: result.instructionCount,
      verbs: result.verbs,
      acronyms: result.acronyms.map((a) => a[0]),
      timestamp: new Date().toISOString(),
    })
    this.recalibrate()
    this.save()
  }

  dismiss(flagType: string): void {
    this.dismissed[flagType] = (this.dismissed[flagType] ?? 0) + 1
    this.save()
  }

  learnVerb(verb: string, containers?: string[], specificity?: number): void {
    const key = verb.toLowerCase()
    this.learnedVerbs[key] = {
      containers: containers ?? [],
      specificity: specificity ?? 0.5,
      learnedAt: new Date().toISOString(),
    }
    VERB_TAXONOMY[key] = { containers: containers ?? [], specificity: specificity ?? 0.5 }
    this.save()
  }

  learnAcronym(abbr: string, expansion: string): void {
    this.learnedAcronyms[abbr.toUpperCase()] = expansion
    KNOWN_ACRONYMS[abbr.toUpperCase()] = expansion
    this.save()
  }

  learnKeyword(keyword: string, containers?: string[]): void {
    const key = keyword.toLowerCase()
    this.learnedKeywords[key] = {
      containers: containers ?? [],
      learnedAt: new Date().toISOString(),
    }
    KEYWORD_MAP[key] = { containers: containers ?? [] }
    this.save()
  }

  private recalibrate(): void {
    if (this.entries.length < 10) return
    const recent = this.entries.slice(-50)
    const scores = recent.map((e) => e.score)
    const mean = scores.reduce((a, b) => a + b, 0) / scores.length
    const variance = scores.reduce((a, b) => a + (b - mean) ** 2, 0) / scores.length
    this.scoreBaseline = Math.round(mean * 10) / 10
    this.scoreStd = Math.round(Math.sqrt(variance) * 10) / 10
    this.threshold = Math.round((mean - this.scoreStd * 0.5) * 10) / 10
  }

  suppressedFlags(): Set<string> {
    const result = new Set<string>()
    for (const [flagType, count] of Object.entries(this.dismissed)) {
      if (count >= 3) result.add(flagType)
    }
    return result
  }

  adjustedThreshold(): number {
    return Math.max(2.0, Math.min(8.0, this.threshold))
  }
}

let _instance: Profile | null = null

export function getProfile(): Profile {
  if (!_instance) _instance = new Profile()
  return _instance
}
