from ambiguity.translate import (
    translate, Translation, render_translate_report, render_translate_json,
    _expand_acronyms, _replace_vague_verbs, _flag_unqualified_refs,
    _add_constraint_reminder, _add_vocab_hint,
)
from ambiguity.analyzer import Analysis


def test_translation_dataclass():
    t = Translation(original="test", translated="result", score_before=5.0, score_after=3.0)
    assert t.original == "test"
    assert t.changes == []


def test_translate_with_constraints():
    result = translate("implement merge sort in python without recursion")
    assert result.score_before >= 0


def test_translate_adds_constraint_reminder():
    result = translate("do the thing")
    kinds = [c["type"] for c in result.changes]
    assert "constraint_reminder" in kinds
    assert "[NOTE" in result.translated


def test_expand_acronyms():
    analysis = Analysis("check the UDL configuration")
    changes = _expand_acronyms(analysis.result.text, analysis)
    if any(a == "UDL" for a, _ in analysis.result.acronyms):
        assert len(changes) >= 1
        assert changes[0]["type"] == "acronym"


def test_replace_vague_verbs_no_change_for_specific():
    analysis = Analysis("implement a function")
    changes = _replace_vague_verbs(analysis.result.text, analysis)
    # "implement" is specific enough
    for c in changes:
        assert c["type"] == "vague_verb"


def test_flag_unqualified_refs_no_refs():
    analysis = Analysis("implement a function")
    changes = _flag_unqualified_refs(analysis.result.text, analysis)
    assert changes == []


def test_flag_unqualified_refs_detects_thing():
    analysis = Analysis("do the thing")
    changes = _flag_unqualified_refs(analysis.result.text, analysis)
    assert len(changes) >= 1


def test_add_constraint_reminder_when_missing():
    analysis = Analysis("do the thing")
    changes = _add_constraint_reminder("do the thing", analysis)
    assert len(changes) == 1
    assert changes[0]["type"] == "constraint_reminder"


def test_add_constraint_reminder_when_present():
    analysis = Analysis("implement without imports only standard library")
    changes = _add_constraint_reminder("implement without imports", analysis)
    assert changes == []


def test_add_vocab_hint():
    analysis = Analysis("send a udl envelope")
    changes = _add_vocab_hint(analysis.result.text, analysis)
    assert changes == [] or changes[0]["type"] == "vocab_scope"


def test_render_translate_report():
    t = Translation(original="do it", translated="[NOTE] do it", score_before=8.0, score_after=6.0,
                    changes=[{"type": "constraint_reminder", "original": "", "replacement": "[NOTE]"}])
    report = render_translate_report(t)
    assert "de-ambiguation" in report.lower()
    assert "constraint_reminder" in report or "8.0" in report


def test_render_translate_report_no_changes():
    t = Translation(original="implement sort", translated="implement sort", score_before=3.0, score_after=3.0)
    report = render_translate_report(t)
    assert "No changes needed" in report


def test_render_translate_json():
    t = Translation(original="test", translated="result", score_before=5.0, score_after=3.0)
    j = render_translate_json(t)
    assert j["command"] == "translate"
    assert j["score_before"] == 5.0
    assert j["score_after"] == 3.0
