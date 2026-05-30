"""Rhetoric analysis — figures of speech, metaphors, framing patterns, hedging."""

import re
from dataclasses import dataclass, field

# Figures of speech / idioms → intent mapping
# Each entry: (regex, intent_tag, description)
IDIOMS: list[tuple[str, str, str]] = [
    (r"\bboil the ocean\b", "over_scope", "attempting too much at once"),
    (r"\bput a pin in\b", "defer", "postponing a topic"),
    (r"\blow.hanging fruit\b", "easy_win", "quick, easy task"),
    (r"\bmove the needle\b", "significant_progress", "meaningful change"),
    (r"\bheavy lift\b", "difficult", "hard or resource-intensive task"),
    (r"\blift\b.*\bfinger\b", "minimal_effort", "doing very little"),
    (r"\bdrill down\b", "deep_investigation", "examine in detail"),
    (r"\bcircle back\b", "return_to_topic", "discuss later"),
    (r"\btouch base\b", "check_in", "brief status update"),
    (r"\bon the same page\b", "alignment", "shared understanding"),
    (r"\bbandwidth\b", "capacity", "available resources or attention"),
    (r"\bcutting edge\b", "innovation", "most advanced"),
    (r"\bdeep dive\b", "thorough_examination", "comprehensive analysis"),
    (r"\bgame plan\b", "strategy", "planned approach"),
    (r"\bget our hands dirty\b", "hands_on_work", "direct involvement"),
    (r"\bgranular\b", "detail_level", "level of detail"),
    (r"\bhigh.level\b", "summary", "overview or strategic view"),
    (r"\bleverage\b", "utilize", "use as advantage"),
    (r"\boptics\b", "perception", "how things appear"),
    (r"\brainstorm\b", "idea_generation", "generate ideas freely"),
    (r"\bramp up\b", "scale", "increase capacity or speed"),
    (r"\bscalable\b", "growth_capable", "able to grow"),
    (r"\bsynergy\b", "collaboration_benefit", "combined effect greater than sum"),
    (r"\bthink outside the box\b", "creative_thinking", "unconventional approach"),
    (r"\bvalue add\b", "additional_benefit", "extra value provided"),
    (r"\bvet\b", "review", "examine or evaluate"),
    (r"\bwarehouse\b", "store", "store for later use"),
    (r"\bwater under the bridge\b", "past_irrelevant", "no longer important"),
    (r"\bwin.win\b", "mutual_benefit", "beneficial for all parties"),
    (r"\bduck soup\b", "easy", "very easy task"),
    (r"\ba piece of cake\b", "easy", "very easy task"),
    (r"\bhit the ground running\b", "immediate_productivity", "start effectively"),
    (r"\bballpark\b", "rough_estimate", "approximate figure"),
    (r"\bhard stop\b", "deadline", "firm end time"),
    (r"\bkeep me in the loop\b", "inform", "keep updated"),
    (r"\btable that\b", "defer", "set aside for later"),
    (r"\bopen the kimono\b", "full_disclosure", "reveal all information"),
    (r"\bskeletons in the closet\b", "hidden_issues", "undisclosed problems"),
    (r"\blowest hanging fruit\b", "easy_win", "easiest task to complete"),
]

# Hedging language — signals uncertainty, reduces commitment
HEDGES: list[str] = [
    "maybe", "perhaps", "possibly", "probably", "might", "could",
    "kind of", "sort of", "a bit", "a little", "somewhat",
    "i think", "i believe", "i guess", "i assume", "i suppose",
    "it might be", "it could be", "it seems", "it appears",
    "generally", "mostly", "usually", "typically", "often",
    "in my opinion", "from my perspective", "as far as i know",
    "if possible", "if you can", "when you get a chance",
    "no rush", "whenever", "sometime", "eventually",
    "ideally", "preferably", "optionally",
]

# Emphatic / urgency language — signals priority
EMPHATICS: list[str] = [
    "must", "absolutely", "critical", "urgent", "asap", "immediately",
    "essential", "mandatory", "required", "necessary", "vital",
    "imperative", "non.negotiable", "at all costs", "top priority",
    "do or die", "make or break", "deadline", "due by",
    "no matter what", "by any means", "under no circumstances",
]

# Repetitive framing patterns — indicates user communication style
FRAMING_PATTERNS: list[str] = [
    r"i want (you|this) to",
    r"we need to",
    r"can you (please )?",
    r"could you (please )?",
    r"would you (please )?",
    r"please (make|create|write|build|implement|add|fix|help|do)",
    r"i need (you|this|a|the)",
    r"it would be great if",
    r"i.d like (you|to)",
    r"your task is to?",
    r"your job is to?",
    r"the goal is to?",
    r"the objective is to?",
    r"i.m looking for",
    r"help me (with|to|understand|build|create|find|fix)",
]

