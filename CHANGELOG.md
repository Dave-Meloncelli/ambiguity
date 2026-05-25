# Changelog

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
  .cursorrules, GitHub issue templates
- Empirical validation: analyzed 84 real production system prompts
  (Anthropic, OpenAI, Google, xAI) — 0 errors, avg score 6.36/10
