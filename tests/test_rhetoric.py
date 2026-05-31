from ambiguity.rhetoric import (
    analyze_rhetoric, RhetoricResult, render_rhetoric_report,
    IDIOMS, HEDGES, EMPHATICS, METAPHOR_SOURCE_DOMAINS,
)


def test_rhetoric_result_defaults():
    r = RhetoricResult(text="test")
    assert r.text == "test"
    assert r.idioms == []
    assert r.hedges == []
    assert r.emphatics == []
    assert r.metaphors == []


def test_rhetoric_result_scores():
    r = RhetoricResult(text="test")
    assert r.hedge_score == 0.0
    assert r.urgency_score == 0.0
    assert r.metaphor_density == 0.0
    assert r.idiom_weight == 0.0
    assert r.rhetoric_penalty == 0.0


def test_no_rhetorical_patterns():
    r = analyze_rhetoric("sort a list of numbers")
    assert r.idioms == []
    assert r.hedges == []


def test_idiom_detection_boil_the_ocean():
    r = analyze_rhetoric("we should not boil the ocean")
    assert len(r.idioms) >= 1
    intents = [i["intent"] for i in r.idioms]
    assert "over_scope" in intents


def test_idiom_detection_circle_back():
    r = analyze_rhetoric("let me circle back on that")
    assert any(i["intent"] == "return_to_topic" for i in r.idioms)


def test_idiom_detection_deep_dive():
    r = analyze_rhetoric("we need to deep dive into this")
    assert any(i["intent"] == "thorough_examination" for i in r.idioms)


def test_idiom_detection_think_outside_box():
    r = analyze_rhetoric("think outside the box")
    assert any(i["intent"] == "creative_thinking" for i in r.idioms)


def test_hedge_detection():
    r = analyze_rhetoric("maybe we could possibly implement this")
    assert len(r.hedges) >= 2
    assert "maybe" in r.hedges
    assert "possibly" in r.hedges


def test_hedge_single():
    r = analyze_rhetoric("perhaps use python")
    assert "perhaps" in r.hedges


def test_emphatic_detection():
    r = analyze_rhetoric("this is urgent and critical asap")
    assert len(r.emphatics) >= 3


def test_framing_detection():
    r = analyze_rhetoric("can you please write a function")
    assert len(r.framing_hits) >= 1


def test_repetitive_framing():
    text = "we need to do this. we need to do that. we need to do another."
    r = analyze_rhetoric(text)
    assert len(r.repetitive_framing) >= 1


def test_metaphor_detection():
    r = analyze_rhetoric("we need to build a bridge across the landscape")
    metaphors = [m["term"] for m in r.metaphors]
    assert "bridge" in metaphors
    assert "landscape" in metaphors


def test_metaphor_source_domains():
    r = analyze_rhetoric("pipeline architecture ecosystem")
    domains = {m["source_domain"] for m in r.metaphors}
    assert "journey" in domains
    assert "construction" in domains
    assert "nature" in domains


def test_intent_signals_from_idioms():
    r = analyze_rhetoric("that is low hanging fruit")
    assert r.intent_signals.get("easy_win", 0) >= 1.0


def test_rhetoric_indicators_empty():
    r = RhetoricResult(text="hello")
    assert r.rhetoric_indicators == []


def test_rhetoric_indicators_idioms():
    r = RhetoricResult(text="", idioms=[{"intent": "easy_win", "pattern": "", "description": ""}])
    assert any("idioms" in i for i in r.rhetoric_indicators)


def test_rhetoric_indicators_hedging():
    r = RhetoricResult(text="", hedges=["maybe", "perhaps"])
    assert any("hedging" in i for i in r.rhetoric_indicators)


def test_rhetoric_indicators_emphatics():
    r = RhetoricResult(text="", emphatics=["urgent", "critical"])
    assert any("emphatic" in i for i in r.rhetoric_indicators)


def test_rhetoric_indicators_metaphor_density():
    r = RhetoricResult(text="", metaphors=[
        {"term": "a", "source_domain": "x"},
        {"term": "b", "source_domain": "y"},
        {"term": "c", "source_domain": "z"},
    ])
    assert any("metaphor" in i for i in r.rhetoric_indicators)


def test_rhetoric_penalty_capped():
    r = RhetoricResult(text="", idioms=[{"intent": "easy_win", "description": "", "pattern": ""}] * 10)
    assert r.rhetoric_penalty <= 2.0


def test_render_rhetoric_report():
    r = analyze_rhetoric("boil the ocean with urgent critical synergetic thinking")
    report = render_rhetoric_report(r)
    assert "Rhetoric analysis" in report


def test_render_rhetoric_report_empty():
    r = RhetoricResult(text="hello world")
    report = render_rhetoric_report(r)
    assert "No significant rhetorical patterns" in report


def test_all_idioms_have_three_elements():
    for entry in IDIOMS:
        assert len(entry) == 3
        assert isinstance(entry[0], str)
        assert isinstance(entry[1], str)
        assert isinstance(entry[2], str)


def test_all_hedges_are_strings():
    assert all(isinstance(h, str) for h in HEDGES)


def test_all_emphatics_are_strings():
    assert all(isinstance(e, str) for e in EMPHATICS)


def test_metaphor_source_domains_are_strings():
    for word, domain in METAPHOR_SOURCE_DOMAINS.items():
        assert isinstance(word, str)
        assert isinstance(domain, str)
        assert len(word) > 0
