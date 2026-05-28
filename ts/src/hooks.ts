import { Analysis } from "./analyzer.js"

export interface HookResult {
  blocked: boolean
  score: number
  band: string
  indicators: string[]
}

export interface HookConfig {
  gate?: number
  onExceed?: "block" | "warn"
}

function handleResult(score: number, band: string, threshold: number, action?: "block" | "warn"): HookResult {
  if (score < threshold) {
    return { blocked: false, score, band, indicators: [] }
  }
  const msg = `[ambiguity] score ${score.toFixed(1)}/${band} exceeds gate ${threshold.toFixed(1)}`
  if (action === "block") {
    return { blocked: true, score, band, indicators: [msg] }
  }
  console.warn(`WARNING: ${msg}`)
  return { blocked: false, score, band, indicators: [msg] }
}

export class AnthropicHook {
  private config: HookConfig

  constructor(config?: HookConfig) {
    this.config = config ?? {}
  }

  analyzePrompt(text: string): HookResult {
    const analysis = new Analysis(text)
    return handleResult(analysis.score.total, analysis.score.band, this.config.gate ?? 6.0, this.config.onExceed)
  }
}

export class OpenaiHook {
  private config: HookConfig

  constructor(config?: HookConfig) {
    this.config = config ?? {}
  }

  analyzePrompt(text: string): HookResult {
    const analysis = new Analysis(text)
    return handleResult(analysis.score.total, analysis.score.band, this.config.gate ?? 6.0, this.config.onExceed)
  }
}
