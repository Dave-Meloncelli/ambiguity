"""Technical direction pipeline — ambiguity pre-flight → FRAM → challenge → probe."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .analyzer import Analysis

# Technical domain keywords mapped from ambiguity's keyword extraction
TECH_DOMAIN_KEYWORDS: dict[str, dict[str, str]] = {
    "database": {"domain": "data", "entity": "database"},
    "sql": {"domain": "data", "entity": "sql"},
    "nosql": {"domain": "data", "entity": "nosql"},
    "redis": {"domain": "data", "entity": "redis"},
    "postgres": {"domain": "data", "entity": "postgres"},
    "mongodb": {"domain": "data", "entity": "mongodb"},
    "csv": {"domain": "data", "entity": "csv"},
    "elasticsearch": {"domain": "data", "entity": "elasticsearch"},
    "meilisearch": {"domain": "data", "entity": "meilisearch"},
    "kafka": {"domain": "infrastructure", "entity": "message_queue"},
    "queue": {"domain": "infrastructure", "entity": "message_queue"},
    "api": {"domain": "architecture", "entity": "api"},
    "rest": {"domain": "architecture", "entity": "rest_api"},
    "graphql": {"domain": "architecture", "entity": "graphql"},
    "microservice": {"domain": "architecture", "entity": "microservice"},
    "lambda": {"domain": "architecture", "entity": "serverless"},
    "serverless": {"domain": "architecture", "entity": "serverless"},
    "docker": {"domain": "infrastructure", "entity": "containerization"},
    "kubernetes": {"domain": "infrastructure", "entity": "orchestration"},
    "k8s": {"domain": "infrastructure", "entity": "orchestration"},
    "aws": {"domain": "cloud", "entity": "aws"},
    "azure": {"domain": "cloud", "entity": "azure"},
    "gcp": {"domain": "cloud", "entity": "gcp"},
    "react": {"domain": "frontend", "entity": "react"},
    "vue": {"domain": "frontend", "entity": "vue"},
    "angular": {"domain": "frontend", "entity": "angular"},
    "python": {"domain": "language", "entity": "python"},
    "rust": {"domain": "language", "entity": "rust"},
    "go": {"domain": "language", "entity": "golang"},
    "golang": {"domain": "language", "entity": "golang"},
    "typescript": {"domain": "language", "entity": "typescript"},
    "javascript": {"domain": "language", "entity": "javascript"},
    "blockchain": {"domain": "architecture", "entity": "blockchain"},
    "ml": {"domain": "ai", "entity": "machine_learning"},
    "machine learning": {"domain": "ai", "entity": "machine_learning"},
    "llm": {"domain": "ai", "entity": "llm"},
    "rag": {"domain": "ai", "entity": "rag"},
}

# Scope-creep / overengineering signal words
OVERENGINEERING_SIGNALS: list[str] = [
    "enterprise", "scalable", "distributed", "fault tolerant",
    "event driven", "real time", "microservice", "platform",
    "unified", "comprehensive", "fully managed", "autonomous",
    "self healing", "zero trust",
]

# Solutions that often reinvent existing wheels
REINVENTION_PATTERNS: list[dict[str, str]] = [
    {"pattern": "workflow engine", "existing": "temporal / prefect / airflow"},
    {"pattern": "message queue", "existing": "redis / rabbitmq / kafka / nats"},
    {"pattern": "auth system", "existing": "auth0 / keycloak / firebase auth / oauth"},
    {"pattern": "feature flag", "existing": "launchdarkly / unleash / flagd"},
    {"pattern": "notification", "existing": "slack webhook / email / pushover / ntfy"},
    {"pattern": "file storage", "existing": "s3 / minio / local fs"},
    {"pattern": "rate limit", "existing": "redis + sliding window / envoy / nginx"},
    {"pattern": "caching layer", "existing": "redis / memcached / varnish / cdn"},
    {"pattern": "webrtc", "existing": "livekit / mediasoup / ion-sfu"},
    {"pattern": "object store", "existing": "minio / s3 / ceph"},
    {"pattern": "vector db", "existing": "chroma / qdrant / pinecone / weaviate"},
    {"pattern": "search engine", "existing": "elasticsearch / meilisearch / typesense / algolia"},
    {"pattern": "orchestrator", "existing": "temporal / aws step functions / prefect / dagster"},
    {"pattern": "reverse proxy", "existing": "nginx / caddy / traefik / envoy"},
]


@dataclass
class TechnicalEntity:
    name: str
    domain: str
    entity_type: str


@dataclass
class TechnicalAssessment:
    prompt: str
    ambiguity_analysis: Analysis
    technical_entities: list[TechnicalEntity] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)
    maturity_signal: str = "unknown"
    overengineering_signals: list[str] = field(default_factory=list)
    reinvention_signals: list[dict[str, str]] = field(default_factory=list)
    fram_target: str = ""
    challenge_targets: list[str] = field(default_factory=list)
    probe_target: str = ""

    def handoff_package(self) -> dict[str, Any]:
        return {
            "pipeline": "ambiguity → fram → challenge → probe",
            "version": "0.1.0",
            "prompt": self.prompt,
            "ambiguity": self._ambiguity_summary(),
            "technical_entities": [{"name": e.name, "domain": e.domain, "entity_type": e.entity_type}
                                   for e in self.technical_entities],
            "red_flags": self.red_flags,
            "maturity_signal": self.maturity_signal,
            "overengineering_signals": self.overengineering_signals,
            "reinvention_signals": self.reinvention_signals,
            "handoff": {
                "fram": {
                    "target": self.fram_target,
                    "reason": self._fram_reason(),
                    "mode": "analyse" if self.technical_entities else "triple-layer",
                },
                "challenge": {
                    "targets": self.challenge_targets,
                    "reason": self._challenge_reason(),
                },
                "probe": {
                    "target": self.probe_target,
                    "reason": self._probe_reason(),
                },
            },
        }

    def _ambiguity_summary(self) -> dict[str, Any]:
        s = self.ambiguity_analysis.score
        return {
            "score": round(s.total, 1),
            "band": s.band,
            "verbs": list(self.ambiguity_analysis.result.verbs),
            "constraints": self.ambiguity_analysis.result.constraints,
            "entropy_indicators": s.entropy_indicators,
            "container_overlap": s.container_overlap,
            "verb_specificity": round(s.verb_specificity, 2),
        }

    def _fram_reason(self) -> str:
        if self.technical_entities:
            entities = ", ".join(e.name for e in self.technical_entities[:3])
            return f"Evaluate technical fitness of: {entities}"
        if self.reinvention_signals:
            return f"Stress-test proposed approach against existing solutions ({self.reinvention_signals[0].get('existing', '')})"
        return "Triple-layer analysis of proposed technical direction"

    def _challenge_reason(self) -> str:
        if self.overengineering_signals:
            return f"Illuminate assumptions behind: {', '.join(self.overengineering_signals[:3])}"
        if self.red_flags:
            return f"Challenge red flags: {'; '.join(self.red_flags[:3])}"
        return "Interrogate architectural decisions — 'why this and not that?'"

    def _probe_reason(self) -> str:
        if self.technical_entities and len(self.technical_entities) > 0:
            return f"Probe existing surfaces in codebase related to: {self.technical_entities[0].domain}"
        return "Deep-dive into codebase for existing surfaces that address this domain"


def assess(prompt: str) -> TechnicalAssessment:
    analysis = Analysis(prompt)
    result = analysis.result
    score = analysis.score

    entities: list[TechnicalEntity] = []
    red_flags: list[str] = []

    text_lower = prompt.lower()

    # Normalize hyphens to spaces for pattern matching
    text_normalized = text_lower.replace("-", " ")

    # Extract technical entities from keyword hits + direct scanning
    def _resolve_keyword(kw: str) -> tuple[str, dict[str, str]] | None:
        if kw in TECH_DOMAIN_KEYWORDS:
            return kw, TECH_DOMAIN_KEYWORDS[kw]
        if kw.endswith("s") and len(kw) > 3:
            singular = kw[:-1]
            if singular in TECH_DOMAIN_KEYWORDS:
                return singular, TECH_DOMAIN_KEYWORDS[singular]
        return None

    found_entities: dict[str, TechnicalEntity] = {}
    for kw in result.keywords:
        resolved = _resolve_keyword(kw)
        if resolved is not None:
            entity_key, info = resolved
            if entity_key not in found_entities:
                found_entities[entity_key] = TechnicalEntity(
                    name=entity_key, domain=info["domain"], entity_type=info["entity"],
                )
    for word in text_normalized.split():
        word_clean = word.strip(".,;:!?")
        # Try exact match first
        if word_clean in TECH_DOMAIN_KEYWORDS and word_clean not in found_entities:
            info = TECH_DOMAIN_KEYWORDS[word_clean]
            found_entities[word_clean] = TechnicalEntity(
                name=word_clean, domain=info["domain"], entity_type=info["entity"],
            )
            continue
        # Try singular form for common plurals
        if word_clean.endswith("s") and len(word_clean) > 3:
            singular = word_clean[:-1]
            if singular in TECH_DOMAIN_KEYWORDS and singular not in found_entities:
                info = TECH_DOMAIN_KEYWORDS[singular]
                found_entities[singular] = TechnicalEntity(
                    name=singular, domain=info["domain"], entity_type=info["entity"],
                )
    entities = list(found_entities.values())

    # Overengineering signal detection (use hyphen-normalized text)
    overengineering = [s for s in OVERENGINEERING_SIGNALS if s in text_normalized]

    # Reinvention pattern detection (use hyphen-normalized text)
    reinvention = [p for p in REINVENTION_PATTERNS if p["pattern"] in text_normalized]

    # Red flag: vague technical context
    if not entities and score.total > 5.0:
        red_flags.append("no specific technical entities detected; direction is vague")

    # Red flag: overengineering + vague verbs
    if overengineering and score.verb_specificity < 0.5:
        red_flags.append(f"overengineering signals ({', '.join(overengineering)}) with vague verbs — likely scope creep")

    # Red flag: reinvention
    if reinvention and result.verbs:
        existing_list = [r["existing"] for r in reinvention]
        red_flags.append(f"consider existing solutions instead of rebuilding: {'; '.join(existing_list)}")

    # Red flag: contradiction (multi-clause with competing goals)
    if analysis.chunking and analysis.chunking.has_contradictions:
        red_flags.append("competing constraints detected — architecture may be trying to satisfy opposing goals")

    # Red flag: missing constraints for technical request
    if entities and not result.constraints:
        red_flags.append("technical entities specified but no constraints (language, performance, budget) — risk of unbounded scope")

    # Maturity signal
    if score.total <= 4.0 and entities:
        maturity_signal = "well-specified"
    elif score.total > 6.0 and overengineering:
        maturity_signal = "warning — vague or over-scoped"
    elif reinvention:
        maturity_signal = "warning — reinvention risk"
    else:
        maturity_signal = "review needed"

    # Build handoff targets
    entity_names = [e.name for e in entities]
    fram_target = ", ".join(entity_names[:3]) if entity_names else prompt[:60]
    challenge_targets = []
    if overengineering:
        challenge_targets.append("design: validate overengineering signals")
    if reinvention:
        challenge_targets.append("design: validate reinvention risk against existing systems")
    if not entities:
        challenge_targets.append("design: illuminate missing technical context")
    challenge_targets.append("design: interrogate architectural decisions")
    probe_target = entity_names[0] if entity_names else "general"

    return TechnicalAssessment(
        prompt=prompt,
        ambiguity_analysis=analysis,
        technical_entities=entities,
        red_flags=red_flags,
        maturity_signal=maturity_signal,
        overengineering_signals=overengineering,
        reinvention_signals=reinvention,
        fram_target=fram_target,
        challenge_targets=challenge_targets,
        probe_target=probe_target,
    )


def render_technical_report(assessment: TechnicalAssessment) -> str:
    lines: list[str] = []
    sep = "=" * 62

    lines.append(sep)
    lines.append("  ambiguity technical — pipeline assessment")
    lines.append(sep)
    lines.append(f"  Score: {assessment.ambiguity_analysis.score.total:.1f}/10 ({assessment.ambiguity_analysis.score.band})")
    lines.append(f"  Maturity: {assessment.maturity_signal}")
    lines.append("")

    if assessment.technical_entities:
        lines.append("  [Technical Entities]")
        for e in assessment.technical_entities:
            lines.append(f"    {e.name:20s} {e.domain:15s} {e.entity_type}")
        lines.append("")

    if assessment.overengineering_signals:
        lines.append("  [!] Overengineering signals:")
        for s in assessment.overengineering_signals:
            lines.append(f"      - {s}")
        lines.append("")

    if assessment.reinvention_signals:
        lines.append("  [!] Reinvention risk — consider existing:")
        for r in assessment.reinvention_signals:
            lines.append(f"      - {r['pattern']:20s} → {r['existing']}")
        lines.append("")

    if assessment.red_flags:
        lines.append("  [Red Flags]")
        for flag in assessment.red_flags:
            lines.append(f"    !  {flag}")
        lines.append("")

    lines.append("  [Pipeline Handoff]")
    lines.append(f"    FRAM -> {assessment.fram_target}")
    for target in assessment.challenge_targets:
        lines.append(f"    challenge -> {target}")
    lines.append(f"    probe -> {assessment.probe_target}")
    lines.append("")

    lines.append(sep)
    return "\n".join(lines)


def render_technical_json(assessment: TechnicalAssessment) -> dict[str, Any]:
    return assessment.handoff_package()


# Self-test corpus — known prompts with expected detection outcomes
SELF_TEST_CASES: list[dict[str, Any]] = [
    {
        "prompt": "build a distributed enterprise-grade microservice platform with event-driven architecture",
        "expect_entities": ["microservice"],
        "expect_overengineering": ["enterprise", "distributed", "microservice", "platform"],
        "expect_reinvention": [],
        "expect_red_flags": True,
    },
    {
        "prompt": "we need a workflow engine for our data pipeline",
        "expect_entities": [],
        "expect_overengineering": [],
        "expect_reinvention": ["workflow engine"],
        "expect_red_flags": True,
    },
    {
        "prompt": "implement merge sort on a linked list in python without recursion",
        "expect_entities": ["python"],
        "expect_overengineering": [],
        "expect_reinvention": [],
        "expect_red_flags": False,
    },
    {
        "prompt": "add a real-time notification system with websockets",
        "expect_entities": [],
        "expect_overengineering": ["real time"],
        "expect_reinvention": [],
        "expect_red_flags": True,
    },
    {
        "prompt": "build an event-driven fault-tolerant self-healing platform",
        "expect_entities": [],
        "expect_overengineering": ["event driven", "fault tolerant", "self healing", "platform"],
        "expect_reinvention": [],
        "expect_red_flags": True,
    },
    {
        "prompt": "write a python script that reads a csv file and sums a column",
        "expect_entities": ["python", "csv"],
        "expect_overengineering": [],
        "expect_reinvention": [],
        "expect_red_flags": True,  # constraints missing — correct advisory
    },
    {
        "prompt": "deploy microservices with kubernetes and postgres",
        "expect_entities": ["microservice", "kubernetes", "postgres"],
        "expect_overengineering": ["microservice"],
        "expect_reinvention": [],
        "expect_red_flags": True,
    },
]


@dataclass
class SelfTestResult:
    prompt: str
    entities_found: list[str]
    entities_missed: list[str]
    overengineering_found: list[str]
    overengineering_missed: list[str]
    reinvention_found: list[dict[str, str]]
    reinvention_missed: list[dict[str, str]]
    red_flag_expected: bool
    red_flag_actual: bool
    maturity_actual: str
    pass_: bool


def self_test() -> list[SelfTestResult]:
    results: list[SelfTestResult] = []
    for case in SELF_TEST_CASES:
        a = assess(case["prompt"])
        entity_names = [e.name for e in a.technical_entities]
        over_found = list(a.overengineering_signals)
        rein_found = list(a.reinvention_signals)
        red_flag_actual = len(a.red_flags) > 0

        entities_missed = [e for e in case["expect_entities"] if e not in entity_names]
        over_missed = [s for s in case["expect_overengineering"] if s not in over_found]
        rein_patterns_missed = [
            p for p in case["expect_reinvention"]
            if p not in [r["pattern"] for r in rein_found]
        ]
        expected_rein_entries = [
            {"pattern": p, "existing": next(
                (r["existing"] for r in REINVENTION_PATTERNS if r["pattern"] == p), ""
            )}
            for p in case["expect_reinvention"]
        ]

        passed = (
            len(entities_missed) == 0
            and len(over_missed) == 0
            and len(rein_patterns_missed) == 0
            and red_flag_actual == case["expect_red_flags"]
        )

        results.append(SelfTestResult(
            prompt=case["prompt"],
            entities_found=entity_names,
            entities_missed=entities_missed,
            overengineering_found=over_found,
            overengineering_missed=over_missed,
            reinvention_found=rein_found,
            reinvention_missed=expected_rein_entries if rein_patterns_missed else [],
            red_flag_expected=case["expect_red_flags"],
            red_flag_actual=red_flag_actual,
            maturity_actual=a.maturity_signal,
            pass_=passed,
        ))
    return results


def render_self_test(results: list[SelfTestResult], prev_results: list[SelfTestResult] | None = None) -> str:
    lines: list[str] = []
    sep = "=" * 62
    lines.append(sep)
    lines.append("  ambiguity technical — self-test")
    if prev_results:
        lines.append("  (delta mode: current vs previous run)")
    lines.append(sep)
    lines.append("")

    total = len(results)

    for i, r in enumerate(results):
        status = "PASS" if r.pass_ else "FAIL"
        lines.append(f"  [{status}] [{i+1}/{total}] {r.prompt[:55]}")
        if not r.pass_:
            if r.entities_missed:
                lines.append(f"         entities missed: {', '.join(r.entities_missed)}")
            if r.overengineering_missed:
                lines.append(f"         overengineering missed: {', '.join(r.overengineering_missed)}")
            if r.reinvention_missed:
                for rm in r.reinvention_missed:
                    lines.append(f"         reinvention missed: {rm['pattern']} -> {rm['existing']}")
            if r.red_flag_expected != r.red_flag_actual:
                lines.append(f"         red flag expected={r.red_flag_expected} actual={r.red_flag_actual}")

        # Delta indicator (handle growing/ shrinking test suites)
        if prev_results:
            if i < len(prev_results):
                prev = prev_results[i]
                if prev.pass_ and not r.pass_:
                    lines.append("         <<< REGRESSION from previous run")
                elif not prev.pass_ and r.pass_:
                    lines.append("         >>> NEW PASS from previous run")
            else:
                lines.append("         [new test case]")

    lines.append("")
    lines.append(sep)
    count_pass = sum(1 for r in results if r.pass_)
    pct = count_pass / total * 100 if total > 0 else 0
    lines.append(f"  {count_pass}/{total} passed ({pct:.0f}%)")
    if prev_results:
        prev_pass = sum(1 for r in prev_results if r.pass_)
        delta = count_pass - prev_pass
        new_cases = total - len(prev_results)
        if new_cases != 0:
            lines.append(f"  ({new_cases:+d} test case{'s' if abs(new_cases) != 1 else ''} from baseline)")
        if delta != 0:
            lines.append(f"  Delta: {delta:+d} passing from baseline")
        else:
            lines.append("  No change in passing count from baseline")
    lines.append(sep)
    return "\n".join(lines)


__all__ = [
    "assess",
    "TechnicalAssessment",
    "TechnicalEntity",
    "render_technical_report",
    "render_technical_json",
    "TECH_DOMAIN_KEYWORDS",
    "OVERENGINEERING_SIGNALS",
    "REINVENTION_PATTERNS",
    "self_test",
    "SelfTestResult",
    "render_self_test",
    "SELF_TEST_CASES",
]
