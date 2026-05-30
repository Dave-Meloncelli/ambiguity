"""Response-side analysis — evaluate LLM responses for quality, constraint compliance, and clarity."""

from dataclasses import dataclass, field
from .parser import parse as parse_prompt
from .scoring import AmbiguityScore

WEASEL_WORDS: set[str] = {
    "basically", "essentially", "simply", "just", "actually",
    "literally", "virtually", "practically", "nearly", "almost",
    "sort of", "kind of", "in a sense", "in a way", "more or less",
    "to some extent", "to a certain extent", "perhaps", "maybe",
    "arguably", "debatably", "reportedly", "allegedly", "supposedly",
    "i think", "i believe", "i feel", "it seems", "it appears",
    "it might", "it could", "possibly", "probably", "seems like",
    "in my opinion", "from my perspective", "as far as i know",
}

FILLER_PATTERNS: list[str] = [
    "let me", "i'll go ahead and", "i'm going to", "i would like to",
    "feel free to", "don't hesitate to", "please note that",
    "it is worth noting that", "it is important to note that",
    "it goes without saying", "needless to say",
    "it should be noted that", "it is worth mentioning",
    "i wanted to", "i'm happy to", "i'd be happy to",
    "you can also", "you might want to", "you may want to",
]

HALLUCINATION_MARKERS: list[str] = [
    "i don't actually have", "i cannot actually",
    "in theory", "hypothetically", "technically speaking",
    "based on the information provided", "based on the context",
    "as far as i understand", "to the best of my knowledge",
    "i don't have access to", "i'm not able to",
    "unfortunately i", "i apologize", "i'm sorry",
]

CONFIDENCE_MARKERS: dict[str, float] = {
    "definitely": 1.0, "certainly": 1.0, "undoubtedly": 1.0,
    "without a doubt": 1.0, "absolutely": 1.0, "always": 0.9,
    "never": 0.9, "guaranteed": 1.0, "i confirm": 1.0,
    "i guarantee": 1.0, "i'm certain": 1.0, "i'm sure": 1.0,
    "i know": 0.9, "i understand": 0.8, "i see": 0.5,
    "likely": 0.4, "unlikely": 0.4, "probably": 0.3,
    "possibly": 0.2, "maybe": 0.1, "perhaps": 0.1,
    "might": 0.2, "could": 0.2, "may": 0.2,
    "potentially": 0.3, "presumably": 0.2,
}

BOILERPLATE_MARKERS: list[str] = [
    "if you have any questions", "let me know if",
    "i hope this helps", "feel free to reach out",
    "don't hesitate to ask", "please let me know",
    "hope this clarifies", "hope this answers",
    "if anything is unclear", "happy to help",
    "glad to help", "you're welcome",
]


@dataclass
class ReviewIssue:
    kind: str
    detail: str
    severity: str  # "info" | "warning" | "error"


@dataclass
class ReviewResult:
    prompt: str
    response: str
    score: float
    band: str
    issues: list[ReviewIssue] = field(default_factory=list)
    word_count: int = 0
    sentence_count: int = 0
    hedging_count: int = 0
    filler_count: int = 0
    hallucination_signals: list[str] = field(default_factory=list)
    confidence_signals: dict[str, float] = field(default_factory=dict)
    constraint_compliance: dict[str, bool] = field(default_factory=dict)
    unaddressed_verbs: list[str] = field(default_factory=list)
    boilerplate_lines: int = 0


def _lower_words(text: str) -> set[str]:
    import re
    return set(re.findall(r'\b\w+\b', text.lower()))


def _find_phrases(text: str, phrases: list[str]) -> list[str]:
    lower = text.lower()
    found: list[str] = []
    for phrase in phrases:
        import re
        if re.search(r'\b' + re.escape(phrase) + r'\b', lower):
            found.append(phrase)
    return found


def _find_phrases_dict(text: str, phrases: dict[str, float]) -> dict[str, float]:
    lower = text.lower()
    found: dict[str, float] = {}
    for phrase, score in phrases.items():
        import re
        if re.search(r'\b' + re.escape(phrase) + r'\b', lower):
            found[phrase] = score
    return found


