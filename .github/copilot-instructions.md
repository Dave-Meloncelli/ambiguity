# ambiguity — GitHub Copilot Instructions

## Project overview

Deterministic prompt analysis tool. Scores prompts for ambiguity (0-10) before
they reach an LLM. Zero LLM calls — all regex + dict + arithmetic.

## Dual implementation

- **Python**: `src/ambiguity/` — pip-installable
- **TypeScript**: `ts/src/` — canonical npm dist (`ambiguity-analyzer`)
- Both must stay in sync: same modules, same logic, same verb taxonomy

## Key files

- `src/ambiguity/containers.py` / `ts/src/containers.ts` — verb taxonomy + keyword map
- `src/ambiguity/parser.py` / `ts/src/parser.ts` — regex extraction
- `src/ambiguity/scoring.py` / `ts/src/scoring.ts` — ambiguity score formula
- `docs/AGENTS.md` — full agent guide with conventions

## Commands

```bash
# Python
pip install -e .
pytest tests/
ambiguity analyze "your prompt"

# TypeScript
cd ts && npm install && npm run quality
```

## Pre-flight self-assessment
When you receive a coding request, self-evaluate against this ambiguity rubric before responding:
- **Action verb**: specific (implement/convert/verify) or vague (do/make/handle)?
- **Constraints present**: language, framework, boundaries, exclusions?
- **Unqualified refs**: "it", "the thing", "as we discussed" without anchor?
- **Acronyms**: expanded on first use?
- **Instruction count**: 3+ instructions in one prompt = overloaded
- **Domain jargon**: technical terms without definition?
Score 0-10: 0-3 proceed, 3-6 flag issues, 6-8 ask clarification, 8-10 request restructuring.

## Rules
1. Keep Python and TypeScript implementations identical
2. No LLM calls in analysis code
3. Run both test suites before submitting changes
