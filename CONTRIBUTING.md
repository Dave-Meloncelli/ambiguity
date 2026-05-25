# Contributing

## Dual implementation

Both Python (`src/ambiguity/`) and TypeScript (`ts/src/`) must stay in sync.
If you add a verb to one taxonomy, add it to the other. Same logic, same
modules, same verb taxonomy.

## Deterministic only

No module may call an LLM. All analysis is regex + dict + arithmetic. If you
need external data, add it as a lookup table or configuration file.

## Development

```bash
# Python
pip install -e .
pytest tests/

# TypeScript
cd ts
npm install
npm run quality   # typecheck + lint + test
```

## Before submitting

1. Run all tests (Python + TypeScript)
2. Keep both implementations in sync
3. Add tests for new patterns
4. Verify CLI works: `ambiguity analyze "test" --json`
5. If modifying UDL bridge, test with and without C:\Federation available

## Project structure

- `src/ambiguity/containers.py` + `ts/src/containers.ts` — verb taxonomy, keyword map, acronyms
- `src/ambiguity/parser.py` + `ts/src/parser.ts` — regex extraction
- `src/ambiguity/scoring.py` + `ts/src/scoring.ts` — ambiguity score formula
- `src/ambiguity/advisory.py` + `ts/src/advisory.ts` — priority-ordered advisories
- `src/ambiguity/bridges.py` + `ts/src/bridges.ts` — UDL envelope (Federation bridge)
- `docs/AGENTS.md` — full project conventions and handoff instructions
