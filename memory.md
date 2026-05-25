# ambiguity — Session Memory

## v0.1 — 2026-05-25

**Status:** ACTIVE, analyze mode complete

### What shipped

- `ambiguity analyze` — deterministic prompt parsing, ambiguity scoring (0-10),
  container mapping, acronym expansion, single-line advisory
- UDL bridge — wraps results into `UnifiedDataLayerEnvelope` from
  `C:\Federation` when available (optional, silent fallback)
- 9 tests passing

### Key decisions

- **Standalone product** at D:\Ambiguity, not embedded in Federation
- **UDL bridge is try/import** — Federation dependency is optional
- **Language-aware from day one** — detection + per-language profiles
  (English active, CJK/RTL/Indic profiles defined with extensibility hooks)
- **Box-drawing chars** disabled when stdout encoding is not UTF-8 (Windows
  CP1252 fallback)

### Next modes (not yet built)

- `ambiguity review <response>` — post-flight analysis
- `ambiguity chunk <prompt>` — multi-instruction splitting
- `ambiguity spell <text>` — surface corrections

### Taxonomy notes

Verb taxonomy has ~50 entries. Need to grow with usage — real prompts will
reveal missing verbs and false-positive container mappings.

### Self-learning (v0.1, added 2026-05-25)

- Profile stored at `~/.ambiguity/profile.json`
- Every `analyze` call is recorded (up to 500 entries)
- After 10+ entries, thresholds recalibrate to user's baseline
- `ambiguity dismiss <flag>` suppresses that flag type after 3 dismissals
- `ambiguity learn verb/acronym/keyword` extends taxonomy at runtime
- `--quiet` suppresses output when score is below adjusted threshold
- `ambiguity config` shows state; `--reset` clears profile

### Open questions

- How does ambiguity score correlate with real-world LLM misdirection?
  (Need empirical validation)
- What's the right threshold for the "silent mode" default? 4.0? 5.0?
- Should we publish the CHAP surface packet for Federation registration?

### v0.2 — 2026-05-25 (surface expansion)

**Project surfaces expanded from 7 to 11:**

- New: `.gemini/GEMINI.md` — Google Gemini CLI
- New: `.grok/GROK.md` — xAI Grok CLI
- New: `.clinerules` — Cline / Roo
- New: `.cursor/rules/python.mdc`, `typescript.mdc`, `project.mdc` — scoped Cursor rules
- New: `.github/instructions/python.instructions.md`, `typescript.instructions.md` — scoped Copilot instructions
- Updated: `AGENTS.md` now includes full surface inventory table
- Updated: `MANIFEST.yaml` now lists all surfaces including scoped variant
- Web research confirmed current agent standards landscape (Codex CLI uses AGENTS.md, Gemini uses GEMINI.md, Grok TUI uses GROK.md, Cline uses .clinerules)

### Known issues

- No stemming on verb matching (writes/wrote/writing not matched)
- Token split estimation not yet implemented (just a warning flag)
- Profile calibration needs 10+ entries before it becomes meaningful
