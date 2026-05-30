# APS Rules for AI Agents — ambiguity

> See `D:\Project\plans\aps-rules.md` for the full canonical APS agent guidance.
> This file documents ambiguity-specific conventions and deviations.

## Core Principle

**Specs describe intent. Work items authorise execution. Actions are checkpoints, not tutorials.**

## Deviation from Canonical APS

| Rule | Canonical | ambiguity | Rationale |
|------|-----------|-----------|-----------|
| `plans/` location | `plans/` at project root | `plans/` at project root | Aligned |
| `designs/` location | `designs/` at project root or `plans/designs/` | `designs/` at project root | Aligned |
| Dual implementation | N/A | Python + TS must stay in sync | Project is dual-language |
| Module statuses | Draft / Ready / In Progress / Complete | All CORE items are Complete | Project is v1.0 stable |
