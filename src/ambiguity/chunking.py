"""Clause-level chunking and multi-word verb detection — zero-dependency."""

import re
from dataclasses import dataclass, field

# Multi-word phrasal verbs — verb + particle combinations
PHRASAL_VERBS: dict[str, list[str]] = {
    "set": ["up", "down", "out", "forth", "aside"],
    "tear": ["down", "apart", "up"],
    "break": ["down", "up", "apart", "out", "into"],
    "carry": ["out", "on", "through", "forward"],
    "take": ["on", "over", "up", "out", "apart"],
    "put": ["together", "aside", "off", "on", "forward"],
    "turn": ["on", "off", "up", "down", "into"],
    "bring": ["up", "in", "on", "together", "about"],
    "come": ["up", "in", "on", "across", "apart"],
    "go": ["through", "over", "ahead", "forward", "back"],
    "look": ["into", "over", "up", "through", "for"],
    "point": ["out", "to", "at"],
    "figure": ["out"],
    "find": ["out", "a way"],
    "run": ["through", "on", "over"],
    "move": ["forward", "on", "ahead"],
    "back": ["up", "off", "away", "out"],
    "call": ["out", "up", "on", "for"],
    "map": ["out", "to"],
    "scope": ["out", "down"],
    "roll": ["out", "up", "back"],
    "reach": ["out", "in"],
    "follow": ["up", "through", "on"],
    "wire": ["up", "together"],
    "hook": ["up", "in", "together"],
    "build": ["out", "up", "on", "upon"],
    "clean": ["up", "out", "off"],
    "cut": ["down", "off", "out", "up"],
    "phase": ["out", "in"],
    "scale": ["up", "down", "out"],
    "spin": ["up", "out", "off"],
    "stand": ["up", "by"],
    "start": ["up", "out", "over"],
    "step": ["up", "back", "through", "aside"],
    "strip": ["out", "down"],
    "sum": ["up"],
    "tie": ["together", "in", "into"],
    "try": ["out", "on"],
    "use": ["up"],
    "write": ["out", "up", "down", "off"],
    "zero": ["in"],
}

# Clause boundary markers — split on these to separate instructions
CLAUSE_BOUNDARIES: list[str] = [
    r"\band\b(?!\s+then\b)",
    r"\bbut\b",
    r"\bor\b",
    r"\bso that\b",
    r"\bsuch that\b",
    r"\bprovided that\b",
    r"\bhowever\b",
    r"\btherefore\b",
    r"\bthen\b",
    r"\bnext\b",
    r"\bafterwards\b",
    r"\bmeanwhile\b",
    r"\badditionally\b",
    r"\bfurthermore\b",
    r"\bmoreover\b",
    r"\balso\b",
    r"\bconversely\b",
    r"\balternatively\b",
    r"\botherwise\b",
    r"\bfinally\b",
    r"\bsubsequently\b",
    r"\bconsequently\b",
    r"\bas a result\b",
]

# Topic shift markers — stronger boundaries indicating new instructions
TOPIC_SHIFT_MARKERS: list[str] = [
    r"\bnow\b",
    r"\bok[ay]*,?\s",
    r"\balright,?\s",
    r"\bso,?\s",
    r"\bright,?\s",
    r"\bfirst(ly)?\b",
    r"\bsecond(ly)?\b",
    r"\bthird(ly)?\b",
    r"\bfinally\b",
    r"\blast(ly)?\b",
    r"\bin addition\b",
    r"\bon the other hand\b",
    r"\bmeanwhile\b",
    r"\bmoving on\b",
    r"\bnext up\b",
]

# Contradiction markers — signals that two clauses may conflict
CONTRADICTION_MARKERS: list[re.Pattern] = [
    re.compile(r"\b(but|however|although|though|while|whereas|conversely|nevertheless|on the other hand)\b", re.IGNORECASE),
    re.compile(r"\b(yet|still|instead|rather|otherwise|alternatively)\b", re.IGNORECASE),
    re.compile(r"\b(must|required|essential)\b.*\b(but|however|although)\b", re.IGNORECASE),
    re.compile(r"\b(only|exactly|strictly)\b.*\b(also|additionally|furthermore)\b", re.IGNORECASE),
]


