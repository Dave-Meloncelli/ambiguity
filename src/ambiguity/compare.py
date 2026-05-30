"""Compare experiment — runs a prompt with and without ambiguity pre-flight, compares outputs."""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .analyzer import Analysis
from .advisory import advisory as get_advisory


@dataclass
class CompareResult:
    prompt: str
    ambiguity_score: float
    band: str
    advisory: str | None
    enriched_prompt: str
    control_response: str | None = None
    treatment_response: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


def build_enriched_prompt(prompt: str) -> str:
    analysis = Analysis(prompt)
    adv = get_advisory(analysis.result, analysis.score)
    score = analysis.score.total
    band = analysis.score.band
    indicators = analysis.score.entropy_indicators
    verbs = analysis.result.verbs
    constraints = analysis.result.constraints

    parts = ["## Ambiguity Pre-Flight Analysis\n"]
    parts.append(f"Score: {score:.1f}/10 ({band})")
    if adv:
        parts.append(f"Advisory: {adv}")
    if indicators:
        parts.append("\nIssues to address:\n" + "\n".join(f"- {i}" for i in indicators))
    if verbs:
        parts.append(f"\nDetected verbs: {', '.join(verbs)}")
    if constraints:
        parts.append(f"Constraints: {', '.join(constraints)}")
    parts.append(f"\n---\n\n## Original Request\n\n{prompt}")
    parts.append("\n\n## Response Requirements\n")
    parts.append("Please address all issues flagged above in your response.")
    return "\n".join(parts)


def _call_llm(prompt: str, provider: str | None = None) -> str | None:
    provider = provider or os.environ.get("AMBIGUITY_LLM_PROVIDER", "")
    if provider.lower() in ("anthropic", "claude"):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            resp = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.content[0].text if resp.content else ""
        except Exception as e:
            return f"[LLM call failed: {e}]"
    elif provider.lower() in ("openai", "gpt"):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return None
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model="gpt-4o",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            return f"[LLM call failed: {e}]"
    return None


def _compare_responses(control: str, treatment: str) -> dict[str, Any]:
    control_len = len(control.split())
    treatment_len = len(treatment.split())
    metrics = {
        "control_word_count": control_len,
        "treatment_word_count": treatment_len,
        "length_ratio": round(treatment_len / max(control_len, 1), 2),
    }
    common_words = set(control.lower().split()) & set(treatment.lower().split())
    metrics["vocab_overlap_ratio"] = round(
        len(common_words) / max(len(set(treatment.lower().split())), 1), 2
    )
    return metrics


def compare(
    prompt: str,
    provider: str | None = None,
    no_llm: bool = False,
) -> CompareResult:
    analysis = Analysis(prompt)
    adv = get_advisory(analysis.result, analysis.score)
    enriched = build_enriched_prompt(prompt)

    result = CompareResult(
        prompt=prompt,
        ambiguity_score=analysis.score.total,
        band=analysis.score.band,
        advisory=adv,
        enriched_prompt=enriched,
    )

    if no_llm:
        return result

    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        result.error = "No API key found (set ANTHROPIC_API_KEY or OPENAI_API_KEY)"
        return result

    result.control_response = _call_llm(prompt, provider)
    result.treatment_response = _call_llm(enriched, provider)

    if result.control_response and result.treatment_response:
        result.metrics = _compare_responses(result.control_response, result.treatment_response)

    return result


def render_compare_report(result: CompareResult) -> str:
    width = 64
    lines = []
    lines.append(f"{'=' * width}")
    lines.append("  ambiguity compare — pre-flight experiment")
    lines.append(f"{'=' * width}")
    lines.append(f"  Score: {result.ambiguity_score:.1f}/10 ({result.band})")
    if result.advisory:
        lines.append(f"  Advisory: {result.advisory}")
    lines.append("")
    if result.error:
        lines.append(f"  [SKIP] {result.error}")
        lines.append("")
        lines.append("  To run the full experiment, set:")
        lines.append("    ANTHROPIC_API_KEY=sk-...  or  OPENAI_API_KEY=sk-...")
        lines.append("")
        lines.append("  Or use --no-llm to output prompt files for manual testing:")
        lines.append("    ambiguity compare \"your prompt\" --no-llm --output-dir ./experiment")
        lines.append(f"{'=' * width}")
        return "\n".join(lines)

    if result.control_response and result.treatment_response:
        lines.append("  Control (raw prompt):")
        for line in result.control_response.strip().splitlines()[:6]:
            lines.append(f"    | {line[:width-6]}")
        if len(result.control_response.splitlines()) > 6:
            lines.append(f"    | ... ({len(result.control_response.splitlines()) - 6} more lines)")
        lines.append("")
        lines.append("  Treatment (with ambiguity pre-flight):")
        for line in result.treatment_response.strip().splitlines()[:6]:
            lines.append(f"    | {line[:width-6]}")
        if len(result.treatment_response.splitlines()) > 6:
            lines.append(f"    | ... ({len(result.treatment_response.splitlines()) - 6} more lines)")
        lines.append("")
        if result.metrics:
            lines.append("  Metrics:")
            for k, v in result.metrics.items():
                lines.append(f"    {k}: {v}")
    lines.append(f"{'=' * width}")
    return "\n".join(lines)


def render_compare_json(result: CompareResult) -> dict[str, Any]:
    return {
        "command": "compare",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "prompt": result.prompt,
        "ambiguity_score": round(result.ambiguity_score, 1),
        "band": result.band,
        "advisory": result.advisory,
        "enriched_prompt": result.enriched_prompt,
        "control_response": result.control_response,
        "treatment_response": result.treatment_response,
        "metrics": result.metrics,
        "error": result.error,
    }


def write_experiment_files(result: CompareResult, output_dir: str) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (out / f"original_prompt_{stamp}.txt").write_text(result.prompt, encoding="utf-8")
    (out / f"enriched_prompt_{stamp}.txt").write_text(result.enriched_prompt, encoding="utf-8")
    if result.control_response:
        (out / f"control_response_{stamp}.txt").write_text(result.control_response, encoding="utf-8")
    if result.treatment_response:
        (out / f"treatment_response_{stamp}.txt").write_text(result.treatment_response, encoding="utf-8")
    report = render_compare_json(result)
    (out / f"compare_report_{stamp}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return out
