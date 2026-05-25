"""Bridges to Federation infrastructure — UDL envelope wrapping."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from . import containers as _containers
from .parser import ParseResult
from .scoring import AmbiguityScore


def _import_udl_envelope():
    """Try to import the Federation's UDL envelope. Falls back to None."""
    fed_path = r"C:\Federation"
    if fed_path not in sys.path:
        sys.path.insert(0, fed_path)
    try:
        from federation.registry.schemas.UNIFIED_DATA_LAYER_ENVELOPE import (
            UnifiedDataLayerEnvelope,
            build_unified_data_layer_envelope,
        )
        return build_unified_data_layer_envelope, UnifiedDataLayerEnvelope
    except ImportError:
        return None, None


def as_udl_envelope(result: ParseResult, score: AmbiguityScore) -> dict[str, Any] | str | None:
    """Wrap analysis results into a UDL envelope if Federation schema is available."""
    build_fn, _ = _import_udl_envelope()
    if build_fn is None:
        return None

    raw = {
        "prompt": result.text,
        "word_count": result.word_count,
        "sentence_count": result.sentence_count,
        "instruction_count": result.instruction_count,
    }

    bridge = {
        "job_story": "Analyze prompt for ambiguity before LLM processing",
        "proof_condition": "ambiguity_score < 6.0 AND verb_specificity > 0.3 AND no critical entropy indicators",
        "baseline_shape": result.text,
        "evidence_signals": score.entropy_indicators,
        "constraint_summary": result.constraints,
        "status": "analyzed",
    }

    envelope = build_fn(
        surface="ambiguity_framework",
        agent_id="ambiguity_analyzer_v0.1",
        raw_payload=raw,
        run_id=f"run_{uuid4().hex[:8]}",
        source_of_truth="D:\\Ambiguity",
        intent="Analyze prompt for translation ambiguity",
        provenance={
            "created_at": datetime.now(timezone.utc).isoformat(),
            "tool_version": "0.1.0",
        },
        jtbd_bridge=bridge,
    )

    try:
        return envelope.model_dump_json(indent=2)
    except AttributeError:
        try:
            return envelope.json(indent=2)
        except AttributeError:
            return str(envelope)


def as_minimal_envelope(result: ParseResult, score: AmbiguityScore) -> dict[str, Any]:
    """Standalone envelope format (works without Federation UDL schema)."""
    return {
        "_envelope": {
            "format": "ambiguity_analysis_v1",
            "version": "0.1.0",
            "surface": "ambiguity_framework",
            "agent": "ambiguity_analyzer",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        "intent": "Analyze prompt for translation ambiguity",
        "raw_payload": {
            "prompt": result.text,
            "word_count": result.word_count,
            "instruction_count": result.instruction_count,
        },
        "normalized_view": {
            "ambiguity_score": round(score.total, 1),
            "band": score.band,
            "verb_specificity": round(score.verb_specificity, 2),
            "container_count": score.container_overlap,
            "constraint_count": score.constraint_count,
            "entropy_indicator_count": len(score.entropy_indicators),
            "unqualified_refs": result.unqualified_refs,
        },
        "analysis": {
            "verbs": [
                {
                    "word": v,
                    "containers": _containers.containers_for_verb(v)[0],
                    "specificity": _containers.containers_for_verb(v)[1],
                }
                for v in result.verbs
            ],
            "keywords": result.keywords,
            "constraints": result.constraints,
            "acronyms": dict(result.acronyms),
        },
    }
