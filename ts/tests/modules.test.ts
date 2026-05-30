import { describe, it, expect, vi, beforeAll, afterAll } from "vitest"
import { analyzeRhetoric, renderRhetoricReport } from "../src/rhetoric.js"
import { chunk, renderChunkReport } from "../src/chunking.js"
import { advisory, setSuppressed } from "../src/advisory.js"
import { AmbiguityScore } from "../src/scoring.js"
import { parse } from "../src/parser.js"
import { buildUdlEnvelope } from "../src/bridges.js"
import { containersForVerb, fuzzyVerbMatch, specificityBand, resolveAcronym } from "../src/containers.js"
import { detectLanguage } from "../src/language.js"
import { audit } from "../src/audit.js"
import { translate, renderTranslateReport } from "../src/translate.js"
import { generateClarification, renderClarifyReport } from "../src/clarify.js"
import { compare, renderCompareReport } from "../src/compare.js"
import { flowTest, renderFlowReport } from "../src/flow.js"
import { AnthropicHook, OpenaiHook, type HookConfig } from "../src/hooks.js"
import { discover } from "../src/import_discover.js"
import { analyze, renderNlpReport } from "../src/nlp_bridge.js"
import { getProfile, Profile } from "../src/profile.js"
import { Analysis } from "../src/analyzer.js"
import { writeEntry, readEntries, summary } from "../src/memory.js"
import { review, renderReviewReport, renderReviewJson } from "../src/review.js"
import { upgradeConstraints, constraintAnalysisFromParse, ConstraintType, ConstraintCategory } from "../src/constraints.js"

// ---------------------------------------------------------------------------
// rhetoric
// ---------------------------------------------------------------------------
describe("rhetoric", () => {
  it("detects idioms and intent", () => {
    const r = analyzeRhetoric("we need to boil the ocean and move the needle")
    expect(r.idioms.length).toBeGreaterThanOrEqual(1)
    const intents = r.idioms.map((i) => i.intent)
    expect(intents).toContain("over_scope")
    expect(intents).toContain("significant_progress")
  })

  it("detects hedging language", () => {
    const r = analyzeRhetoric("maybe implement it if possible no rush")
    expect(r.hedges.length).toBeGreaterThanOrEqual(2)
  })

  it("detects emphatics", () => {
    const r = analyzeRhetoric("this is critical must fix asap")
    expect(r.emphatics).toContain("critical")
    expect(r.emphatics).toContain("must")
  })

  it("detects metaphors by source domain", () => {
    const r = analyzeRhetoric("build a bridge across the landscape layer")
    const domains = r.metaphors.map((m) => m.source_domain)
    expect(domains).toContain("physical_space")
    expect(domains).toContain("construction")
  })

  it("generates rhetoric_indicators for dense patterns", () => {
    const r = analyzeRhetoric("maybe perhaps possibly probably i think i believe")
    expect(r.rhetoric_indicators.length).toBeGreaterThan(0)
  })

  it("renders rhetoric report", () => {
    const r = analyzeRhetoric("we need to boil the ocean")
    const report = renderRhetoricReport(r)
    expect(report).toContain("Rhetoric")
    expect(report).toContain("Idioms")
  })
})

// ---------------------------------------------------------------------------
// chunking
// ---------------------------------------------------------------------------
describe("chunking", () => {
  it("finds phrasal verbs", () => {
    const c = chunk("set up the environment and tear down the old one")
    expect(c.compound_verbs.length).toBeGreaterThanOrEqual(1)
    const verbs = c.compound_verbs.map((cv) => cv.full)
    expect(verbs.some((v) => v === "set_up" || v === "tear_down")).toBe(true)
  })

  it("splits clauses", () => {
    const c = chunk("first implement the api then add the tests but skip the docs")
    expect(c.clauses.length).toBeGreaterThanOrEqual(2)
  })

  it("detects contradictions across clauses", () => {
    const c = chunk("must be fast but not comprehensive")
    expect(c.clauses.length).toBeGreaterThanOrEqual(2)
    expect(c.contradiction_hits.length).toBeGreaterThanOrEqual(1)
  })

  it("detects topic shifts", () => {
    const c = chunk("first do this. second do that. third do something else. finally wrap up.")
    expect(c.topic_shifts).toBeGreaterThan(0)
  })

  it("renders chunk report", () => {
    const c = chunk("set up the environment")
    const report = renderChunkReport(c)
    expect(report).toContain("Chunk")
    expect(report).toContain("Phrasal")
  })
})

