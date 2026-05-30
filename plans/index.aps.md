# ambiguity — Project Plan

| Field | Value |
|-------|-------|
| Status | Complete |
| Created | 2026-05-30 |
| Pattern Family | named tool |
| Owner Surface | Process Guild |

## Project Pattern Declaration

```yaml
project_pattern:
  pattern_family: named tool
  delivery_surface: CLI + SDK (operator), pip + npm (delivery), Analysis class (integration)
  host_platform: Python 3.12+ / TypeScript 5.x / Windows (primary), Linux + macOS (compatible)
  contract_layer: deterministic-only (no LLM calls), dual-sync (Python + TS), UDL bridge (optional)
  proof_condition: 67+ Python tests + 74+ TS tests pass, calibration corpus stable
  owner_surface: Process Guild
  classification: unclassified
  repo_boundary: D:\Ambiguity (standalone, not monorepo)
  rebirth_target: TBD
```

## Modules

| ID | Name | Status |
|----|------|--------|
| CORE | Core Analysis Engine | Complete |

## What This Is

Deterministic prompt analysis — pre-flight linter that scores ambiguity (0-10), maps verbs to prediction-space containers, expands acronyms, flags missing constraints, and outputs UDL envelopes. Zero LLM calls.

## What This Is Not

- Not an LLM proxy or guardrail service
- Not a replacement for semantic validation
- Not a containerized service
- Not a multi-agent coordination tool

## Designs

- [Ambiguity Analyzer Architecture](../designs/2026-05-30-ambiguity-analyzer.design.md)
