# Changelog

## 0.3.0 (2026-05-25)

- VOCABULARY_SCOPE dimension: detects domain-specific jargon (ecosystem/technical/metaphor),
  flags undefined terms in entropy indicators, adds score penalty (capped at 1.5)
- Advisory priority 6: vocab_scope ("define domain terms before use")
- Python port: containers.py, parser.py, scoring.py, advisory.py, report.py + 2 tests
- TypeScript port: containers.ts, parser.ts, scoring.ts, advisory.ts, report.ts + 2 tests
- Both sides have 0.3 parity: 11 Python tests, 14 TS tests, biome lint clean

## 0.2.0 (2026-05-25)

- Project surfaces expanded from 7 to 11:
  - New: `.gemini/GEMINI.md` — Google Gemini CLI
  - New: `.grok/GROK.md` — xAI Grok CLI
  - New: `.clinerules/rules.md` — Cline / Roo (directory format)
  - New: `.cursor/rules/python.mdc`, `typescript.mdc`, `project.mdc` — scoped Cursor
  - New: `.github/instructions/python.instructions.md`, `typescript.instructions.md` — scoped Copilot
- Root restructured: 30→22 visible items
  - Deleted `.cursorrules` (legacy, replaced by `.cursor/rules/`)
  - Migrated `.windsurfrules` → `.windsurf/rules/rules.md`
  - Migrated `.clinerules` (file) → `.clinerules/rules.md`
  - Moved to `docs/`: AGENTS.md, QUICKSTART.md, CHANGELOG.md, CHAP_ANCHOR.md, memory.md
- All 12 surface/cross-reference files updated with corrected root paths
- Web research confirmed modern agent surface conventions across 11 platforms
- Added standard docs: CODE_OF_CONDUCT.md, SUPPORT.md, AUTHORS.md
- Added `.npmignore` for TS package publishing

## 0.1.0 (2026-05-25)

- Initial release
- `ambiguity analyze` — deterministic prompt parsing, scoring (0-10), verb/container mapping
- Verb taxonomy: 80+ verbs with specificity scores and container mappings
- Levenshtein fuzzy matching (edit distance 1), British spelling support
- Acronym expansion, constraint detection, unqualified reference detection
- Self-learning profile (history, dismissals, threshold calibration)
- Accessibility: missing space detection, stutter words, repeated characters
- Advisory system with priority-ordered single-line fixes
- Terminal report + JSON output + UDL envelope (optional Federation bridge)
- Dual implementation: Python (`src/ambiguity/`) + TypeScript (`ts/src/`)
- Project infrastructure: opencode.json, CLAUDE.md, AGENTS.md, QUICKSTART.md,
  MANIFEST.yaml, CHAP_ANCHOR.md, .editorconfig, .gitignore, LICENSE (MIT),
  GitHub issue templates
- Empirical validation: analyzed 84 real production system prompts
  (Anthropic, OpenAI, Google, xAI) — 0 errors, avg score 6.36/10
