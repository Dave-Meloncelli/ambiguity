You are working on ambiguity — a deterministic prompt analysis tool.

## Project structure
- Python implementation in `src/ambiguity/`
- TypeScript implementation in `ts/src/` (canonical npm distribution)
- Both must stay in sync: same modules, same logic, same verb taxonomy

## Critical rules
1. No LLM calls in analysis code — all regex + dict + arithmetic
2. Federation UDL bridge is optional try/import (C:\Federation)
3. Levenshtein fuzzy matching at edit distance 1 only
4. Edit both Python and TypeScript when adding verbs, keywords, or advisories

## Build/test
- Python: `pip install -e . && pytest tests/`
- TypeScript: `cd ts && npm run quality` (lint + test + typecheck)
- CLI: `ambiguity analyze "test" --json`

## Reference files
- `docs/AGENTS.md` — full guide with conventions and handoff
- `docs/QUICKSTART.md` — install and usage
- `src/ambiguity/containers.py` — verb taxonomy (Python)
- `ts/src/containers.ts` — verb taxonomy (TypeScript)
- `docs/memory.md` — session history and open decisions