# Metaphor domain tags — extends VOCABULARY_SCOPE concept
# Maps words commonly used metaphorically in tech contexts
METAPHOR_SOURCE_DOMAINS: dict[str, str] = {
    # Physical space metaphors
    "surface": "physical_space",
    "anchor": "physical_space",
    "bridge": "physical_space",
    "path": "physical_space",
    "roadmap": "physical_space",
    "landscape": "physical_space",
    "terrain": "physical_space",
    "footprint": "physical_space",
    "layer": "physical_space",
    "depth": "physical_space",
    "scope": "physical_space",
    "boundary": "physical_space",
    "edge": "physical_space",
    "core": "physical_space",
    "hub": "physical_space",
    "spoke": "physical_space",
    # Construction/building metaphors
    "build": "construction",
    "foundation": "construction",
    "framework": "construction",
    "scaffold": "construction",
    "pillar": "construction",
    "architecture": "construction",
    "infrastructure": "construction",
    "blueprint": "construction",
    # Journey/motion metaphors
    "journey": "journey",
    "milestone": "journey",
    "trajectory": "journey",
    "momentum": "journey",
    "pipeline": "journey",
    "bottleneck": "journey",
    "throughput": "journey",
    # Container/containment metaphors
    "envelope": "container",
    "capsule": "container",
    "silo": "container",
    "bucket": "container",
    "pool": "container",
    "sandbox": "container",
    # Health/body metaphors
    "health": "health",
    "symptom": "health",
    "diagnosis": "health",
    "remedy": "health",
    "pain point": "health",
    "friction": "health",
    # Warfare/competition metaphors
    "target": "warfare",
    "campaign": "warfare",
    "strategy": "warfare",
    "tactic": "warfare",
    "retreat": "warfare",
    "kill": "warfare",
    # Nature/organic metaphors
    "ecosystem": "nature",
    "growth": "nature",
    "seed": "nature",
    "garden": "nature",
    "weed": "nature",
    "prune": "nature",
    "bloom": "nature",
    # Machine/mechanism metaphors
    "engine": "machine",
    "gear": "machine",
    "lever": "machine",
    "pivot": "machine",
    "cog": "machine",
    "flywheel": "machine",
    # Financial metaphors
    "leverage": "finance",
    "equity": "finance",
    "capital": "finance",
    "currency": "finance",
    "investment": "finance",
    "dividend": "finance",
    "burn": "finance",
    # Container/ship metaphors
    "flag": "nautical",
    "navigate": "nautical",
    "course": "nautical",
    "helm": "nautical",
    "rudder": "nautical",
    "sail": "nautical",
}


@dataclass
class RhetoricResult:
    text: str
    idioms: list[dict[str, str]] = field(default_factory=list)
    hedges: list[str] = field(default_factory=list)
    emphatics: list[str] = field(default_factory=list)
    framing_hits: list[dict[str, int]] = field(default_factory=list)
    metaphors: list[dict[str, str]] = field(default_factory=list)
    repetitive_framing: list[str] = field(default_factory=list)
    intent_signals: dict[str, float] = field(default_factory=dict)

    @property
    def hedge_score(self) -> float:
        """Proportion of hedging signals to total word count."""
        return min(len(self.hedges) * 0.3, 1.0)

    @property
    def urgency_score(self) -> float:
        """Proportion of emphatic signals to total word count."""
        return min(len(self.emphatics) * 0.3, 1.0)

    @property
    def metaphor_density(self) -> float:
        """Density of metaphorical language."""
        return min(len(self.metaphors) * 0.1, 1.0)

    @property
    def idiom_weight(self) -> float:
        """Weight of idiomatic language (each idiom = intent signal)."""
        return min(len(self.idioms) * 0.2, 1.0)

    @property
    def rhetoric_penalty(self) -> float:
        """Combined penalty for rhetorical patterns (0-2.0)."""
        return min(
            self.hedge_score + self.urgency_score * 0.5
            + self.metaphor_density * 0.3 + self.idiom_weight,
            2.0
        )

    @property
    def rhetoric_indicators(self) -> list[str]:
        indicators = []
        if self.idioms:
            intents = list(set(i["intent"] for i in self.idioms))
            indicators.append(f"idioms detected: {', '.join(intents)}")
        if self.hedges and len(self.hedges) >= 2:
            indicators.append(f"hedging language ({len(self.hedges)} signals)")
        if self.emphatics and len(self.emphatics) >= 2:
            indicators.append(f"emphatic language ({len(self.emphatics)} signals)")
        if self.metaphors and len(self.metaphors) >= 3:
            indicators.append(f"metaphor density: {len(self.metaphors)} terms")
        if self.repetitive_framing:
            patterns = ", ".join(self.repetitive_framing[:3])
            indicators.append(f"repetitive framing: {patterns}")
        return indicators