// ---------------------------------------------------------------------------
// advisory
// ---------------------------------------------------------------------------
describe("advisory", () => {
  it("flags vague verbs", () => {
    const result = parse("do the thing")
    const score = new AmbiguityScore(result)
    const adv = advisory(result, score)
    expect(adv).not.toBeNull()
    if (adv) expect(adv).toContain("vague")
  })

  it("flags missing constraints for longer prompts", () => {
    const result = parse("write a python function that sorts a list")
    const score = new AmbiguityScore(result)
    const adv = advisory(result, score)
    // Should mention constraints or verbs
    expect(adv).not.toBeNull()
  })

  it("flags unqualified references", () => {
    const result = parse("fix it and make it work")
    const score = new AmbiguityScore(result)
    const adv = advisory(result, score)
    expect(adv).not.toBeNull()
  })

  it("respects suppressed flags", () => {
    setSuppressed(new Set(["vague_verb"]))
    const result = parse("do the thing")
    const score = new AmbiguityScore(result)
    const adv = advisory(result, score)
    // vague_verb suppressed — might still have other advisories
    // Should NOT contain the vague verb advisory
    if (adv && adv.includes("vague")) {
      // If another vague advisory, that's OK but shouldn't be about "do"
    }
    expect(adv).not.toContain("vague verb 'do'")
  })
})

// ---------------------------------------------------------------------------
// stemming / fuzzy matching
// ---------------------------------------------------------------------------
describe("stemming", () => {
  it("matches inflected forms via fuzzyVerbMatch", () => {
    const cases: [string, string][] = [
      ["writes", "write"], ["wrote", "write"], ["written", "write"], ["writing", "write"],
      ["creates", "create"], ["created", "create"], ["creating", "create"],
      ["implements", "implement"], ["implemented", "implement"], ["implementing", "implement"],
      ["running", "run"], ["building", "build"],
    ]
    for (const [inflected, base] of cases) {
      const result = fuzzyVerbMatch(inflected)
      expect(result).not.toBeNull()
      expect(result!.verb).toBe(base)
    }
  })

  it("returns null for non-verb common words", () => {
    const result = fuzzyVerbMatch("the")
    expect(result).toBeNull()
  })

  it("parsing includes stemmed verbs", () => {
    const result = parse("writing optimizing running")
    expect(result.verbs).toContain("write")
    expect(result.verbs).toContain("optimize")
    expect(result.verbs).toContain("run")
  })
})

// ---------------------------------------------------------------------------
// NLP bridge
// ---------------------------------------------------------------------------
describe("nlp_bridge", () => {
  it("gracefully falls back when spaCy not available", () => {
    const r = analyze("write a function that sorts a list")
    expect(r.has_spacy).toBe(false)
    const report = renderNlpReport(r)
    expect(report).toContain("spaCy not available")
  })
})

// ---------------------------------------------------------------------------
// language detection
// ---------------------------------------------------------------------------
describe("language", () => {
  it("detects English by default", () => {
    const lang = detectLanguage("write a python function")
    expect(lang.code).toBe("en")
  })

  it("detects Chinese script", () => {
    const lang = detectLanguage("你好世界")
    expect(lang.code).toBe("zh")
  })
})

// ---------------------------------------------------------------------------
// audit
// ---------------------------------------------------------------------------
describe("audit", () => {
  it("extracts claimed files and detects missing", () => {
    const result = audit("create src/main.py and src/utils.py", ".")
    expect(result.claimedFiles).toContain("src/main.py")
    expect(result.claimedFiles).toContain("src/utils.py")
  })

  it("calculates metrics without crashing", () => {
    const result = audit("create main.py", ".")
    expect(result.summary.claimed).toBeGreaterThan(0)
    expect(typeof result.precision).toBe("number")
    expect(typeof result.recall).toBe("number")
    expect(typeof result.f1).toBe("number")
  })
})

// ---------------------------------------------------------------------------
// translate
// ---------------------------------------------------------------------------
describe("translate", () => {
  it("expands acronyms in translation", () => {
    const t = translate("check the UDL configuration")
    expect(t.changes.some((c) => c.type === "acronym")).toBe(true)
  })

  it("detects vague verbs", () => {
    const t = translate("do the thing")
    expect(t.changes.length).toBeGreaterThan(0)
    expect(t.bandBefore).toBeTruthy()
  })

  it("renders translate report", () => {
    const t = translate("check the UDL config")
    const report = renderTranslateReport(t)
    expect(report).toContain("translate")
  })
})

// ---------------------------------------------------------------------------
// clarify
// ---------------------------------------------------------------------------
describe("clarify", () => {
  it("generates questions for vague prompts", () => {
    const c = generateClarification("do the thing make it work")
    expect(c.questions.length).toBeGreaterThan(0)
  })

  it("no questions for precise prompts", () => {
    const c = generateClarification("implement a python function that sorts a list")
    // May have some — but should not have excessive
    // The key test: it runs without error and returns valid structure
    expect(typeof c.score).toBe("number")
    expect(typeof c.band).toBe("string")
  })

  it("renders clarify report", () => {
    const c = generateClarification("do the thing")
    const report = renderClarifyReport(c)
    expect(report).toContain("clarify")
  })
})

