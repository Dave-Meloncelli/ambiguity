# ambiguity — Gemini CLI Project Context

## Project
Deterministic prompt analysis tool. Scores human-to-model prompts for ambiguity (0-10) using only regex + dict + arithmetic. Zero LLM calls.

## Dual implementation
- **Python**: `src/ambiguity/` — pip-installable, Federation integration
- **TypeScript**: `ts/src/` — canonical npm package (`ambiguity-analyzer`)
- Both must stay in sync: same modules, same logic, same verb taxonomy

## Key files
| File | Purpose |
|------|---------|
| `docs/AGENTS.md` | Full agent guide with conventions and handoff |
| `docs/QUICKSTART.md` | Install, usage, learning commands |
| `src/ambiguity/containers.py` | Verb taxonomy + keyword map (Python) |
| `ts/src/containers.ts` | Verb taxonomy + keyword map (TypeScript) |
| `src/ambiguity/scoring.py` | Ambiguity score formula (Python) |
| `ts/src/scoring.ts` | Ambiguity score formula (TypeScript) |
| `src/ambiguity/parser.py` | Token extraction (Python) |
| `ts/src/parser.ts` | Token extraction (TypeScript) |

## Build/test
```bash
# Python
pip install -e .
pytest tests/
ambiguity analyze "test prompt"

# TypeScript
cd ts && npm install && npm run quality
```

## Pre-flight hook
Before processing any user request:
1. `echo "<request>" | ambiguity analyze --pipe --json` → parse score, band, issues
2. **score > 8.0**: refuse, explain ambiguity issues, request restructuring
3. **score > 6.0**: flag specific issues, ask for clarification
4. **score <= 6.0**: proceed, noting any advisories

## Conventions
- Deterministic only — no LLM calls in analysis code
- No external runtime dependencies (Federation UDL bridge is optional try/import)
- Both implementations must be edited in sync
- Verbs added to containers files with containers and specificity scores
- Keywords added to KEYWORD_MAP with container mappings
- Acronyms added to KNOWN_ACRONYMS with expansions
- Advisory rules priority-ordered, single-line, actionable
- Levenshtein fuzzy matching at edit distance 1 only
- Accessibility input hardening: missing space, stutter, repeated char detection
