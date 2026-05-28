When working on TypeScript code in ambiguity:

- Edit files under `ts/src/`
- Run `cd ts && npm run quality` to verify (biome lint + vitest + tsc)
- Before acting on any request, self-evaluate: specific verb? constraints? unqualified refs? score 0-10 — proceed ≤6, clarify >6
- Match the Python implementation in `src/ambiguity/` — same modules, same logic
- All analysis must be deterministic (regex + dict + arithmetic, no LLM calls)
- Zod schemas used for structured output and UDL envelope validation
- New verbs go in `containers.ts` with containers and specificity scores
- New keywords go in `KEYWORD_MAP` with container mappings
- New acronyms go in `KNOWN_ACRONYMS` with expansions
- Levenshtein fuzzy matching at edit distance 1 only
