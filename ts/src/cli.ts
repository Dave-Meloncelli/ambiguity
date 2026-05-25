#!/usr/bin/env node

import { readFileSync } from "node:fs"
import { advisory, setSuppressed } from "./advisory.js"
import { Analysis } from "./analyzer.js"
import { getProfile } from "./profile.js"

function parseArgs(): Record<string, unknown> {
  const args = process.argv.slice(2)
  const cmd = args[0]

  if (!cmd || cmd === "--help") {
    console.log(`
usage:
  ambiguity analyze <prompt> [--json] [--udl] [--quiet]
  ambiguity analyze --pipe [--json] [--udl]
  ambiguity learn verb <word> [--containers ...] [--specificity n]
  ambiguity learn acronym <abbr> --expansion <text>
  ambiguity learn keyword <word> [--containers ...]
  ambiguity dismiss <flag_type>
  ambiguity config [--reset]
    `)
    process.exit(cmd ? 0 : 1)
  }

  const result: Record<string, unknown> = { command: cmd }

  if (cmd === "analyze") {
    const pipeIdx = args.indexOf("--pipe")
    const jsonIdx = args.indexOf("--json")
    const udlIdx = args.indexOf("--udl")
    const quietIdx = args.indexOf("--quiet")

    result.pipe = pipeIdx !== -1
    result.json = jsonIdx !== -1
    result.udl = udlIdx !== -1
    result.quiet = quietIdx !== -1

    if (result.pipe) {
      result.prompt = readFileSync(0, "utf-8").trim()
    } else {
      result.prompt = args[1] ?? ""
    }
  } else if (cmd === "learn") {
    result.type = args[1]
    result.value = args[2]
    const containersIdx = args.indexOf("--containers")
    result.containers =
      containersIdx !== -1 ? args.slice(containersIdx + 1).filter((a) => !a.startsWith("--")) : []
    const specIdx = args.indexOf("--specificity")
    result.specificity = specIdx !== -1 ? Number.parseFloat(args[specIdx + 1]) : 0.5
    const expIdx = args.indexOf("--expansion")
    result.expansion = expIdx !== -1 ? args[expIdx + 1] : undefined
  } else if (cmd === "dismiss") {
    result.flag_type = args[1]
  } else if (cmd === "config") {
    result.reset = args.includes("--reset")
  }

  return result
}

function cmdAnalyze(args: Record<string, unknown>): number {
  const prompt = args.prompt as string
  if (!prompt) {
    console.error("error: no prompt provided")
    return 1
  }

  const profile = getProfile()
  const suppressed = profile.suppressedFlags()
  if (suppressed.size > 0) setSuppressed(suppressed)

  const analysis = new Analysis(prompt)
  const adv = advisory(analysis.result, analysis.score)
  profile.record(analysis.result, analysis.score, adv)

  if (args.quiet && analysis.score.total < profile.adjustedThreshold()) {
    return 0
  }

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

function cmdLearn(args: Record<string, unknown>): number {
  const profile = getProfile()
  const type = args.type as string
  const value = args.value as string

  if (type === "verb") {
    profile.learnVerb(value, args.containers as string[], args.specificity as number)
    console.log(`learned verb '${value}'`)
  } else if (type === "acronym") {
    const expansion = args.expansion as string
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

function cmdDismiss(args: Record<string, unknown>): number {
  getProfile().dismiss(args.flag_type as string)
  console.log(`dismissed '${args.flag_type}' (will suppress after 3 dismissals)`)
  return 0
}

function cmdConfig(args: Record<string, unknown>): number {
  const profile = getProfile()

  if (args.reset) {
    console.log(
      "profile reset is not available via CLI — delete ~/.ambiguity/profile.json manually",
    )
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

function main(): number {
  const args = parseArgs()
  const cmd = args.command as string

  switch (cmd) {
    case "analyze":
      return cmdAnalyze(args)
    case "learn":
      return cmdLearn(args)
    case "dismiss":
      return cmdDismiss(args)
    case "config":
      return cmdConfig(args)
    default:
      console.error(`unknown command: ${cmd}`)
      return 1
  }
}

process.exit(main())
