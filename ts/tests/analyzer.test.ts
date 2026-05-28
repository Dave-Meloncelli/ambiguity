import { describe, it, expect } from "vitest"
import { parse } from "../src/parser.js"
import { AmbiguityScore } from "../src/scoring.js"
import { Analysis } from "../src/analyzer.js"
import { containersForVerb, specificityBand, resolveAcronym } from "../src/containers.js"

describe("parser", () => {
  it("extracts verbs from a prompt", () => {
    const result = parse("write a function that sorts a list")
    expect(result.verbs).toContain("write")
    expect(result.verbs).toContain("sorts")
  })

  it("extracts keywords", () => {
    const result = parse("write a python function")
    expect(result.keywords).toContain("python")
  })

  it("detects acronyms", () => {
    const result = parse("check the UDL configuration")
    expect(result.acronyms.some(([a]) => a === "UDL")).toBe(true)
  })

  it("detects constraints", () => {
    const result = parse("implement without imports")
    expect(result.constraints.length).toBeGreaterThan(0)
  })

  it("detects vocabulary scope terms", () => {
    const result = parse("output the UDL envelope via the Federation surface bridge")
    expect(result.vocabScope.length).toBeGreaterThan(0)
    const terms = result.vocabScope.map((v) => v.term)
    expect(terms).toContain("envelope")
    expect(terms).toContain("surface")
    expect(terms).toContain("bridge")
  })
})

describe("scoring", () => {
  it("vague prompt scores high", () => {
    const analysis = new Analysis("do the thing make it work")
    expect(analysis.score.total).toBeGreaterThan(6.0)
  })

  it("precise prompt scores lower", () => {
    const analysis = new Analysis("implement merge sort on a linked list in python without recursion, handle empty list")
    expect(analysis.score.total).toBeLessThan(8.0)
  })

  it("jargon-heavy prompt gets vocabulary scope penalty", () => {
    const analysis = new Analysis("publish the UDL envelope to the Federation surface bridge")
    expect(analysis.result.vocabScope.length).toBeGreaterThan(0)
    expect(analysis.score.entropyIndicators.some((i) => i.includes("domain-specific"))).toBe(true)
  })
})

describe("containers", () => {
  it("maps verbs to containers and specificity", () => {
    const [containers, spec] = containersForVerb("sort")
    expect(containers.length).toBeGreaterThan(0)
    expect(spec).toBeGreaterThan(0)
  })

  it("returns specificity band", () => {
    const band = specificityBand(0.85)
    expect(band).toBe("precise")
  })

  it("resolves acronyms", () => {
    const expansion = resolveAcronym("UDL")
    expect(expansion).toBe("Unified Data Layer")
  })
})

describe("analysis", () => {
  it("produces a terminal report", () => {
    const analysis = new Analysis("write a function")
    const report = analysis.terminalReport()
    expect(report).toContain("ambiguity")
  })

  it("produces a JSON report", () => {
    const analysis = new Analysis("write a function")
    const jr = analysis.jsonReport()
    expect(jr.version).toBe("0.1.0")
  })

  it("produces a UDL envelope", () => {
    const analysis = new Analysis("write a function")
    expect(analysis.udlEnvelope).not.toBeNull()
    expect(analysis.udlEnvelope!.format).toBe("udl_v1")
  })
})
