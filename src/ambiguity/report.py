"""Terminal output formatting for analysis results."""

import sys
import textwrap

from .parser import ParseResult
from .scoring import AmbiguityScore
from .containers import (
    containers_for_verb,
    specificity_band,
    containers_for_keyword,
)
from .advisory import advisory

_USE_UNICODE = sys.stdout.encoding and sys.stdout.encoding.lower() in ("utf-8", "utf8")

if _USE_UNICODE:
    BOX = "\u2501"
    V = "\u2502"
    TL = "\u250f"
    TR = "\u2513"
    BL = "\u2517"
    BR = "\u251b"
    TE = "\u2523"
    BE = "\u252b"
    DOT = "\u2022"
    OK = "\u2714"
    WARN = "\u26a0"
    BAD = "\u2716"
else:
    BOX = "="
    V = "|"
    TL = "+"
    TR = "+"
    BL = "+"
    BR = "+"
    TE = "+"
    BE = "+"
    DOT = "*"
    OK = "[OK]"
    WARN = "[!]"
    BAD = "[X]"


def render_report(result: ParseResult, score: AmbiguityScore, udl_info: str | None = None) -> str:
    lines = []
    width = 64

    header = "ambiguity analyze v0.1"
    spacer = " " * (width - len(header) - 2)

    lines.append(f"{TL}{BOX * (width - 2)}{TR}")
    lines.append(f"{V} {header}{spacer}{V}")
    lines.append(f"{TE}{BOX * (width - 2)}{BE}")

    def row(label: str, value: str):
        if not label:
            content = value
        else:
            content = f"{label}: {value}"
        line = content[:width - 4]
        lines.append(f"{V}  {line.ljust(width - 4)}{V}")

    row("Language", "English")
    row("Ambiguity Score", f"{score.total:.1f}/10 ({score.band})")

    band_symbol = {"low": OK, "medium": WARN, "high": WARN, "very high": BAD}
    sym = band_symbol.get(score.band, "?")
    adv = advisory(result, score)
    if adv:
        tip_label = f"  {sym} Tip"
        tip_prefix = f"{tip_label}: "
        body_w = width - 4 - len(tip_prefix)
        wrapped = textwrap.wrap(adv, width=max(body_w, 30))
        for i, wline in enumerate(wrapped):
            prefix = tip_prefix if i == 0 else " " * len(tip_prefix)
            display = f"{prefix}{wline}"[:width - 4]
            lines.append(f"{V}  {display.ljust(width - 4)}{V}")

    lines.append(f"{TE}{BOX * (width - 2)}{BE}")

    for verb in result.verbs:
        containers, spec = containers_for_verb(verb)
        band = specificity_band(spec)
        c_str = ", ".join(containers) if containers else "(none)"
        fuzzy = None
        for fv in result.fuzzy_verbs:
            if fv.corrected == verb:
                fuzzy = fv
                break
        verb_label = (
            f"{verb} (from '{fv.original}')" if fuzzy else verb
        )
        row(f"  Verb: {verb_label}", f"{band}  spec: {spec:.2f}  [{c_str}]")

    if result.typo_words:
        row("Typos", ", ".join(f"{t.original}->{t.corrected}" for t in result.typo_words))
    if result.missing_spaces:
        row("Misspaces", ", ".join(f"{m.combined}->{m.split[0]} {m.split[1]}" for m in result.missing_spaces))
    if result.stutter_words:
        row("Stutter", ", ".join(f"{s.word}x{s.occurrences}" for s in result.stutter_words))
    if result.repeated_chars:
        row("RepeatCh", ", ".join(result.repeated_chars))
    if not result.has_terminal_punctuation and result.word_count > 3:
        row("Punct", "no terminal punctuation")

    lines.append(f"{TE}{BOX * (width - 2)}{BE}")

    row("Keywords", ", ".join(result.keywords[:6]) if result.keywords else "(none)")
    row("Constraints", ", ".join(result.constraints) if result.constraints else "(none)")
    row("Acronyms", ", ".join(f"{a}->{e}" for a, e in result.acronyms) if result.acronyms else "(none)")
    if result.vocab_scope:
        row("Vocab", ", ".join(f"{vt.term}({vt.domain})" for vt in result.vocab_scope[:4]))
    row("Instructions", str(result.instruction_count))
    row("Words", str(result.word_count))

    lines.append(f"{TE}{BOX * (width - 2)}{BE}")

    if score.entropy_indicators:
        row("Issues", "")
        for indicator in score.entropy_indicators[:5]:
            row(f"  {DOT}", indicator[:width - 8])

    if udl_info:
        lines.append(f"{TE}{BOX * (width - 2)}{BE}")
        row("UDL Envelope", udl_info)

    lines.append(f"{BL}{BOX * (width - 2)}{BR}")

    return "\n".join(lines)


def render_json(result: ParseResult, score: AmbiguityScore) -> dict:
    return {
        "version": "0.1.0",
        "language": "English",
        "ambiguity_score": {
            "total": round(score.total, 1),
            "band": score.band,
            "verb_specificity": round(score.verb_specificity, 2),
            "container_overlap": score.container_overlap,
            "unqualified_refs": score.unqualified_refs,
            "constraint_count": score.constraint_count,
            "instruction_density": round(score.instruction_density, 2),
            "entropy_indicators": score.entropy_indicators,
        },
        "advisory": advisory(result, score),
        "analysis": {
            "verbs": [
                {
                    "word": v,
                    "containers": containers_for_verb(v)[0],
                    "specificity": containers_for_verb(v)[1],
                    "band": specificity_band(containers_for_verb(v)[1]),
                }
                for v in result.verbs
            ],
            "keywords": [
                {
                    "word": kw,
                    "containers": containers_for_keyword(kw),
                }
                for kw in result.keywords
            ],
            "constraints": result.constraints,
            "acronyms": [{"abbreviation": a, "expansion": e} for a, e in result.acronyms],
            "vocabulary_scope": [{"term": vt.term, "domain": vt.domain} for vt in result.vocab_scope],
            "unqualified_refs": result.unqualified_refs,
            "fuzzy_verbs": [{"original": fv.original, "corrected": fv.corrected, "distance": fv.distance} for fv in result.fuzzy_verbs],
            "typo_words": [{"original": tw.original, "corrected": tw.corrected, "distance": tw.distance} for tw in result.typo_words],
            "stutter_words": [{"word": sw.word, "occurrences": sw.occurrences} for sw in result.stutter_words],
            "missing_spaces": [{"combined": ms.combined, "split": list(ms.split)} for ms in result.missing_spaces],
            "repeated_chars": result.repeated_chars,
            "has_terminal_punctuation": result.has_terminal_punctuation,
            "word_count": result.word_count,
            "sentence_count": result.sentence_count,
            "instruction_count": result.instruction_count,
        },
    }
