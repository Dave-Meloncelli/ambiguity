# ambiguity — Quickstart

Walkthrough for humans **and** AI agents. Structured for easy machine parsing.

## What is this?

A deterministic prompt analysis tool. It takes a human-written prompt and lints
it for translation ambiguity before it reaches an LLM.

- **Input:** raw prompt text
- **Output:** ambiguity score (0-10), advisory, verb/container mapping, vocabulary scope analysis, UDL envelope
- **Cost:** zero (regex + dict + arithmetic, no LLM calls)

## Install

### Python (pip)

```bash
pip install ambiguity-analyzer
```

Or from source:

```bash
git clone <repo>
cd ambiguity
pip install -e .
```

### TypeScript (npm)

```bash
npm install -g ambiguity-analyzer
```

Or from source:

```bash
cd ts
npm install
npm run build
```

## Usage

```bash
# Analyze a prompt
ambiguity analyze "Write a function that calculates fibonacci"

# Pipe from file
cat prompt.txt | ambiguity analyze --pipe

# JSON output
ambiguity analyze "Your prompt here" --json

# Suppress output when score is below learned threshold
ambiguity analyze "Low risk prompt" --quiet
```

## Learning commands

```bash
# Teach a new verb
ambiguity learn verb "deploy" --containers code_generation --specificity 0.8

# Expand an acronym
ambiguity learn acronym "API" --expansion "Application Programming Interface"

# Dismiss a recurring false positive
ambiguity dismiss "no_terminal_punctuation"

# View current config
ambiguity config
```

## Architecture

```
prompt → parser → verb/keyword/acronym extraction → scoring (0-10)
       → advisory (priority-ordered fix) → report (terminal/JSON)
       → UDL envelope (optional Federation bridge)
       → profile (self-learning, flag suppression, calibration)
```

## Keywords for search

`prompt-engineering` `prompt-linting` `llm-guardrails` `deterministic-analysis`
`human-to-model-translation` `pre-flight` `entropy-scoring` `federation-surface`

## License

MIT — see LICENSE file.
