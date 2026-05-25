# ambiguity — GitHub Copilot Instructions

## Project overview

Deterministic prompt analysis tool. Scores prompts for ambiguity (0-10) before
they reach an LLM. Zero LLM calls — all regex + dict + arithmetic.

## Dual implementation

- **Python**: `src/ambiguity/` — pip-installable
- **TypeScript**: `ts/src/` — canonical npm dist (`ambiguity-analyzer`)
- Both must stay in sync: same modules, same logic, same verb taxonomy

## Key files

- `src/ambiguity/containers.py` / `ts/src/containers.ts` — verb taxonomy + keyword map
- `src/ambiguity/parser.py` / `ts/src/parser.ts` — regex extraction
- `src/ambiguity/scoring.py` / `ts/src/scoring.ts` — ambiguity score formula
- `docs/AGENTS.md` — full agent guide with conventions

## Commands

```bash
# Python
pip install -e .
pytest tests/
ambiguity analyze "your prompt"

# TypeScript
cd ts && npm install && npm run quality
```

## Rules

1. Keep Python and TypeScript implementations identical
2. No LLM calls in analysis code
3. Run both test suites before submitting changes
