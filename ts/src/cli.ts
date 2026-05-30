#!/usr/bin/env node

import { readFileSync } from "node:fs"
import { advisory, setSuppressed } from "./advisory.js"
import { Analysis } from "./analyzer.js"
import { getProfile } from "./profile.js"
import { compare, writeExperimentFiles, renderCompareReport } from "./compare.js"
import { audit, renderAuditReport } from "./audit.js"
import { translate, renderTranslateReport } from "./translate.js"
import { generateClarification, renderClarifyReport } from "./clarify.js"
import { writeEntry, readEntries, summary as memorySummary } from "./memory.js"
import { discover, renderImportReport } from "./import_discover.js"
import { flowTest, renderFlowReport } from "./flow.js"
import { review, renderReviewReport, renderReviewJson } from "./review.js"

function readStdin(): string {
  try {
    return readFileSync(0, "utf-8").trim()
  } catch {
    return ""
  }
}

function helpText(): string {
  return `
usage:
  ambiguity analyze <prompt> [--json] [--udl] [--quiet] [--pipe] [--gate <n>]
  ambiguity learn verb <word> [--containers ...] [--specificity n]
  ambiguity learn acronym <abbr> --expansion <text>
  ambiguity learn keyword <word> [--containers ...]
  ambiguity dismiss <flag_type>
  ambiguity config [--reset]
  ambiguity compare <prompt> [--json] [--pipe] [--no-llm] [--output-dir <dir>]
  ambiguity audit <prompt> [--json] [--pipe] [--dir <path>]
  ambiguity translate <prompt> [--json] [--pipe]
  ambiguity clarify <prompt> [--json] [--pipe]
  ambiguity log <prompt> [--pipe] [--action <a>] [--outcome <o>] [--note <n>] [--summary]
  ambiguity import [--consent] [--execute] [--json]
  ambiguity flow-test [--json]
  ambiguity review <prompt> --response <text> [--json]
    `
}

interface ParsedArgs {
  command: string
  [key: string]: unknown
}

function parseArgs(): ParsedArgs {
  const args = process.argv.slice(2)
  const cmd = args[0]

  if (!cmd || cmd === "--help" || cmd === "-h") {
    console.log(helpText())
    process.exit(cmd ? 0 : 1)
  }

  const result: ParsedArgs = { command: cmd }

  const has = (flag: string) => args.includes(flag)
  const idx = (flag: string) => args.indexOf(flag)
  const after = (flag: string) => {
    const i = idx(flag)
    return i >= 0 ? args[i + 1] : undefined
  }

  if (cmd === "analyze") {
    result.pipe = has("--pipe")
    result.json = has("--json")
    result.udl = has("--udl")
    result.quiet = has("--quiet")
    const gateIdx = idx("--gate")
    result.gate = gateIdx >= 0 ? Number.parseFloat(args[gateIdx + 1]) : 0
    if (result.pipe) {
      result.prompt = readStdin()
    } else {
      result.prompt = args[1] ?? ""
    }
  } else if (cmd === "learn") {
    result.type = args[1]
    result.value = args[2]
    const ci = idx("--containers")
    result.containers = ci >= 0 ? args.slice(ci + 1).filter((a) => !a.startsWith("--")) : []
    result.specificity = has("--specificity") ? Number.parseFloat(after("--specificity") ?? "0.5") : 0.5
    result.expansion = after("--expansion")
  } else if (cmd === "dismiss") {
    result.flag_type = args[1]
  } else if (cmd === "config") {
    result.reset = has("--reset")
  } else if (["compare", "audit", "translate", "clarify"].includes(cmd)) {
    result.json = has("--json")
    result.pipe = has("--pipe")
    if (result.pipe) {
      result.prompt = readStdin()
    } else {
      result.prompt = args[1] ?? ""
    }
    if (cmd === "compare") {
      result.no_llm = has("--no-llm")
      result.output_dir = after("--output-dir")
    }
    if (cmd === "audit") {
      result.dir = after("--dir") ?? "."
    }
  } else if (cmd === "log") {
    result.pipe = has("--pipe")
    if (result.pipe) {
      result.prompt = readStdin()
    } else {
      result.prompt = args[1] ?? ""
    }
    result.action = after("--action") ?? "none"
    result.outcome = after("--outcome") ?? "accepted"
    result.note = after("--note") ?? ""
    result.summary = has("--summary")
  } else if (cmd === "import") {
    result.consent = has("--consent")
    result.execute = has("--execute")
    result.json = has("--json")
  } else if (cmd === "flow-test") {
    result.json = has("--json")
  } else if (cmd === "review") {
    result.prompt = args[1] ?? ""
    result.response = after("--response") ?? ""
    result.json = has("--json")
  }

  return result
}

function getPrompt(args: ParsedArgs): string | null {
  const prompt = args.prompt as string | undefined
  if (!prompt) {
    console.error("error: no prompt provided (pass as argument or pipe via stdin)")
    return null
  }
  return prompt
}

function cmdAnalyze(args: ParsedArgs): number {
  const prompt = getPrompt(args)
  if (!prompt) return 1

  const profile = getProfile()
  const suppressed = profile.suppressedFlags()
  if (suppressed.size > 0) setSuppressed(suppressed)

  const analysis = new Analysis(prompt)
  const adv = advisory(analysis.result, analysis.score)
  profile.record(analysis.result, analysis.score, adv)

  const gate = args.gate as number
  if (gate > 0 && analysis.score.total > gate) {
    if (args.json) {
      console.log(JSON.stringify(analysis.fullOutput(args.udl as boolean), null, 2))
    } else {
      console.log(analysis.terminalReport())
    }
    console.error(`[ambiguity] GATE: score ${analysis.score.total.toFixed(1)} exceeds ${gate.toFixed(1)}`)
    return 1
  }

  if (args.quiet && analysis.score.total < profile.adjustedThreshold()) return 0

  if (args.json) {
    const output = analysis.fullOutput(args.udl as boolean) as Record<string, unknown> & {
      _profile?: Record<string, unknown>
    }
    output._profile = {
      baseline: profile.scoreBaseline,
      threshold: profile.adjustedThreshold(),
      suppressed: [...profile.suppressedFlags()],
    }
    console.log(JSON.stringify(output, null, 2))
  } else {
    console.log(analysis.terminalReport())
  }

  return 0
}