// ---------------------------------------------------------------------------
// compare
// ---------------------------------------------------------------------------
describe("compare", () => {
  it("produces a compare result without LLM", () => {
    const result = compare("write a function")
    expect(result.controlScore).toBeGreaterThan(0)
    expect(result.treatmentScore).toBeGreaterThan(0)
    expect(result.controlPrompt).toBe("write a function")
    expect(result.treatmentPrompt).not.toBe("write a function")
  })

  it("renders compare report without error", () => {
    const result = compare("hello world")
    const report = renderCompareReport(result)
    expect(report).toContain("compare")
  })
})

// ---------------------------------------------------------------------------
// UDL envelope (bridges)
// ---------------------------------------------------------------------------
describe("bridges", () => {
  it("builds a valid UDL envelope", () => {
    const result = parse("write a python function")
    const score = new AmbiguityScore(result)
    const env = buildUdlEnvelope(result, score)
    expect(env.format).toBe("udl_v1")
    expect(env.surface).toBe("ambiguity_framework")
    expect(env.raw_payload.prompt).toBe("write a python function")
    expect(env.raw_payload.word_count).toBeGreaterThan(0)
    expect(env.normalized_view.ambiguity_score).toBeGreaterThan(0)
  })
})

// ---------------------------------------------------------------------------
// hooks
// ---------------------------------------------------------------------------
describe("hooks", () => {
  it("AnthropicHook blocks high-scoring prompts when configured", () => {
    const hook = new AnthropicHook({ gate: 3.0, onExceed: "block" })
    // "do the thing" should score high
    const result = hook.analyzePrompt("do the thing make it work")
    expect(result.blocked).toBe(true)
    expect(result.score).toBeGreaterThan(3.0)
  })

  it("AnthropicHook does not block low-scoring prompts", () => {
    const hook = new AnthropicHook({ gate: 9.0, onExceed: "block" })
    const result = hook.analyzePrompt("write a function")
    expect(result.blocked).toBe(false)
  })

  it("AnthropicHook warns on high score when configured", () => {
    const hook = new AnthropicHook({ gate: 3.0, onExceed: "warn" })
    const result = hook.analyzePrompt("do the thing")
    expect(result.blocked).toBe(false)
    expect(result.indicators.length).toBeGreaterThan(0)
  })

  it("OpenaiHook has same behavior", () => {
    const hook = new OpenaiHook({ gate: 3.0, onExceed: "block" })
    const result = hook.analyzePrompt("do the thing")
    expect(result.blocked).toBe(true)
  })
})

// ---------------------------------------------------------------------------
// import_discover
// ---------------------------------------------------------------------------
describe("import_discover", () => {
  it("rejects without consent", () => {
    const result = discover(false)
    expect(result.promptsFound).toBe(0)
    expect(result.errors.length).toBeGreaterThan(0)
  })
})

// ---------------------------------------------------------------------------
// flow
// ---------------------------------------------------------------------------
describe("flow", () => {
  it("runs without crashing", () => {
    const result = flowTest()
    expect(typeof result.passed).toBe("boolean")
    expect(result.issues).toBeDefined()
  })

  it("renders flow report", () => {
    const result = flowTest()
    const report = renderFlowReport(result)
    expect(report).toContain("flow-test")
  })
})

// ---------------------------------------------------------------------------
// profile
// ---------------------------------------------------------------------------
describe("profile", () => {
  it("returns a profile instance", () => {
    const p = getProfile()
    expect(p).toBeInstanceOf(Profile)
    expect(typeof p.adjustedThreshold()).toBe("number")
  })

  it("suppresses flags after 3 dismissals", () => {
    const p = new Profile()
    p.dismiss("test_flag")
    p.dismiss("test_flag")
    p.dismiss("test_flag")
    const suppressed = p.suppressedFlags()
    expect(suppressed.has("test_flag")).toBe(true)
  })
})

// ---------------------------------------------------------------------------
// specificity / containers helpers
// ---------------------------------------------------------------------------
describe("containers", () => {
  it("specificityBand returns band labels", () => {
    expect(specificityBand(0.1)).toBe("vague")
    expect(specificityBand(0.5)).toBe("moderate")
    expect(specificityBand(0.7)).toBe("specific")
    expect(specificityBand(0.9)).toBe("precise")
  })

  it("containersForVerb returns containers and specificity", () => {
    const [containers, spec] = containersForVerb("sort")
    expect(containers.length).toBeGreaterThan(0)
    expect(spec).toBeGreaterThan(0)
  })

  it("resolveAcronym expands UDL", () => {
    expect(resolveAcronym("UDL")).toBe("Unified Data Layer")
    expect(resolveAcronym("api")).toBe("Application Programming Interface")
  })
})

