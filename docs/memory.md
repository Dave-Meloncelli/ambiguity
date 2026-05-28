# ambiguity — Project Memory

> Auto-maintained by `ambiguity log`. Each entry records a prompt interaction
> (analyze → translate/clarify → outcome) so agents learn user patterns across sessions.

## Convention

Every entry follows this structure:

```yaml
- date: 2026-05-25T17:30:00Z
  prompt: "write a function"
  hash: a1b2c3d4
  score: 5.8
  band: medium
  action: translate
  changes:
    - type: vague_verb
      original: "write"
      replacement: "implement"
  outcome: accepted
```

Agents: read this file at session start. Append after each interaction.

## Entries

- date: 2026-05-25T09:35:22Z
  prompt: "Hey so do the UDL thing and make it work"
  hash: 31424db7
  score: 7.6
  band: high
  action: translate
    changes:
      - type: acronym
        original: "UDL"
        replacement: "UDL (Unified Data Layer)"
      - type: unqualified_ref
        original: "it"
        replacement: "<<it>>"
      - type: constraint_reminder
        original: ""
        replacement: "  [NOTE: Add explicit constraints — languages, dependencies,"
  outcome: accepted
    note: "demo session"