@dataclass
class Clause:
    text: str
    verbs: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    has_negation: bool = False
    has_hedging: bool = False
    has_emphasis: bool = False


@dataclass
class CompoundVerb:
    verb: str
    particle: str
    full: str
    position: int = 0


@dataclass
class ChunkResult:
    text: str
    clauses: list[Clause] = field(default_factory=list)
    compound_verbs: list[CompoundVerb] = field(default_factory=list)
    topic_shifts: int = 0
    contradiction_hits: list[str] = field(default_factory=list)

    @property
    def clause_count(self) -> int:
        return len(self.clauses)

    @property
    def has_contradictions(self) -> bool:
        return len(self.contradiction_hits) > 0

    @property
    def clause_indicators(self) -> list[str]:
        indicators = []
        if self.clause_count > 3:
            indicators.append(f"{self.clause_count} clauses detected (may indicate multi-instruction)")
        if self.has_contradictions:
            indicators.append(f"contradictory markers: {', '.join(self.contradiction_hits[:2])}")
        if self.compound_verbs:
            verbs = [f"{cv.full}" for cv in self.compound_verbs[:3]]
            indicators.append(f"phrasal verbs: {', '.join(verbs)}")
        if self.topic_shifts > 2:
            indicators.append(f"{self.topic_shifts} topic shifts (may indicate scope creep)")
        return indicators


def _split_clauses(text: str) -> list[str]:
    """Split text into clauses using boundary markers."""
    # First split on sentence boundaries
    clauses = re.split(r'[.!?]+', text)
    result = []
    for clause in clauses:
        clause = clause.strip()
        if not clause:
            continue
        # Further split on clause boundaries
        # Build a combined pattern from CLAUSE_BOUNDARIES
        boundary_pattern = "(" + "|".join(CLAUSE_BOUNDARIES) + ")"
        # Split preserving the boundary marker context
        parts = re.split(boundary_pattern, clause)
        current = ""
        for part in parts:
            if part and part.strip():
                current += part + " "
                # If the last word is a boundary marker, flush current
                if any(re.search(p, part.strip()) for p in CLAUSE_BOUNDARIES):
                    if current.strip():
                        result.append(current.strip())
                    current = ""
        if current.strip():
            result.append(current.strip())
    return result


def _detect_compound_verbs(tokens: list[str]) -> list[CompoundVerb]:
    """Detect multi-word phrasal verbs in token stream."""
    found: list[CompoundVerb] = []
    for i, token in enumerate(tokens):
        low = token.lower()
        if low in PHRASAL_VERBS:
            # Check next token for particle
            if i + 1 < len(tokens):
                next_token = tokens[i + 1].lower().rstrip(".!,;")
                if next_token in PHRASAL_VERBS[low]:
                    found.append(CompoundVerb(
                        verb=low,
                        particle=next_token,
                        full=f"{low}_{next_token}",
                        position=i,
                    ))
    return found


def _detect_contradictions(clauses: list[Clause]) -> list[str]:
    """Detect contradictory constraint pairs across clauses."""
    hits: list[str] = []
    for i, clause in enumerate(clauses):
        for pattern in CONTRADICTION_MARKERS:
            if pattern.search(clause.text):
                # Look for contradictory indicators in other clauses
                for j in range(i + 1, len(clauses)):
                    # Check if one clause has negation and another has requirement
                    if clauses[i].has_negation and clauses[j].has_emphasis:
                        hits.append(f"clause {i+1} (negation) vs clause {j+1} (emphasis)")
                    elif clauses[i].has_emphasis and clauses[j].has_negation:
                        hits.append(f"clause {i+1} (emphasis) vs clause {j+1} (negation)")
    return list(set(hits))


def _count_topic_shifts(clauses: list[Clause]) -> int:
    """Count topic shift markers across clauses."""
    count = 0
    for clause in clauses:
        for marker in TOPIC_SHIFT_MARKERS:
            if re.search(marker, clause.text, re.IGNORECASE):
                count += 1
    return count


