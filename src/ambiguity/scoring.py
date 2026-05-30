"""Scoring functions — ambiguity, specificity, container overlap, entropy."""

from .parser import ParseResult
from .containers import (
    containers_for_verb,
    containers_for_keyword,
)


class AmbiguityScore:
    verb_specificity: float
    container_overlap: int
    entropy_indicators: list[str]
    unqualified_refs: int
    constraint_count: int
    instruction_density: float
    total: float
    band: str

    def __init__(self, result: ParseResult, rhetoric=None, chunking=None, profile=None):
        suppressed = set(profile.suppressed_flags()) if profile else set()
        self.verb_specificity = _verb_specificity(result.verbs)
        self.container_overlap = _container_overlap(result.verbs, result.keywords)
        self.entropy_indicators = _entropy_indicators(result, rhetoric=rhetoric, chunking=chunking, suppressed=suppressed)
        self.unqualified_refs = len(result.unqualified_refs)
        self.constraint_count = len(result.constraints)
        self.instruction_density = _instruction_density(result)
        self.total = _total_score(self, result, rhetoric=rhetoric, chunking=chunking)
        self.band = _band(self.total)

    def __repr__(self) -> str:
        return (
            f"AmbiguityScore(total={self.total:.1f}, band={self.band}, "
            f"verb_specificity={self.verb_specificity:.2f}, "
            f"container_overlap={self.container_overlap}, "
            f"unqualified_refs={self.unqualified_refs}, "
            f"constraints={self.constraint_count})"
        )


def _verb_specificity(verbs: list[str]) -> float:
    if not verbs:
        return 0.0
    scores = [containers_for_verb(v)[1] for v in verbs]
    return sum(scores) / len(scores)


def _container_overlap(verbs: list[str], keywords: list[str]) -> int:
    all_containers: set[str] = set()
    for v in verbs:
        cs, _ = containers_for_verb(v)
        all_containers.update(cs)
    for kw in keywords:
        all_containers.update(containers_for_keyword(kw))
    return len(all_containers)


def _entropy_indicators(result: ParseResult, rhetoric=None, chunking=None, suppressed: set[str] | None = None) -> list[str]:
    suppressed = suppressed or set()
    indicators = []
    if result.instruction_count > 3:
        indicators.append(f"{result.instruction_count} instructions in one prompt")
    if not result.verbs and "no action verb detected" not in suppressed:
        indicators.append("no action verb detected")
    if len(result.unqualified_refs) > 0:
        indicators.append(f"unqualified references: {', '.join(result.unqualified_refs[:3])}")
    verb_spec = _verb_specificity(result.verbs)
    if verb_spec < 0.3 and result.verbs:
        verbs_str = ", ".join(result.verbs)
        indicators.append(f"vague verb(s): {verbs_str}")
    if not result.constraints:
        indicators.append("no explicit constraints")
    if result.acronyms:
        acronyms_str = ", ".join(a for a, _ in result.acronyms)
        indicators.append(f"acronyms (expand: {acronyms_str})")
    if result.vocab_scope:
        terms_str = ", ".join(f"{vt.term} ({vt.domain})" for vt in result.vocab_scope[:5])
        indicators.append(f"domain-specific vocabulary used without definition: {terms_str}")

    # Rhetoric indicators
    if rhetoric:
        for ri in rhetoric.rhetoric_indicators:
            if ri not in suppressed:
                indicators.append(ri)

    # Chunking indicators
    if chunking:
        for ci in chunking.clause_indicators:
            if ci not in suppressed:
                indicators.append(ci)

    return indicators


def _instruction_density(result: ParseResult) -> float:
    if result.word_count == 0:
        return 0.0
    return result.instruction_count / (result.word_count / 10)


def _total_score(score: AmbiguityScore, result: ParseResult, rhetoric=None, chunking=None) -> float:
    base = 5.0
    base -= score.verb_specificity * 2.0
    base += min(score.container_overlap * 0.5, 2.0)
    base += len(score.entropy_indicators) * 0.5
    base += score.unqualified_refs * 0.5
    base -= min(score.constraint_count * 0.5, 2.0)
    base += min(len(result.vocab_scope) * 0.3, 1.5)

    if rhetoric:
        base += rhetoric.rhetoric_penalty
    if chunking and chunking.has_contradictions:
        base += 0.5
    if chunking and chunking.clause_count > 4:
        base += 0.3

    return max(0.0, min(10.0, base))


SCORE_BANDS = [
    (0.0, 3.0, "low"),
    (3.0, 6.0, "medium"),
    (6.0, 8.0, "high"),
    (8.0, 10.0, "very high"),
]


def _band(total: float) -> str:
    for lo, hi, label in SCORE_BANDS:
        if lo <= total < hi:
            return label
    return "very high"
