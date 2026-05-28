"""Bridges to Federation infrastructure — UDL envelope wrapping.
Preserves all analysis dimensions; no flattening of individual considerations."""

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


def _build_normalized_view(result: ParseResult, score: AmbiguityScore) -> dict[str, Any]:
    return {
        "ambiguity_score": round(score.total, 1),
        "band": score.band,
        "verb_specificity": round(score.verb_specificity, 2),
        "container_overlap": score.container_overlap,
        "constraint_count": score.constraint_count,
        "instruction_density": round(score.instruction_density, 2),
        "unqualified_ref_count": len(result.unqualified_refs),
        "entropy_indicator_count": len(score.entropy_indicators),
        "entropy_indicators": score.entropy_indicators,
        "has_terminal_punctuation": result.has_terminal_punctuation,
        "word_count": result.word_count,
        "sentence_count": result.sentence_count,
        "instruction_count": result.instruction_count,
    }


def _build_analysis(result: ParseResult) -> dict[str, Any]:
    return {
        "verbs": [
            {
                "word": v,
                "containers": _containers.containers_for_verb(v)[0],
                "specificity": _containers.containers_for_verb(v)[1],
                "band": _containers.specificity_band(_containers.containers_for_verb(v)[1]),
            }
            for v in result.verbs
        ],
        "fuzzy_verb_matches": [
            {"original": fv.original, "corrected": fv.corrected, "distance": fv.distance}
            for fv in result.fuzzy_verbs
        ],
        "keywords": result.keywords,
        "constraints": result.constraints,
        "acronyms": [{"abbreviation": a, "expansion": e} for a, e in result.acronyms],
        "vocabulary_scope": [{"term": vt.term, "domain": vt.domain} for vt in result.vocab_scope],
        "unqualified_refs": result.unqualified_refs,
        "typo_words": [
            {"original": tw.original, "corrected": tw.corrected, "distance": tw.distance}
            for tw in result.typo_words
        ],
        "missing_spaces": [
            {"combined": ms.combined, "split": list(ms.split)}
            for ms in result.missing_spaces
        ],
        "stutter_words": [
            {"word": sw.word, "occurrences": sw.occurrences}
            for sw in result.stutter_words
        ],
        "repeated_chars": result.repeated_chars,
    }


def as_udl_envelope(result: ParseResult, score: AmbiguityScore) -> dict[str, Any] | str | None:
    """Wrap full analysis into a UDL envelope if Federation schema is available."""
    build_fn, _ = _import_udl_envelope()
    if build_fn is None:
        return None

    norm = _build_normalized_view(result, score)
    analysis = _build_analysis(result)

    bridge = {
        "job_story": "Analyze prompt for ambiguity before LLM processing",
        "proof_condition": "ambiguity_score < 6.0 AND verb_specificity > 0.3 AND no critical entropy indicators",
        "baseline_shape": result.text,
        "evidence_signals": score.entropy_indicators,
        "constraint_summary": result.constraints,
        "vocabulary_scope": [vt.term for vt in result.vocab_scope],
        "status": "analyzed",
    }

    envelope = build_fn(
        surface="ambiguity_framework",
        agent_id="ambiguity_analyzer_v0.1",
        raw_payload={
            "prompt": result.text,
            **norm,
            **analysis,
        },
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
    """Standalone envelope format — preserves all analysis dimensions."""
    norm = _build_normalized_view(result, score)
    analysis = _build_analysis(result)

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
            "sentence_count": result.sentence_count,
            "instruction_count": result.instruction_count,
        },
        "normalized_view": norm,
        "analysis": analysis,
    }