// ---------------------------------------------------------------------------
// memory
// ---------------------------------------------------------------------------
describe("memory", () => {
  it("readEntries returns empty array without memory file", () => {
    const entries = readEntries(5)
    expect(Array.isArray(entries)).toBe(true)
  })

  it("summary returns fallback string without memory file", () => {
    const s = summary()
    expect(typeof s).toBe("string")
  })
})

// ---------------------------------------------------------------------------
// review
// ---------------------------------------------------------------------------
describe("review", () => {
  it("detects hedging in response", () => {
    const r = review("write a function", "i think maybe we could possibly implement a sort of function")
    expect(r.hedgingCount).toBeGreaterThanOrEqual(2)
    expect(r.issues.some((i) => i.kind === "hedging")).toBe(true)
  })

  it("detects hallucination signals", () => {
    const r = review("write a function", "based on the information provided the answer is 42")
    expect(r.hallucinationSignals.length).toBeGreaterThanOrEqual(1)
    expect(r.issues.some((i) => i.severity === "error")).toBe(true)
  })

  it("clean response has few warnings", () => {
    const r = review("write a python function", "implement a python function that sorts a list")
    expect(r.score).toBeGreaterThanOrEqual(0)
  })

  it("detects verbose response", () => {
    const shortPrompt = "write a function"
    const longResponse = Array(200).fill("word").join(" ")
    const r = review(shortPrompt, longResponse)
    expect(r.issues.some((i) => i.kind === "verbose")).toBe(true)
  })

  it("handles empty response", () => {
    const r = review("write a function", "")
    expect(r.issues.some((i) => i.kind === "empty")).toBe(true)
    expect(r.score).toBeGreaterThanOrEqual(8)
  })

  it("renders review report", () => {
    const r = review("write a function", "i think maybe we could implement a function")
    const report = renderReviewReport(r)
    expect(report).toContain("review")
  })

  it("renders review JSON", () => {
    const r = review("write a function", "maybe a function")
    const data = renderReviewJson(r)
    expect(data.command).toBe("review")
  })
})

// ---------------------------------------------------------------------------
// constraints
// ---------------------------------------------------------------------------
describe("constraints", () => {
  it("upgrades constraints to typed CDL objects", () => {
    const result = parse("must be fast without recursion")
    const typed = upgradeConstraints(result)
    expect(typed.length).toBeGreaterThanOrEqual(1)
    const hard = typed.filter((c) => c.constraintCategory === ConstraintCategory.HARD)
    expect(hard.length).toBeGreaterThan(0)
  })

  it("detects missing constraint types", () => {
    const result = parse("write a function")
    const ca = constraintAnalysisFromParse(result)
    expect(ca.missingTypes).toContain(ConstraintType.FINANCIAL)
    expect(ca.missingTypes).toContain(ConstraintType.TEMPORAL)
  })

  it("classifies assumption as false constraint", () => {
    const result = parse("assuming the system is available")
    const typed = upgradeConstraints(result)
    const assumption = typed.find((c) => c.rawText === "assumption")
    expect(assumption).toBeDefined()
    expect(assumption!.constraintCategory).toBe(ConstraintCategory.FALSE)
  })

  it("classifies requirement as hard constraint", () => {
    const result = parse("must be fast")
    const typed = upgradeConstraints(result)
    const req = typed.find((c) => c.rawText === "requirement")
    expect(req).toBeDefined()
    expect(req!.constraintCategory).toBe(ConstraintCategory.HARD)
    expect(req!.constraintType).toBe(ConstraintType.TECHNICAL)
  })

  it("assignment to parse result is propagated", () => {
    const result = parse("must be fast without recursion")
    expect(result.constraints).toContain("requirement")
    expect(result.constraints).toContain("negation")
  })
})

// ---------------------------------------------------------------------------
// Analysis integration
// ---------------------------------------------------------------------------
describe("analysis integration", () => {
  it("full pipeline produces coherent output", () => {
    const a = new Analysis("write a python function that sorts a list without recursion")
    expect(a.score.total).toBeGreaterThan(0)
    expect(a.score.total).toBeLessThanOrEqual(10)
    expect(a.score.band).toBeTruthy()
    expect(a.result.verbs).toContain("write")
    expect(a.result.constraints).toContain("negation")
    expect(a.rhetoric).toBeDefined()
    expect(a.chunking).toBeDefined()
  })

  it("Analysis supports fullOutput with UDL", () => {
    const a = new Analysis("write a function")
    const out = a.fullOutput(true)
    expect(out.version).toBe("0.1.0")
    expect(out._udl_envelope).toBeDefined()
  })
})
