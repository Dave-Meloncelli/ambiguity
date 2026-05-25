# ambiguity — deterministic prompt analysis

Pre-flight linter that scores ambiguity (0-10), maps verbs to prediction-space
containers, expands acronyms, flags missing constraints, and outputs UDL
envelopes. Zero LLM calls. Zero token cost.

## Quick start

```bash
pip install -e .
pytest tests/
ambiguity analyze "your prompt here"
```

## Dual implementation

- **Python**: `src/ambiguity/` — pip-installable, Federation-facing
- **TypeScript**: `ts/` — canonical npm distribution (`ambiguity-analyzer`)

## Key files

| File | Purpose |
|------|---------|
| `AGENTS.md` | Full agent guide with structure, conventions, handoff |
| `src/ambiguity/containers.py` | Verb taxonomy + keyword map |
| `ts/src/containers.ts` | TypeScript verb taxonomy (mirrors Python) |
| `src/ambiguity/scoring.py` | Ambiguity score (0-10) formula |

## Important conventions

- Deterministic only — no LLM calls, all regex + dict + arithmetic
- No external runtime deps (Federation UDL bridge is try/import)
- Both Python and TS implementations must stay in sync

## Build / test commands

- Python: `pip install -e .` then `pytest tests/`
- TypeScript: `cd ts && npm run build && npm test`
- Lint: Python uses ruff (defined in pyproject.toml), TS uses biome
