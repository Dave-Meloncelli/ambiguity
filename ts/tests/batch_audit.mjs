import { execSync } from "node:child_process"

const testPrompts = [
  // Vague / underspecified
  { prompt: "do the thing",          expected: "high" },
  { prompt: "handle the data",       expected: "high" },
  { prompt: "make it work",          expected: "high" },
  { prompt: "deal with the problem", expected: "high" },
  { prompt: "fix the code",          expected: "medium" },

  // Precise / well-specified
  { prompt: "implement merge sort on a linked list in python without recursion, handle empty list", expected: "low-medium" },
  { prompt: "write a google test for the sort function validating ascending order with 5 fixtures", expected: "medium" },
  { prompt: "explain the difference between TCP and UDP with three examples each", expected: "low-medium" },

  // Acronyms
  { prompt: "check the UDL configuration for consistency", expected: "medium" },

  // Multi-instruction
  { prompt: "write a function, handle edge cases, no imports, add comments, make it efficient", expected: "high" },

  // Constrained
  { prompt: "implement sort using only the standard library, must handle empty list and None values, return a new list", expected: "low" },

  // Mixed quality
  { prompt: "optimize the query",    expected: "medium" },
  { prompt: "refactor the code",     expected: "medium" },
  { prompt: "debug the test failure on CI", expected: "medium" },

  // Edge cases
  { prompt: "a b c d e f",           expected: "error" },  // no verbs
  { prompt: "print('hello world')",  expected: "medium" },  // code-only

  // Real-world vibe coder prompts
  { prompt: "make a cool landing page with react",      expected: "high" },
  { prompt: "build a CRUD API with node and express with auth middleware and validation", expected: "medium" },
]

let allPassed = true

for (const tc of testPrompts) {
  const escaped = tc.prompt.replace(/"/g, '\\"')
  let output
  try {
    output = execSync(`node dist/cli.js analyze "${escaped}" --json 2>&1`, { encoding: "utf-8", timeout: 10000 })
  } catch (e) {
    if (tc.expected === "error") {
      console.log(`|  ERROR  | expected  | "${tc.prompt.slice(0, 40)}" |`)
    } else {
      console.log(`[ERROR] "${tc.prompt.slice(0, 50)}" — ${e.message.slice(0, 60)}`)
      allPassed = false
    }
    continue
  }

  let data
  try {
    data = JSON.parse(output)
  } catch {
    console.log(`[PARSE ERROR] "${tc.prompt.slice(0, 50)}" — raw: ${output.slice(0, 100)}`)
    allPassed = false
    continue
  }

  const score = data.ambiguity_score
  const verbs = data.analysis.verbs.map((v) => v.word).join(", ")
  const keywords = data.analysis.keywords.map((k) => k.word).join(", ")
  const advisory = data.advisory || "—"
  const constraints = data.analysis.constraints.join(", ") || "(none)"
  const acronyms = data.analysis.acronyms.map((a) => `${a.abbreviation}->${a.expansion}`).join(", ") || "(none)"

  console.log(
    `| ${score.total.toFixed(1).padStart(5)} | ${score.band.padEnd(9)} | ${verbs.padEnd(30)}` +
    ` | ${keywords.padEnd(20)} | ${constraints.padEnd(18)} | ${acronyms.padEnd(20)} | ${advisory.slice(0, 40).padEnd(40)} |`
  )

  // Basic sanity checks
  if (tc.prompt && tc.expected !== "error") {
    if (score.total < 0 || score.total > 10) {
      console.log(`  !! Score out of range: ${score.total}`)
      allPassed = false
    }
    if (advisory !== "—" && advisory.length > 80) {
      console.log(`  !! Advisory too long: ${advisory.length} chars`)
      allPassed = false
    }
  }
}

console.log(`\n${allPassed ? "ALL SANITY CHECKS PASSED" : "SOME SANITY CHECKS FAILED"}`)
