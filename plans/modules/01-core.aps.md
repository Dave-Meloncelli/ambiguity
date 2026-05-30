# Module: Core Analysis Engine

| ID | Owner | Priority | Status |
|----|-------|----------|--------|
| CORE | Engineering Guild | high | Complete |

## Purpose

Analyze human-written prompts for translation ambiguity before they reach an LLM. Score 0-10, map verbs to prediction-space containers, expand acronyms, flag missing constraints, detect rhetoric patterns.

## Boundaries

- **In scope**: verb extraction, keyword matching, acronym expansion, constraint detection, vocabulary scope, rhetoric analysis, chunking, advisory generation, ambiguity scoring
- **Out of scope**: LLM calls, semantic understanding, response generation, prompt rewriting
- **Dual implementation**: Python (src/ambiguity/) and TypeScript (ts/src/) must stay in sync

## Interfaces

| Interface | Type | Description |
|-----------|------|-------------|
| CLI | operator | `ambiguity analyze`, `ambiguity learn`, `ambiguity dismiss`, `ambiguity config`, `ambiguity review`, `ambiguity compare`, `ambiguity translate`, `ambiguity clarify`, `ambiguity audit`, `ambiguity log`, `ambiguity import`, `ambiguity flow-test` |
| SDK | integration | `Analysis` class, `parse()`, `AmbiguityScore`, `Profile`, hooks (AnthropicHook, OpenaiHook) |
| pip package | delivery | `pip install ambiguity-analyzer` |
| npm package | delivery | `npm install ambiguity-analyzer` |
| UDL bridge | integration | Optional `bridges.py` → C:\Federation UnifiedDataLayerEnvelope |

## Work Items

### CORE-001: Verb Taxonomy

- **Intent:** Map human verbs to prediction-space containers with specificity scores
- **Expected Outcome:** 80+ verbs in Python + 80+ in TS, each with container mapping and specificity
- **Validation:** `pytest tests/` (67 pass) && `cd ts && npx vitest run` (74 pass)
- **Status:** Complete: 2026-05-30

### CORE-002: Ambiguity Scoring

- **Intent:** Score prompts 0-10 based on verb specificity, container overlap, constraint count, instruction density, entropy indicators
- **Expected Outcome:** Repeatable, deterministic scoring — same input always produces same score
- **Validation:** Score tests pass, calibration corpus (271 files) zero score drift
- **Status:** Complete: 2026-05-30

### CORE-003: Constraint Taxonomy

- **Intent:** Detect typed constraints (7 types × 3 categories) from prompt text
- **Expected Outcome:** CDL constraints extracted and classified as hard/soft/false
- **Validation:** Constraints module tests pass (Python + TS)
- **Status:** Complete: 2026-05-30

### CORE-004: Response Review

- **Intent:** Post-flight analysis of LLM responses — detect hedging, hallucination signals, constraint compliance
- **Expected Outcome:** Response scored 0-10 with typed issues
- **Validation:** `ambiguity review --response "..."` produces scored result
- **Status:** Complete: 2026-05-30

### CORE-005: Dual-Sync Enforcement

- **Intent:** Keep Python and TS implementations identical in logic, taxonomy, and output
- **Expected Outcome:** Same data tables, same parsing, same scoring algorithms in both languages
- **Validation:** Parity verified (verbs: 110/110, acronyms: 20/20, hedges: 38/38, emphatics: 22/22, constraints: same types)
- **Status:** Complete: 2026-05-30
