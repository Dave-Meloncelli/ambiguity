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
| `docs/AGENTS.md` | Full agent guide with structure, conventions, handoff |
| `src/ambiguity/containers.py` | Verb taxonomy + keyword map + vocabulary scope |
| `ts/src/containers.ts` | TypeScript verb taxonomy (mirrors Python) |
| `src/ambiguity/scoring.py` | Ambiguity score (0-10) formula + entropy indicators |
| `src/ambiguity/parser.py` | Regex extraction (verbs, keywords, acronyms, vocab scope) |
| `src/ambiguity/constraints.py` | CDL typed constraint taxonomy (7 types × 3 categories) |
| `src/ambiguity/embeddings.py` | Optional semantic gap detection (requires `AMBIGUITY_EMBEDDINGS=1`) |
| `src/ambiguity/hooks.py` | LLM client wrappers (auto-analyze prompts before send) |

## Important conventions

- Deterministic only — no LLM calls, all regex + dict + arithmetic
- No external runtime deps (Federation UDL bridge is try/import)
- Both Python and TS implementations must stay in sync
- **Embedding analysis is opt-in**: set `AMBIGUITY_EMBEDDINGS=1` to enable sentence-transformers semantic gap detection
- **Constraint taxonomy is always active**: `analysis.constraint_analysis` returns typed CDL `Constraint` objects

## Pre-flight hook

Before processing any user request, run it through the ambiguity engine:

1. `echo "<request>" | ambiguity analyze --pipe --json` → parse score, band, issues
2. **score > 8.0**: refuse, explain ambiguity issues, request restructuring
3. **score > 6.0**: flag specific issues (vague verbs, missing constraints, etc.), ask for clarification
4. **score <= 6.0**: proceed normally, noting any low-severity advisories

## Build / test commands

- Python: `pip install -e .` then `pytest tests/`
- TypeScript: `cd ts && npm run build && npm test`
- Lint: Python uses ruff (defined in pyproject.toml), TS uses biome
