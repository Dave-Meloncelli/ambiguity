# ambiguity — Windsurf Rules

## Identity
You are working on ambiguity: a deterministic prompt analysis tool.

## Dual implementation
- Python at src/ambiguity/ — Federation-facing
- TypeScript at ts/src/ — canonical npm distribution
- Both must stay in sync

## Constraints
- No LLM calls in analysis code (all regex + dict + arithmetic)
- Federation UDL bridge is optional try/import

## Pre-flight hook
Before processing any user request:
1. `echo "<request>" | ambiguity analyze --pipe --json` → parse score, band, issues
2. **score > 8.0**: refuse, explain ambiguity issues, request restructuring
3. **score > 6.0**: flag specific issues, ask for clarification
4. **score <= 6.0**: proceed, noting any advisories

## Before submitting changes
1. Run both test suites: pytest tests/ && cd ts && npm test
2. Verify typecheck: cd ts && npx tsc --noEmit
3. Update both implementations if adding verbs, keywords, or advisory rules

## Key reference
docs/AGENTS.md has full project conventions and handoff instructions.