def _check_constraint_compliance(prompt_constraints: list[str], response: str) -> dict[str, bool]:
    lower = response.lower()
    compliance: dict[str, bool] = {}
    for constraint in prompt_constraints:
        if constraint == "negation":
            compliance["no_negation_ignored"] = not bool(
                _find_phrases(response, ["but", "however", "although", "alternatively"])
            )
        elif constraint == "exact":
            compliance["exact_followed"] = True
        elif constraint == "dependency":
            compliance["dependency_respected"] = True
        elif constraint == "requirement":
            compliance["requirement_met"] = True
        else:
            compliance[constraint] = True
    return compliance


def _review_response(prompt: str, response: str) -> ReviewResult:
    import re

    if not response.strip():
        return ReviewResult(
            prompt=prompt,
            response="",
            score=10.0,
            band="very high",
            issues=[ReviewIssue("empty", "response is empty", "error")],
        )

    prompt_result = parse_prompt(prompt)
    prompt_score = AmbiguityScore(prompt_result)
    words = response.split()
    word_count = len(words)
    sentences = re.split(r'[.!?]+', response)
    sentence_count = len([s for s in sentences if s.strip()])

    hedging_found = _find_phrases(response, list(WEASEL_WORDS))
    filler_found = _find_phrases(response, list(FILLER_PATTERNS))
    hallucination_found = _find_phrases(response, list(HALLUCINATION_MARKERS))
    confidence_found = _find_phrases_dict(response, CONFIDENCE_MARKERS)
    boilerplate_found = _find_phrases(response, list(BOILERPLATE_MARKERS))

    issues: list[ReviewIssue] = []

    if hedging_found:
        issues.append(ReviewIssue(
            "hedging", f"response uses {len(hedging_found)} hedging phrase(s): {', '.join(hedging_found[:5])}", "warning"
        ))
    if filler_found:
        issues.append(ReviewIssue(
            "filler", f"response contains {len(filler_found)} filler phrase(s)", "info"
        ))
    if hallucination_found:
        issues.append(ReviewIssue(
            "hallucination_signal", f"hallucination/uncertainty markers: {', '.join(hallucination_found[:3])}", "error"
        ))
    if boilerplate_found:
        issues.append(ReviewIssue(
            "boilerplate", f"{len(boilerplate_found)} boilerplate closing line(s) detected", "info"
        ))
    if confidence_found:
        avg_conf = sum(confidence_found.values()) / len(confidence_found)
        if avg_conf < 0.3:
            issues.append(ReviewIssue(
                "low_confidence",
                f"average confidence marker weight is {avg_conf:.2f} (low)",
                "warning"
            ))

    # constraint compliance
    if prompt_result.constraints:
        compliance = _check_constraint_compliance(prompt_result.constraints, response)
        unaddressed = [k for k, v in compliance.items() if not v]
        if unaddressed:
            issues.append(ReviewIssue(
                "constraint_breach",
                f"prompt constraints may be unaddressed: {', '.join(unaddressed)}",
                "error"
            ))
    else:
        compliance = {}

    # find unaddressed verbs
    unaddressed_verbs: list[str] = []
    for verb in prompt_result.verbs:
        verb_lower = verb.lower()
        if verb_lower not in _lower_words(response):
            unaddressed_verbs.append(verb)
    if unaddressed_verbs:
        issues.append(ReviewIssue(
            "unaddressed_verb",
            f"verbs from prompt not reflected in response: {', '.join(unaddressed_verbs[:5])}",
            "warning"
        ))

    # check response length ratio vs prompt
    prompt_len = len(prompt.split())
    ratio = word_count / max(prompt_len, 1)
    if ratio > 15:
        issues.append(ReviewIssue(
            "verbose",
            f"response is {ratio:.0f}x longer than prompt ({word_count} vs {prompt_len} words)",
            "info"
        ))
    elif ratio < 0.5 and prompt_len > 5:
        issues.append(ReviewIssue(
            "too_short",
            f"response is only {ratio:.1f}x the prompt length ({word_count} vs {prompt_len} words)",
            "warning"
        ))

    # compute score
    base = prompt_score.total if prompt_score.total < 5.0 else 3.0
    score = base
    score += min(len(hedging_found) * 0.3, 1.5)
    score += min(len(filler_found) * 0.1, 0.5)
    score += min(len(hallucination_found) * 0.5, 2.0)
    score -= min(len(confidence_found) * 0.1, 1.0)
    score += min(len(unaddressed_verbs) * 0.3, 1.0)
    if prompt_result.constraints:
        breached = sum(1 for v in compliance.values() if not v)
        score += min(breached * 0.5, 1.5)
    score = max(0.0, min(10.0, score))

    bands = [
        (8.0, 10.0, "very high"),
        (6.0, 8.0, "high"),
        (3.0, 6.0, "medium"),
        (0.0, 3.0, "low"),
    ]
    band = "medium"
    for lo, hi, label in bands:
        if lo <= score < hi:
            band = label
            break

    return ReviewResult(
        prompt=prompt,
        response=response,
        score=round(score, 1),
        band=band,
        issues=issues,
        word_count=word_count,
        sentence_count=sentence_count,
        hedging_count=len(hedging_found),
        filler_count=len(filler_found),
        hallucination_signals=hallucination_found[:3],
        confidence_signals=confidence_found,
        constraint_compliance=compliance if prompt_result.constraints else {},
        unaddressed_verbs=unaddressed_verbs,
        boilerplate_lines=len(boilerplate_found),
    )


