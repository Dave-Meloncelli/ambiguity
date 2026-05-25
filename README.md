# ambiguity

**Deterministic prompt analysis — pre-flight linter for human-to-model translation.**

Score any prompt for ambiguity (0-10) before it reaches an LLM. Zero LLM calls.
Zero token cost. All analysis is regex + dict + arithmetic.

```bash
pip install ambiguity-analyzer
ambiguity analyze "Write a function that calculates fibonacci"
# Score: 5.8/10 (medium) — 1 verb, 0 constraints, container: code_generation
```

## Why

Ambiguous prompts produce inconsistent behavior across models and harnesses.
ambiguity gives you a deterministic pre-flight check — no API calls, no
hallucinated analysis, just hard numbers and actionable fixes.

| Score | Band | Meaning |
|-------|------|---------|
| 0-3   | low  | Well-structured, proceed |
| 3-6   | medium | Minor issues, advisory shown |
| 6-8   | high | Multiple entropy indicators, mandatory review |
| 8-10  | very high | Significant ambiguity, restructure before submitting |

## Install

```bash
# Python
pip install ambiguity-analyzer

# TypeScript (npm)
npm install -g ambiguity-analyzer

# From source
git clone <url>
cd ambiguity && pip install -e .
cd ts && npm install && npm run build
```

## Usage

```bash
# Analyze a prompt
ambiguity analyze "Your prompt here"

# Pipe from file or stdin
cat prompt.txt | ambiguity analyze --pipe

# JSON output for programmatic consumption
ambiguity analyze "Your prompt" --json

# Self-learning: dismiss recurring false positives
ambiguity dismiss "no_terminal_punctuation"

# Teach new vocabulary
ambiguity learn verb "deploy" --containers code_generation --specificity 0.8
ambiguity learn acronym "API" --expansion "Application Programming Interface"
```

## Features

- **Verb taxonomy** — 80+ verbs mapped to prediction-space containers with specificity scores
- **Constraint detection** — flags missing boundaries, unqualified references, vague pronouns
- **Acronym expansion** — known acronyms expanded, unknown ones flagged
- **Fuzzy matching** — Levenshtein distance-1 catches typos and inflected forms
- **Accessibility** — detects missing spaces, stutter words, repeated characters, missing punctuation
- **Self-learning profile** — adapts to your writing patterns after 10+ sessions
- **UDL envelope** — optional Federation bridge for Unified Data Layer consumers
- **Dual implementation** — Python (Federation) and TypeScript (npm) with identical logic

## Architecture

```
prompt → parser → verb extraction (VERB_TAXONOMY + fuzzy match)
                → keyword extraction (KEYWORD_MAP)
                → acronym expansion (KNOWN_ACRONYMS)
                → constraint detection
                → language detection
       → scoring (0-10, verb specificity + container overlap + entropy)
       → advisory (priority-ordered, single-line fix)
       → report (terminal tables or JSON)
       → UDL envelope (optional Federation bridge)
       → profile (self-learning, threshold calibration, flag suppression)
```

## Keywords

`prompt-engineering` `prompt-linting` `llm-guardrails` `deterministic-analysis`
`pre-flight` `entropy-scoring` `human-to-model-translation` `federation-surface`
`udl-envelope` `ambiguity`

## License

MIT — see [LICENSE](LICENSE)

## Project surfaces

| File | Tool/Platform |
|------|---------------|
| `opencode.json` | opencode (canonical entry) |
| `CLAUDE.md` | Claude Code |
| `.cursor/rules/` | Cursor IDE (scoped rules) |
| `.github/copilot-instructions.md` | GitHub Copilot |
| `.windsurf/rules/` | Windsurf (Codeium) |
| `CONVENTIONS.md` | Aider |
| `docs/AGENTS.md` | Agent guide with conventions |
| `docs/QUICKSTART.md` | Human + agent walkthrough |
| `MANIFEST.yaml` | Ecosystem manifest |
| `docs/CHAP_ANCHOR.md` | Federation surface anchor |
