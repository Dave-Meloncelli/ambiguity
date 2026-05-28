export { Analysis } from "./analyzer.js"
export { AmbiguityScore } from "./scoring.js"
export { parse, type ParseResult } from "./parser.js"
export { advisory, setSuppressed } from "./advisory.js"
export { getProfile, Profile } from "./profile.js"
export { jsonReport, terminalReport } from "./report.js"
export {
  buildUdlEnvelope,
  UdlEnvelopeSchema,
  type UdlEnvelope,
} from "./bridges.js"
export {
  CONTAINERS,
  VERB_TAXONOMY,
  KEYWORD_MAP,
  KNOWN_ACRONYMS,
  STEMMING_TABLE,
  specificityBand,
  containersForVerb,
  containersForKey,
  resolveAcronym,
  fuzzyVerbMatch,
} from "./containers.js"
export { detectLanguage } from "./language.js"
export {
  type CompareResult,
  compare,
  renderCompareReport,
} from "./compare.js"
export {
  type AuditResult,
  audit,
  renderAuditReport,
} from "./audit.js"
export {
  type Translation,
  translate,
  renderTranslateReport,
} from "./translate.js"
export {
  type Clarification,
  generateClarification,
  renderClarifyReport,
} from "./clarify.js"
export {
  type MemoryEntry,
  writeEntry,
  readEntries,
  summary as memorySummary,
} from "./memory.js"
export {
  type ImportResult,
  discover,
} from "./import_discover.js"
export {
  type RhetoricResult,
  analyzeRhetoric,
  renderRhetoricReport,
} from "./rhetoric.js"
export {
  type ChunkResult,
  chunk,
  renderChunkReport,
} from "./chunking.js"
export {
  type NlpResult,
  analyze as nlpAnalyze,
  renderNlpReport,
} from "./nlp_bridge.js"
export {
  type FlowTestResult,
  flowTest,
  renderFlowReport,
} from "./flow.js"
export {
  type HookConfig,
  type HookResult,
  AnthropicHook,
} from "./hooks.js"