def review(prompt: str, response: str) -> ReviewResult:
    """Analyze an LLM response against the original prompt."""
    return _review_response(prompt, response)


def render_review_report(r: ReviewResult) -> str:
    sep = "=" * 56
    lines = [
        sep,
        "  ambiguity review — response-side analysis",
        sep,
        "",
        f"  Score: {r.score}/10 ({r.band})",
        f"  Response: {r.word_count} words, {r.sentence_count} sentences",
        "",
    ]
    if not r.issues:
        lines.append("  No issues detected.", sep)
        return "\n".join(lines)

    severity_symbol = {"error": "[X]", "warning": "[!]", "info": "[i]"}
    for issue in r.issues:
        sym = severity_symbol.get(issue.severity, "[*]")
        lines.append(f"  {sym} {issue.severity.upper()}: {issue.detail[:64]}")

    if r.unaddressed_verbs:
        lines.append("")
        lines.append(f"  Unaddressed verbs: {', '.join(r.unaddressed_verbs)}")
    if r.constraint_compliance:
        lines.append("")
        lines.append("  Constraint compliance:")
        for k, v in r.constraint_compliance.items():
            sym = "[OK]" if v else "[X]"
            lines.append(f"    {sym} {k}")
    if r.confidence_signals:
        lines.append("")
        avg = sum(r.confidence_signals.values()) / len(r.confidence_signals)
        lines.append(f"  Avg confidence: {avg:.2f} ({len(r.confidence_signals)} signals)")

    lines.append(sep)
    return "\n".join(lines)


def render_review_json(r: ReviewResult) -> dict:
    return {
        "command": "review",
        "prompt": r.prompt,
        "response": r.response,
        "score": r.score,
        "band": r.band,
        "issues": [
            {"kind": i.kind, "detail": i.detail, "severity": i.severity}
            for i in r.issues
        ],
        "word_count": r.word_count,
        "sentence_count": r.sentence_count,
        "hedging_count": r.hedging_count,
        "filler_count": r.filler_count,
        "hallucination_signals": r.hallucination_signals,
        "confidence_signals": r.confidence_signals,
        "constraint_compliance": r.constraint_compliance,
        "unaddressed_verbs": r.unaddressed_verbs,
        "boilerplate_lines": r.boilerplate_lines,
    }
