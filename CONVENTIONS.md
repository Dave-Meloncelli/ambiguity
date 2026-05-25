# ambiguity — Aider Conventions

## Project

Deterministic prompt analysis. Scores ambiguity (0-10) without any LLM calls.

## Dual implementation

Both sides must be edited in sync:

```
src/ambiguity/containers.py  ←→  ts/src/containers.ts
src/ambiguity/parser.py      ←→  ts/src/parser.ts
src/ambiguity/scoring.py     ←→  ts/src/scoring.py
src/ambiguity/advisory.py    ←→  ts/src/advisory.ts
src/ambiguity/bridges.py     ←→  ts/src/bridges.ts
```

## Testing

```bash
pytest tests/
cd ts && npm run quality
```

## Federation bridge

`src/ambiguity/bridges.py` optionally imports UDL envelope from C:\Federation.
Must fail silently if Federation is unavailable.

## Taxonomy conventions

- Verbs added to `containers.py`/`containers.ts` with containers and specificity
- Keywords added to `KEYWORD_MAP` with container mappings
- Acronyms added to `KNOWN_ACRONYMS` with expansions
- Advisory rules added to `advisory.py`/`advisory.ts` with priority ordering