def _detect_verbs_in_clause(clause_text: str, known_verbs: set[str]) -> list[str]:
    """Find known verbs present in a clause."""
    lower = clause_text.lower()
    return [v for v in known_verbs if re.search(r"\b" + re.escape(v) + r"\b", lower)]


def _detect_constraints_in_clause(clause_text: str) -> list[str]:
    """Detect constraint types present in a clause."""
    lower = clause_text.lower()
    constraints = []
    if re.search(r"\b(without|avoid|never|no |not|don't|do not|except|excluding)\b", lower):
        constraints.append("negation")
    if re.search(r"\b(must|need to|have to|required|essential)\b", lower):
        constraints.append("requirement")
    if re.search(r"\b(only|exactly|strictly|specifically|precisely)\b", lower):
        constraints.append("exact")
    if re.search(r"\b(using|with|via|through|by|import|require|dependency|library)\b", lower):
        constraints.append("dependency")
    return constraints


def chunk(text: str, known_verbs: set[str] | None = None) -> ChunkResult:
    """Analyze text into clauses, compound verbs, and contradiction patterns."""
    tokens = re.findall(r"\b\w+\b", text)
    known_verbs = known_verbs or set()
    verb_set = known_verbs

    # Detect compound verbs
    compound_verbs = _detect_compound_verbs(tokens)

    # Split into clauses
    clause_texts = _split_clauses(text)

    # Analyze each clause
    clauses: list[Clause] = []
    for ct in clause_texts:
        verbs_in = _detect_verbs_in_clause(ct, verb_set)
        constraints_in = _detect_constraints_in_clause(ct)
        has_neg = "negation" in constraints_in
        has_hedge = bool(re.search(
            r"\b(maybe|perhaps|possibly|probably|might|could|i think|i believe)\b",
            ct, re.IGNORECASE
        ))
        has_emp = bool(re.search(
            r"\b(must|absolutely|critical|urgent|essential|required|vital)\b",
            ct, re.IGNORECASE
        ))
        clauses.append(Clause(
            text=ct.strip(),
            verbs=verbs_in,
            constraints=constraints_in,
            has_negation=has_neg,
            has_hedging=has_hedge,
            has_emphasis=has_emp,
        ))

    # Detect contradictions
    contradiction_hits = _detect_contradictions(clauses)

    # Count topic shifts
    topic_shifts = _count_topic_shifts(clauses)

    return ChunkResult(
        text=text,
        clauses=clauses,
        compound_verbs=compound_verbs,
        topic_shifts=topic_shifts,
        contradiction_hits=contradiction_hits,
    )


def render_chunk_report(cr: ChunkResult) -> str:
    sep = "=" * 56
    lines = [sep]
    lines.append("  Chunk analysis")
    lines.append(sep)
    lines.append("")

    if cr.compound_verbs:
        verbs_str = ", ".join(f"{cv.full}" for cv in cr.compound_verbs)
        lines.append(f"  Phrasal verbs: {verbs_str}")
        lines.append("")

    lines.append(f"  Clauses ({cr.clause_count}):")
    for i, clause in enumerate(cr.clauses, 1):
        parts = []
        if clause.has_negation:
            parts.append("NEG")
        if clause.has_emphasis:
            parts.append("EMP")
        if clause.has_hedging:
            parts.append("HEDGE")
        tags = f"  [{', '.join(parts)}]" if parts else ""
        short = clause.text[:55]
        lines.append(f"    {i}. {short}{tags}")
        if clause.verbs:
            lines.append(f"       verbs: {', '.join(clause.verbs)}")
        if clause.constraints:
            lines.append(f"       constraints: {', '.join(clause.constraints)}")

    if cr.contradiction_hits:
        lines.append("")
        lines.append("  Potential contradictions:")
        for h in cr.contradiction_hits:
            lines.append(f"    ! {h}")

    if cr.topic_shifts > 2:
        lines.append("")
        lines.append(f"  Topic shifts: {cr.topic_shifts} (possible scope creep)")

    lines.append(sep)
    return "\n".join(lines)
