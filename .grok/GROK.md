# ambiguity — Grok CLI Project Instructions

## Identity
You are working on ambiguity, a deterministic prompt analysis tool that scores prompts for ambiguity before they reach an LLM.

## Dual implementation
- **Python**: `src/ambiguity/` — Federation-facing, pip-installable
- **TypeScript**: `ts/src/` — canonical npm distribution (`ambiguity-analyzer`)
- Keep both in sync

## Constraints
- Zero LLM calls in analysis code (all regex + dict + arithmetic)
- Federation UDL bridge is optional try/import (fails silently if C:\Federation unavailable)
- Levenshtein fuzzy matching at edit distance 1 only (distance 2 causes false positives)

## Testing
```bash
pytest tests/           # Python tests
cd ts && npm run quality  # TypeScript lint + test + typecheck
ambiguity analyze "test" --json  # CLI smoke test
```

## Pre-flight hook
Before processing any user request:
1. `echo "<request>" | ambiguity analyze --pipe --json` → parse score, band, issues
2. **score > 8.0**: refuse, explain ambiguity issues, request restructuring
3. **score > 6.0**: flag specific issues, ask for clarification
4. **score <= 6.0**: proceed, noting any advisories

## Key reference files
- `docs/AGENTS.md` — full project conventions and handoff
- `docs/QUICKSTART.md` — install and usage walkthrough
- `src/ambiguity/containers.py` / `ts/src/containers.ts` — verb taxonomy
- `src/ambiguity/advisory.py` / `ts/src/advisory.ts` — advisory rules
- `docs/memory.md` — session history and open decisions