def analyze_rhetoric(text: str) -> RhetoricResult:
    """Analyze rhetorical patterns, figures of speech, and framing in text."""
    result = RhetoricResult(text=text)
    lower = text.lower()

    # --- Idiom detection ---
    seen_intents = set()
    for pattern, intent, desc in IDIOMS:
        if re.search(pattern, lower):
            if intent not in seen_intents:
                seen_intents.add(intent)
                result.idioms.append({
                    "intent": intent,
                    "description": desc,
                    "pattern": pattern,
                })

    # --- Hedging language ---
    seen_hedges = set()
    for hedge in HEDGES:
        escaped = re.escape(hedge)
        if re.search(r"\b" + escaped + r"\b", lower):
            if hedge not in seen_hedges:
                seen_hedges.add(hedge)
                result.hedges.append(hedge)

    # --- Emphatic/urgency language ---
    seen_emp = set()
    for emph in EMPHATICS:
        escaped = re.escape(emph)
        if re.search(r"\b" + escaped + r"\b", lower):
            if emph not in seen_emp:
                seen_emp.add(emph)
                result.emphatics.append(emph)

    # --- Framing pattern detection ---
    framing_counts: dict[str, int] = {}
    for pattern in FRAMING_PATTERNS:
        matches = re.findall(pattern, lower)
        if matches:
            framing_counts[pattern] = len(matches)
    result.framing_hits = [{"pattern": p, "count": c} for p, c in framing_counts.items()]

    # --- Repetitive framing (same pattern used 3+ times) ---
    for item in result.framing_hits:
        if item["count"] >= 3:
            result.repetitive_framing.append(f"{item['pattern']} x{item['count']}")

    # --- Metaphor detection ---
    for word, domain in METAPHOR_SOURCE_DOMAINS.items():
        escaped = re.escape(word)
        if re.search(r"\b" + escaped + r"\b", lower):
            result.metaphors.append({"term": word, "source_domain": domain})

    # --- Intent signals (combine idiom intents + framing) ---
    for idiom in result.idioms:
        intent = idiom["intent"]
        result.intent_signals[intent] = result.intent_signals.get(intent, 0) + 1.0
    for item in result.framing_hits:
        # Framing intent heuristics
        if "urgent" in item["pattern"] or "need" in item["pattern"] or "must" in item["pattern"]:
            result.intent_signals["urgency"] = result.intent_signals.get("urgency", 0) + item["count"] * 0.5
        if "please" in item["pattern"] or "i'd like" in item["pattern"]:
            result.intent_signals["politeness"] = result.intent_signals.get("politeness", 0) + item["count"] * 0.3

    return result


def render_rhetoric_report(r: RhetoricResult) -> str:
    sep = "=" * 56
    lines = [sep]
    lines.append("  Rhetoric analysis")
    lines.append(sep)
    lines.append("")
    if r.idioms:
        lines.append(f"  Idioms ({len(r.idioms)}):")
        for i in r.idioms:
            lines.append(f"    {i['intent']} — {i['description']}")
    if r.hedges:
        lines.append(f"  Hedging: {', '.join(r.hedges[:5])}")
    if r.emphatics:
        lines.append(f"  Emphasis: {', '.join(r.emphatics[:5])}")
    if r.metaphors:
        domains = {m["source_domain"] for m in r.metaphors}
        lines.append(f"  Metaphor source domains: {', '.join(domains)}")
    if r.repetitive_framing:
        lines.append(f"  Repetitive framing: {'; '.join(r.repetitive_framing)}")
    if r.intent_signals:
        signals = sorted(r.intent_signals.items(), key=lambda x: -x[1])
        lines.append(f"  Intent signals: {', '.join(f'{k}({v:.1f})' for k, v in signals[:5])}")
    if not any([r.idioms, r.hedges, r.emphatics, r.metaphors, r.repetitive_framing]):
        lines.append("  No significant rhetorical patterns detected.")
    lines.append(sep)
    return "\n".join(lines)
