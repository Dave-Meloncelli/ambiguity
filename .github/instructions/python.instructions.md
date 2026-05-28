When working on Python code in ambiguity:

- Edit files under `src/ambiguity/`
- Run `pytest tests/` to verify Python changes
- Before acting on any request, self-evaluate: specific verb? constraints? unqualified refs? acronyms expanded? score 0-10 — proceed ≤6, clarify >6
- Match the TypeScript implementation in `ts/src/` — same modules, same logic
- All analysis must be deterministic (regex + dict + arithmetic, no LLM calls)
- Federation UDL bridge in `bridges.py` is optional try/import
- New verbs go in `containers.py` with containers and specificity scores
- New keywords go in `KEYWORD_MAP` with container mappings
- New acronyms go in `KNOWN_ACRONYMS` with expansions
- Levenshtein fuzzy matching at edit distance 1 only
