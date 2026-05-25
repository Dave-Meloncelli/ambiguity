---
chap_anchor_v1:
  surface_id: "ambiguity_analyzer_v1"
  host_path: "D:\\Ambiguity"
  federation_registry: "C:\\Federation\\federation\\registry\\CHAP_AMBIGUITY_ANALYZER_ENTRY_20260525.md"
  retained_surfaces_key: "ambiguity_analyzer"
  udl_bridge: "src/ambiguity/bridges.py"
  proof_condition: "ambiguity_score < 6.0 AND verb_specificity > 0.3"
---

# CHAP Anchor — ambiguity-analyzer

This file anchors the ambiguity-analyzer surface back to its Federation CHAP
registration. Agents discovering this project can trace the surface through
the Federation's retained surfaces canon.

## Federation integration

| Aspect | Location |
|--------|----------|
| Surface entry | `C:\Federation\federation\registry\CHAP_AMBIGUITY_ANALYZER_ENTRY_20260525.md` |
| Profile | `C:\Federation\federation\processes\specs\CHAP_AMBIGUITY_ANALYZER_PROFILE_20260525.md` |
| Capability packet | `C:\Federation\federation\registry\CHAP_AMBIGUITY_ANALYZER_CAPABILITY_PACKET_20260525.md` |
| Retained surfaces | `C:\Federation\federation\registry\RETAINED_SURFACES_CANON.json` (key: `ambiguity_analyzer`) |
| UDL bridge | `src/ambiguity/bridges.py` (try/import from Federation) |

## Consumption

From Federation workflows, call:

```bash
python -m ambiguity analyze --pipe --json < prompt.txt
```

If score >= 6.0, invoke `/fleshitout` to structure the prompt before submission.