function cmdLearn(args: ParsedArgs): number {
  const profile = getProfile()
  const type = args.type as string
  const value = args.value as string

  if (type === "verb") {
    profile.learnVerb(value, args.containers as string[], args.specificity as number)
    console.log(`learned verb '${value}'`)
  } else if (type === "acronym") {
    const expansion = args.expansion as string | undefined
    if (!expansion) {
      console.error("error: --expansion required for acronyms")
      return 1
    }
    profile.learnAcronym(value, expansion)
    console.log(`learned acronym '${value}' -> '${expansion}'`)
  } else if (type === "keyword") {
    profile.learnKeyword(value, args.containers as string[])
    console.log(`learned keyword '${value}'`)
  }

  return 0
}

function cmdDismiss(args: ParsedArgs): number {
  getProfile().dismiss(args.flag_type as string)
  console.log(`dismissed '${args.flag_type}' (will suppress after 3 dismissals)`)
  return 0
}

function cmdConfig(args: ParsedArgs): number {
  const profile = getProfile()

  if (args.reset) {
    console.log("profile reset is not available via CLI — delete ~/.ambiguity/profile.json manually")
    return 0
  }

  const info = {
    entries: profile.entries.length,
    score_baseline: profile.scoreBaseline,
    threshold: profile.adjustedThreshold(),
    suppressed_flags: [...profile.suppressedFlags()],
    learned_verbs: Object.keys(profile.learnedVerbs).length,
    learned_acronyms: Object.fromEntries(Object.entries(profile.learnedAcronyms).slice(0, 10)),
    learned_keywords: Object.keys(profile.learnedKeywords).length,
  }

  console.log(JSON.stringify(info, null, 2))
  return 0
}

function cmdCompare(args: ParsedArgs): number {
  const prompt = getPrompt(args)
  if (!prompt) return 1

  const result = compare(prompt)

  if (args.output_dir) {
    writeExperimentFiles(result, args.output_dir as string)
    console.error(`Experiment files written to ${args.output_dir}`)
  }

  console.log(renderCompareReport(result))
  return 0
}

function cmdAudit(args: ParsedArgs): number {
  const prompt = getPrompt(args)
  if (!prompt) return 1

  const result = audit(prompt, (args.dir as string) ?? ".")
  console.log(renderAuditReport(result))
  return result.summary.missing > 0 || result.permissionIssues.length > 0 ? 1 : 0
}

function cmdTranslate(args: ParsedArgs): number {
  const prompt = getPrompt(args)
  if (!prompt) return 1

  const result = translate(prompt)
  console.log(renderTranslateReport(result))
  return 0
}

function cmdClarify(args: ParsedArgs): number {
  const prompt = getPrompt(args)
  if (!prompt) return 1

  const result = generateClarification(prompt)
  console.log(renderClarifyReport(result))
  return result.questions.length > 0 ? 1 : 0
}

function cmdLog(args: ParsedArgs): number {
  if (args.summary) {
    console.log(memorySummary())
    return 0
  }

  const prompt = getPrompt(args)
  if (!prompt) return 1

  const path = writeEntry(prompt, args.action as string, undefined, args.outcome as string, args.note as string)
  if (!path) {
    console.error("error: docs/memory.md not found")
    return 1
  }
  console.log(`logged to ${path}`)
  return 0
}

function cmdImport(args: ParsedArgs): number {
  const result = discover(args.consent as boolean, !args.execute)
  if (args.json) {
    console.log(JSON.stringify(result, null, 2))
  } else {
    console.log(renderImportReport(result))
  }
  return 0
}

function cmdFlowTest(args: ParsedArgs): number {
  const result = flowTest()
  if (args.json) {
    console.log(JSON.stringify(result, null, 2))
  } else {
    console.log(renderFlowReport(result))
  }
  return result.issues.length > 0 ? 1 : 0
}

function cmdReview(args: ParsedArgs): number {
  const prompt = (args.prompt as string) ?? ""
  const response = (args.response as string) ?? ""

  if (!prompt || !response) {
    console.error("error: usage: ambiguity review <prompt> --response <response>")
    return 1
  }

  const result = review(prompt, response)
  if (args.json) {
    console.log(JSON.stringify(renderReviewJson(result), null, 2))
  } else {
    console.log(renderReviewReport(result))
  }
  return result.issues.some((i) => i.severity === "error") ? 1 : 0
}

function main(): number {
  const args = parseArgs()
  const cmd = args.command

  switch (cmd) {
    case "analyze":
      return cmdAnalyze(args)
    case "learn":
      return cmdLearn(args)
    case "dismiss":
      return cmdDismiss(args)
    case "config":
      return cmdConfig(args)
    case "compare":
      return cmdCompare(args)
    case "audit":
      return cmdAudit(args)
    case "translate":
      return cmdTranslate(args)
    case "clarify":
      return cmdClarify(args)
    case "log":
      return cmdLog(args)
    case "import":
      return cmdImport(args)
    case "flow-test":
      return cmdFlowTest(args)
    case "review":
      return cmdReview(args)
    default:
      console.error(`unknown command: ${cmd}`)
      return 1
  }
}

process.exit(main())
