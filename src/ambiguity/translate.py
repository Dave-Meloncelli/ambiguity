"""Translate ambiguous prompts into clearer versions for agent consumption."""

from dataclasses import dataclass, field
from typing import Any

from .analyzer import Analysis
from .containers import VERB_TAXONOMY


@dataclass
class Translation:
    original: str
    translated: str
    changes: list[dict[str, str]] = field(default_factory=list)
    score_before: float = 0.0
    score_after: float = 0.0
    band_before: str = ""
    band_after: str = ""


def _expand_acronyms(text: str, analysis: Analysis) -> list[dict[str, str]]:
    changes = []
    for acronym, expansion in analysis.result.acronyms:
        if expansion and expansion != "unknown":
            replacement = f"{acronym} ({expansion})"
            if acronym in text:
                changes.append({"type": "acronym", "original": acronym, "replacement": replacement})
    return changes


def _replace_vague_verbs(text: str, analysis: Analysis) -> list[dict[str, str]]:
    changes = []
    for verb in analysis.result.verbs:
        if verb in VERB_TAXONOMY:
            entry = VERB_TAXONOMY[verb]
            spec = entry.get("specificity", 0.5)
            alt = entry.get("alternatives", [])
            if spec < 0.3 and alt:
                changes.append({"type": "vague_verb", "original": verb, "replacement": f"{alt[0]} ({verb})"})
    return changes


def _flag_unqualified_refs(text: str, analysis: Analysis) -> list[dict[str, str]]:
    changes = []
    for ref in analysis.result.unqualified_refs:
        if ref.lower() in ("it", "thing", "stuff", "something", "that"):
            changes.append({"type": "unqualified_ref", "original": ref, "replacement": f"<<{ref}>>"})
    return changes


def _add_constraint_reminder(text: str, analysis: Analysis) -> list[dict[str, str]]:
    changes = []
    if not analysis.result.constraints and analysis.score.total > 4.0:
        reminder = "\n\n[NOTE: Add explicit constraints \u2014 languages, dependencies, boundaries, or format requirements]"
        changes.append({"type": "constraint_reminder", "original": "", "replacement": reminder})
    return changes


def _add_vocab_hint(text: str, analysis: Analysis) -> list[dict[str, str]]:
    changes = []
    for vt in analysis.result.vocab_scope:
        hint = f" ({vt.domain} term)"
        changes.append({"type": "vocab_scope", "original": vt.term, "replacement": f"{vt.term}{hint}"})
    return changes


def _apply(changes: list[dict[str, str]], text: str) -> str:
    for c in changes:
        if c["type"] == "constraint_reminder":
            text += c["replacement"]
        elif c.get("original"):
            text = text.replace(c["original"], c["replacement"])
    return text


def translate(prompt: str) -> Translation:
    analysis_before = Analysis(prompt)

    changes: list[dict[str, str]] = []
    text = prompt

    c = _expand_acronyms(text, analysis_before)
    changes.extend(c)
    text = _apply(c, text)

    c = _replace_vague_verbs(text, analysis_before)
    changes.extend(c)
    text = _apply(c, text)

    c = _flag_unqualified_refs(text, analysis_before)
    changes.extend(c)
    text = _apply(c, text)

    c = _add_vocab_hint(text, analysis_before)
    changes.extend(c)
    text = _apply(c, text)

    c = _add_constraint_reminder(text, analysis_before)
    changes.extend(c)
    text = _apply(c, text)

    analysis_after = Analysis(text)

    return Translation(
        original=prompt,
        translated=text,
        changes=changes,
        score_before=analysis_before.score.total,
        score_after=analysis_after.score.total,
        band_before=analysis_before.score.band,
        band_after=analysis_after.score.band,
    )


def render_translate_report(t: Translation) -> str:
    lines = []
    sep = "=" * 56
    lines.append(sep)
    lines.append("  ambiguity translate — prompt de-ambiguation")
    lines.append(sep)
    lines.append("")
    lines.append(f"  Score: {t.score_before:.1f}/10 ({t.band_before})")
    if not t.changes:
        lines.append("  No changes needed.")
        lines.append(sep)
        return "\n".join(lines)

    lines.append("")
    lines.append("  Changes applied:")
    for c in t.changes:
        sym = {"acronym": "A", "vague_verb": "V", "unqualified_ref": "?", "vocab_scope": "S", "constraint_reminder": "C"}.get(c["type"], "*")
        if c["type"] == "constraint_reminder":
            lines.append(f"    [{sym}] Added constraint reminder")
        else:
            lines.append(f"    [{sym}] {c['original']}  ->  {c['replacement']}")
    lines.append("")
    lines.append("  Translated prompt:")
    for line in t.translated.split("\n"):
        lines.append(f"    | {line}")
    lines.append("")
    lines.append(f"  New score: {t.score_after:.1f}/10 ({t.band_after})")
    lines.append(sep)
    return "\n".join(lines)


def render_translate_json(t: Translation) -> dict[str, Any]:
    return {
        "command": "translate",
        "original": t.original,
        "translated": t.translated,
        "score_before": round(t.score_before, 1),
        "score_after": round(t.score_after, 1),
        "band_before": t.band_before,
        "band_after": t.band_after,
        "changes": t.changes,
    }
