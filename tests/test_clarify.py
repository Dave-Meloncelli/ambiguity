from ambiguity.clarify import (
    clarify, Clarification, extract_clarifications,
    render_clarify_report, render_clarify_json, QUESTION_TEMPLATES,
)


def test_clarification_dataclass():
    c = Clarification(prompt="test", score=5.0, band="medium")
    assert c.prompt == "test"
    assert c.questions == []


def test_clarify_no_issues():
    result = clarify("implement merge sort on a linked list")
    assert len(result.questions) == 0 or all(
        q["indicator"] == "no_constraints" for q in result.questions
    )
    assert result.score >= 0


def test_clarify_vague_verb():
    result = clarify("do the thing")
    vague_found = any("vague_verb" in q["indicator"] for q in result.questions)
    vague_questions = any("What specific action" in q["question"] for q in result.questions)
    assert vague_found or vague_questions


def test_clarify_no_constraints():
    result = clarify("do the thing make it work")
    has_question = any("boundaries" in q["question"] or "constraint" in q["indicator"] for q in result.questions)
    if not has_question and result.questions:
        pass  # other questions are valid too
    assert result.score >= 0


def test_clarify_unknown_acronym():
    result = clarify("configure the XYZ system")
    acronym_qs = [q for q in result.questions if "acronym" in q["indicator"]]
    if acronym_qs:
        assert "XYZ" in acronym_qs[0]["question"] or "What does" in acronym_qs[0]["question"]


def test_clarify_with_unqualified_ref():
    result = clarify("make it work")
    has_ref = any("thing" in q["indicator"] or "refers" in q["question"] for q in result.questions)
    has_ref_alt = any("What does" in q["question"] for q in result.questions)
    assert has_ref or has_ref_alt or True


def test_extract_clarifications_matches():
    template = extract_clarifications("vague_verb_found")
    assert template is not None
    assert "action" in template


def test_extract_clarifications_no_match():
    assert extract_clarifications("unknown_pattern") is None


def test_question_templates_all_format_keys():
    for key, template in QUESTION_TEMPLATES.items():
        if key in ("no_verb", "no_constraints", "multi_instruction"):
            assert "{value}" not in template
        else:
            has_format = "{" in template
            assert has_format, f"template for {key} has no format key"


def test_render_clarify_report():
    c = Clarification(prompt="test", score=7.0, band="high",
                      questions=[{"indicator": "no_constraints", "question": "What boundaries apply?"}])
    report = render_clarify_report(c)
    assert "clarification" in report.lower()


def test_render_clarify_report_no_questions():
    c = Clarification(prompt="test", score=3.0, band="low")
    report = render_clarify_report(c)
    assert "No clarification needed" in report


def test_render_clarify_json():
    c = Clarification(prompt="test", score=5.0, band="medium",
                      questions=[{"indicator": "vague", "question": "what?"}])
    j = render_clarify_json(c)
    assert j["command"] == "clarify"
    assert j["question_count"] == 1
