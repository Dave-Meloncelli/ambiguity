/** UDL envelope schema and factory (no Federation dependency). */

import { z } from "zod"
import { containersForVerb } from "./containers.js"
import type { ParseResult } from "./parser.js"
import type { AmbiguityScore } from "./scoring.js"

const BridgePayload = z.object({
  job_story: z.string(),
  proof_condition: z.string(),
  baseline_shape: z.string(),
  evidence_signals: z.array(z.string()),
  constraint_summary: z.array(z.string()),
  status: z.string(),
})

export const UdlEnvelopeSchema = z.object({
  envelope_id: z.string(),
  format: z.literal("udl_v1"),
  surface: z.literal("ambiguity_framework"),
  agent_id: z.literal("ambiguity_analyzer"),
  intent: z.literal("Analyze prompt for translation ambiguity"),
  created_at: z.string(),
  raw_payload: z.object({
    prompt: z.string(),
    word_count: z.number(),
    instruction_count: z.number(),
  }),
  normalized_view: z.object({
    ambiguity_score: z.number(),
    band: z.string(),
    verb_specificity: z.number(),
    container_count: z.number(),
    constraint_count: z.number(),
    entropy_indicator_count: z.number(),
    unqualified_refs: z.array(z.string()),
  }),
  jtbd_bridge: BridgePayload,
})

export type UdlEnvelope = z.infer<typeof UdlEnvelopeSchema>

type HexStr = string

function uuid(): HexStr {
  const hex = "0123456789abcdef"
  let s = ""
  for (let i = 0; i < 32; i++) {
    s += hex[Math.floor(Math.random() * 16)]
  }
  return `udl_${s}`
}

export function buildUdlEnvelope(result: ParseResult, score: AmbiguityScore): UdlEnvelope {
  return {
    envelope_id: uuid(),
    format: "udl_v1",
    surface: "ambiguity_framework",
    agent_id: "ambiguity_analyzer",
    intent: "Analyze prompt for translation ambiguity",
    created_at: new Date().toISOString(),
    raw_payload: {
      prompt: result.text,
      word_count: result.wordCount,
      instruction_count: result.instructionCount,
    },
    normalized_view: {
      ambiguity_score: Math.round(score.total * 10) / 10,
      band: score.band,
      verb_specificity: Math.round(score.verbSpecificity * 100) / 100,
      container_count: score.containerOverlap,
      constraint_count: score.constraintCount,
      entropy_indicator_count: score.entropyIndicators.length,
      unqualified_refs: result.unqualifiedRefs,
    },
    jtbd_bridge: {
      job_story: "Analyze prompt for ambiguity before LLM processing",
      proof_condition:
        "ambiguity_score < 6.0 AND verb_specificity > 0.3 AND no critical entropy indicators",
      baseline_shape: result.text,
      evidence_signals: score.entropyIndicators,
      constraint_summary: result.constraints,
      status: "analyzed",
    },
  }
}
