"""Generate clarification questions from ambiguity analysis."""

from dataclasses import dataclass, field
from typing import Any

from .analyzer import Analysis
from .containers import VERB_TAXONOMY


@dataclass
class Clarification:
    prompt: str
    score: float
    band: str
    questions: list[dict[str, str]] = field(default_factory=list)


QUESTION_TEMPLATES: dict[str, str] = {
    "vague_verb": "What specific action should '{value}' map to? (e.g. implement, convert, verify, generate)",
    "no_verb": "What should this prompt do? No action verb detected.",
    "no_constraints": "What boundaries apply? (language, dependencies, format, or performance constraints)",
    "acronym": "What does '{value}' stand for?",
    "unqualified_ref": "What does '{value}' refer to? Be specific.",
    "vocab_scope": "What domain does '{value}' belong to? (ecosystem, technical, or metaphor)",
    "multi_instruction": "Which instruction should take priority? This prompt has multiple requests.",
    "typo": "Did you mean '{corrected}' instead of '{original}'?",
}


def extract_clarifications(indicator: str) -> str | None:
    for key, template in QUESTION_TEMPLATES.items():
        if key in indicator:
            return template
    return None


def clarify(prompt: str) -> Clarification:
    analysis = Analysis(prompt)
    questions: list[dict[str, str]] = []

    for indicator in analysis.score.entropy_indicators:
        template = extract_clarifications(indicator)

        if template:
            raw = indicator.split(":")[-1].strip() if ":" in indicator else indicator
            value = raw.rstrip(")").strip()
            questions.append({
                "indicator": indicator,
                "question": template.format(
                    value=value,
                    original=indicator,
                    corrected="",
                ),
            })

    for verb in analysis.result.verbs:
        if verb in VERB_TAXONOMY and VERB_TAXONOMY[verb].get("specificity", 0.5) < 0.3:
            existing = any("vague_verb" in q["indicator"] for q in questions)
            if not existing:
                questions.append({
                    "indicator": f"vague_verb: {verb}",
                    "question": QUESTION_TEMPLATES["vague_verb"].format(value=verb),
                })

    for acronym, expansion in analysis.result.acronyms:
        if expansion == "unknown":
            questions.append({
                "indicator": f"acronym: {acronym}",
                "question": QUESTION_TEMPLATES["acronym"].format(value=acronym),
            })

    return Clarification(
        prompt=prompt,
        score=analysis.score.total,
        band=analysis.score.band,
        questions=questions,
    )


def render_clarify_report(c: Clarification) -> str:
    lines = []
    sep = "=" * 56
    lines.append(sep)
    lines.append("  ambiguity clarify — request clarification")
    lines.append(sep)
    lines.append("")
    lines.append(f"  Score: {c.score:.1f}/10 ({c.band})")

    if not c.questions:
        lines.append("  No clarification needed.")
        lines.append(sep)
        return "\n".join(lines)

    lines.append("")
    lines.append(f"  {len(c.questions)} clarification question(s):")
    lines.append("")
    for i, q in enumerate(c.questions, 1):
        lines.append(f"  {i}. {q['question']}")
    lines.append("")
    lines.append(f"  {sep}")
    lines.append("  How to use: answer each question, then re-run the prompt")
    lines.append(f"  {sep}")
    return "\n".join(lines)


def render_clarify_json(c: Clarification) -> dict[str, Any]:
    return {
        "command": "clarify",
        "prompt": c.prompt,
        "score": round(c.score, 1),
        "band": c.band,
        "questions": [
            {"indicator": q["indicator"], "question": q["question"]}
            for q in c.questions
        ],
        "question_count": len(c.questions),
    }
