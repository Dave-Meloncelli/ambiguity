from ambiguity.compare import (
    compare, CompareResult, build_enriched_prompt, _compare_responses,
    render_compare_report, render_compare_json,
)


def test_compare_result_dataclass():
    r = CompareResult(prompt="test", ambiguity_score=5.0, band="medium",
                      advisory=None, enriched_prompt="enriched test")
    assert r.prompt == "test"
    assert r.ambiguity_score == 5.0


def test_compare_no_llm():
    result = compare("write a function", no_llm=True)
    assert result.error is None or "API key" in result.error
    assert result.enriched_prompt is not None
    assert "Ambiguity Pre-Flight" in result.enriched_prompt


def test_compare_no_llm_high_score():
    result = compare("do the thing make it work quickly", no_llm=True)
    assert result.ambiguity_score >= 5.0 or result.advisory is not None


def test_build_enriched_prompt_contains_sections():
    enriched = build_enriched_prompt("write a function")
    assert "Ambiguity Pre-Flight" in enriched
    assert "Original Request" in enriched
    assert "Response Requirements" in enriched
    assert "write a function" in enriched


def test_build_enriched_prompt_highlights_verbs():
    enriched = build_enriched_prompt("write and sort")
    assert "write" in enriched


def test_compare_responses_metrics():
    metrics = _compare_responses(
        "hello world this is a test",
        "hello world this is an enriched test",
    )
    assert "control_word_count" in metrics
    assert "treatment_word_count" in metrics
    assert "length_ratio" in metrics
    assert "vocab_overlap_ratio" in metrics


def test_compare_responses_same():
    metrics = _compare_responses("same text", "same text")
    assert metrics["vocab_overlap_ratio"] >= 0.9


def test_compare_responses_different():
    metrics = _compare_responses("hello world", "completely different text here")
    assert metrics["vocab_overlap_ratio"] < 0.9


def test_render_compare_report():
    r = CompareResult(prompt="test", ambiguity_score=5.0, band="medium",
                      advisory="test advisory", enriched_prompt="enriched")
    report = render_compare_report(r)
    assert "pre-flight experiment" in report.lower()
    assert "test advisory" in report or "medium" in report


def test_render_compare_report_no_llm():
    r = CompareResult(prompt="test", ambiguity_score=5.0, band="medium",
                      advisory=None, enriched_prompt="enriched",
                      error="No API key found")
    report = render_compare_report(r)
    assert "API key" in report or "SKIP" in report


def test_render_compare_json():
    r = CompareResult(prompt="test", ambiguity_score=5.0, band="medium",
                      advisory=None, enriched_prompt="enriched")
    j = render_compare_json(r)
    assert j["command"] == "compare"
    assert j["ambiguity_score"] == 5.0
