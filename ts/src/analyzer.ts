import { advisory } from "./advisory.js"
import { type UdlEnvelope, buildUdlEnvelope } from "./bridges.js"
import { parse } from "./parser.js"
import { jsonReport, terminalReport } from "./report.js"
import { AmbiguityScore } from "./scoring.js"

export class Analysis {
  result: ReturnType<typeof parse>
  score: AmbiguityScore
  udlEnvelope: UdlEnvelope | null

  constructor(text: string) {
    this.result = parse(text)
    this.score = new AmbiguityScore(this.result)
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
