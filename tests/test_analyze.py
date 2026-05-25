from ambiguity.parser import parse
from ambiguity.scoring import AmbiguityScore
from ambiguity.analyzer import Analysis


def test_parse_extracts_verbs():
    result = parse("write a function that sorts a list")
    assert "write" in result.verbs
    assert "sort" in result.verbs or "sorts" in result.verbs


def test_parse_extracts_keywords():
    result = parse("write a python function")
    assert "python" in result.keywords or "function" in result.keywords


def test_parse_detects_acronyms():
    result = parse("check the UDL configuration")
    assert any(a == "UDL" for a, _ in result.acronyms)


def test_parse_detects_constraints():
    result = parse("implement without imports only use standard library")
    assert "negation" in result.constraints or "exact" in result.constraints or "dependency" in result.constraints


def test_vague_prompt_scores_high():
    analysis = Analysis("do the thing make it work")
    assert analysis.score.total > 6.0


def test_precise_prompt_scores_lower():
    analysis = Analysis("implement merge sort on a linked list in python without recursion, handle empty list")
    assert analysis.score.total < 8.0


def test_terminal_report_renders():
    analysis = Analysis("write a function")
    report = analysis.terminal_report()
    assert "ambiguity" in report.lower()


def test_json_report_has_version():
    analysis = Analysis("write a function")
    jr = analysis.json_report()
    assert jr["version"] == "0.1.0"


def test_minimal_envelope_exists():
    analysis = Analysis("write a function")
    env = analysis.minimal_envelope
    assert env["_envelope"]["format"] == "ambiguity_analysis_v1"
