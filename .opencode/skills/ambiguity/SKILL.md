# ambiguity — Preloaded Analysis Engine Skill

Load this skill when you need deterministic prompt analysis in any session.
The engine is deterministic (zero LLM calls) and hooks into LLM workflows.

## Pre-flight hook (agent surface pattern)
When this skill is loaded, the ambiguity engine operates as a systematic pre-flight
hook for every user request:
1. `echo "<request>" | ambiguity analyze --pipe --json` → parse score, band, issues
2. **score > 8.0**: refuse, explain ambiguity issues, request restructuring
3. **score > 6.0**: flag specific issues, ask for clarification before proceeding
4. **score <= 6.0**: proceed normally, noting any low-severity advisories

## Usage

```python
from ambiguity.analyzer import Analysis
from ambiguity.hooks import AnthropicHook, OpenaiHook

# Direct analysis
analysis = Analysis("write a function that sorts a list")
print(analysis.score.total, analysis.score.band, analysis.advisory)

# Hooked LLM client — auto-analyzes before every API call
client = AnthropicHook(api_key="...")
response = client.messages.create(model="claude-3-5-sonnet", ...)
# ^ analysis logged to ~/.ambiguity/hooks.log before send

# CLI pipe mode for any workflow
# $ echo "your prompt" | ambiguity analyze --pipe --json
```

## Hook modes

| Hook | Trigger | Behavior |
|------|---------|----------|
| `AnthropicHook` | `client.messages.create()` | Analyzes prompt + logs score before API call |
| `OpenaiHook` | `client.chat.completions.create()` | Same for OpenAI |
| Git pre-commit | `git commit` | Fails if changed `.md` files score > 6.0 |
| CI gate | GitHub Action | Fails PR if prompt files exceed threshold |
| Watch mode | `--watch <dir>` | Monitors directory, analyzes new `.md` files |

## Threshold enforcement

```python
hook = AnthropicHook(api_key, gate=6.0, on_exceed="warn")
# on_exceed: "warn" | "block" | "log"
```

## Profile integration

Each hook call records to the self-learning profile. After 10+ calls,
thresholds calibrate to your baseline. Use `ambiguity dismiss` to suppress
recurring false-positive flags.

## References

- `docs/AGENTS.md` — full engine conventions and handoff
- `docs/QUICKSTART.md` — install and basic usage
- `src/ambiguity/hooks.py` — hook implementation source
