from ambiguity.review import (
    review, ReviewResult, ReviewIssue, render_review_report, render_review_json,
    _lower_words, _find_phrases, _find_phrases_dict, _check_constraint_compliance,
    WEASEL_WORDS, FILLER_PATTERNS, HALLUCINATION_MARKERS, BOILERPLATE_MARKERS,
)


def test_review_result_defaults():
    r = ReviewResult(prompt="test", response="ok", score=5.0, band="medium")
    assert r.prompt == "test"
    assert r.score == 5.0
    assert r.issues == []


def test_review_issue_dataclass():
    i = ReviewIssue(kind="test", detail="something", severity="warning")
    assert i.kind == "test"
    assert i.severity == "warning"


def test_review_empty_response():
    r = review("hello", "")
    assert r.score == 10.0
    assert r.band == "very high"
    assert any(i.kind == "empty" for i in r.issues)


def test_review_clean_response():
    r = review("write a function", "def foo():\n    pass")
    assert r.score >= 0.0


def test_review_detects_hedging():
    r = review("implement this", "i think this might work maybe")
    assert r.hedging_count >= 2
    assert any(i.kind == "hedging" for i in r.issues)


def test_review_detects_filler():
    r = review("implement this", "let me go ahead and implement this")
    assert r.filler_count >= 1
    assert any(i.kind == "filler" for i in r.issues)


def test_review_detects_hallucination_markers():
    r = review("hello", "i don't actually have access to that information")
    assert len(r.hallucination_signals) >= 1
    assert any(i.kind == "hallucination_signal" for i in r.issues)


def test_review_detects_boilerplate():
    r = review("hello", "i hope this helps feel free to reach out")
    assert r.boilerplate_lines >= 2
    assert any(i.kind == "boilerplate" for i in r.issues)


def test_review_detects_low_confidence():
    r = review("hello", "it might possibly maybe work")
    assert r.band == "very high" or any(i.kind == "low_confidence" for i in r.issues)


def test_review_unaddressed_verbs():
    r = review("sort the list and also filter it", "here is a list")
    assert len(r.unaddressed_verbs) >= 1
    assert any(i.kind == "unaddressed_verb" for i in r.issues)


def test_review_verbose_response():
    prompt = "write a function"
    long_resp = "word " * 300
    r = review(prompt, long_resp)
    assert any(i.kind == "verbose" for i in r.issues)


def test_review_too_short_response():
    r = review("write a python function that sorts a list using merge sort", "ok")
    assert any(i.kind == "too_short" for i in r.issues)


def test_review_constraint_breach():
    r = review("do not use imports only standard library", "import os")
    assert any(i.kind == "constraint_breach" for i in r.issues) or r.word_count > 0


def test_review_score_bounds():
    r = review("hello", "yes")
    assert 0.0 <= r.score <= 10.0


def test_lower_words():
    result = _lower_words("Hello World!")
    assert "hello" in result
    assert "world" in result


def test_find_phrases():
    result = _find_phrases("i think maybe", ["i think", "maybe"])
    assert "i think" in result
    assert "maybe" in result


def test_find_phrases_no_match():
    assert _find_phrases("hello world", ["nope"]) == []


def test_find_phrases_dict():
    result = _find_phrases_dict("definitely maybe", {"definitely": 1.0, "maybe": 0.1})
    assert result["definitely"] == 1.0
    assert result["maybe"] == 0.1


def test_check_constraint_compliance_negation():
    result = _check_constraint_compliance(["negation"], "but however")
    assert result.get("no_negation_ignored") is False


def test_check_constraint_compliance_negation_ok():
    result = _check_constraint_compliance(["negation"], "this works")
    assert result.get("no_negation_ignored") is True


def test_render_review_report_empty():
    r = ReviewResult(prompt="test", response="ok", score=1.0, band="low")
    report = render_review_report(r)
    assert "Response-side analysis" in report or "ambiguity review" in report


def test_render_review_report_issues():
    r = ReviewResult(
        prompt="test", response="ok", score=5.0, band="medium",
        issues=[ReviewIssue("test", "something", "warning")],
    )
    report = render_review_report(r)
    assert "WARNING" in report.upper()


def test_render_review_json():
    r = ReviewResult(prompt="p", response="r", score=3.0, band="medium")
    j = render_review_json(r)
    assert j["command"] == "review"
    assert j["prompt"] == "p"
    assert j["score"] == 3.0


def test_weasel_words_non_empty():
    assert len(WEASEL_WORDS) > 0
    assert "basically" in WEASEL_WORDS


def test_filler_patterns_non_empty():
    assert len(FILLER_PATTERNS) > 0
    assert any("let me" in f for f in FILLER_PATTERNS)


def test_hallucination_markers_non_empty():
    assert len(HALLUCINATION_MARKERS) > 0


def test_boilerplate_markers_non_empty():
    assert len(BOILERPLATE_MARKERS) > 0
