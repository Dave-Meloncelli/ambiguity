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
  specificityBand,
  containersForVerb,
  containersForKey,
  resolveAcronym,
} from "./containers.js"
export { detectLanguage } from "./language.js"
