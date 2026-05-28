import { advisory } from "./advisory.js"
import { type UdlEnvelope, buildUdlEnvelope } from "./bridges.js"
import { parse } from "./parser.js"
import { jsonReport, terminalReport } from "./report.js"
import { AmbiguityScore } from "./scoring.js"
import { analyzeRhetoric } from "./rhetoric.js"
import type { RhetoricResult } from "./rhetoric.js"
import { chunk } from "./chunking.js"
import type { ChunkResult } from "./chunking.js"

export class Analysis {
  result: ReturnType<typeof parse>
  rhetoric: RhetoricResult
  chunking: ChunkResult
  score: AmbiguityScore
  udlEnvelope: UdlEnvelope | null

  constructor(text: string) {
    this.result = parse(text)
    this.rhetoric = analyzeRhetoric(text)
    this.chunking = chunk(text)
    this.score = new AmbiguityScore(this.result, this.rhetoric, this.chunking)
    this.udlEnvelope = buildUdlEnvelope(this.result, this.score)
  }

  terminalReport(): string {
    const udlInfo = this.udlEnvelope
      ? `envelope written (${JSON.stringify(this.udlEnvelope).length} bytes)`
      : undefined
    return terminalReport(this.result, this.score, udlInfo)
  }

  jsonReport(): Record<string, unknown> {
    return jsonReport(this.result, this.score)
  }

  fullOutput(includeUdl: boolean): Record<string, unknown> {
    const output = this.jsonReport()
    if (includeUdl && this.udlEnvelope) {
      output._udl_envelope = this.udlEnvelope
    }
    return output
  }
}
