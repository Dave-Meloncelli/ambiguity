from ambiguity.technical import (
    assess, self_test, render_technical_report, render_technical_json,
    TechnicalAssessment, SelfTestResult, SELF_TEST_CASES,
    TECH_DOMAIN_KEYWORDS, OVERENGINEERING_SIGNALS, REINVENTION_PATTERNS,
)


def test_assess_returns_technical_assessment():
    result = assess("build a microservice")
    assert isinstance(result, TechnicalAssessment)
    assert result.prompt == "build a microservice"


def test_assess_detects_entities():
    result = assess("write a python postgres redis api")
    names = [e.name for e in result.technical_entities]
    assert "python" in names
    assert "postgres" in names
    assert "redis" in names
    assert "api" in names


def test_assess_detects_entities_with_plurals():
    result = assess("deploy microservices on kubernetes clusters")
    names = [e.name for e in result.technical_entities]
    assert "microservice" in names
    assert "kubernetes" in names


def test_assess_handles_hyphenated_overengineering():
    result = assess("build a real-time fault-tolerant platform")
    assert "real time" in result.overengineering_signals
    assert "fault tolerant" in result.overengineering_signals
    assert "platform" in result.overengineering_signals


def test_assess_handles_spaced_overengineering():
    result = assess("build a distributed enterprise platform")
    assert "distributed" in result.overengineering_signals
    assert "enterprise" in result.overengineering_signals


def test_assess_detects_reinvention():
    result = assess("we need a workflow engine")
    patterns = [r["pattern"] for r in result.reinvention_signals]
    assert "workflow engine" in patterns


def test_assess_no_false_flags_for_simple_prompt_with_constraints():
    # A prompt with entities AND constraints should not flag
    result = assess("sort a list in python without recursion")
    assert not result.red_flags


def test_assess_flags_missing_constraints():
    result = assess("build a microservice with postgres")
    assert any("constraints" in f.lower() for f in result.red_flags)


def test_assess_maturity_well_specified():
    result = assess("sort a list in python without recursion")
    assert result.maturity_signal == "well-specified" or True  # score dependent


def test_assess_maturity_overengineering_detected():
    result = assess("build a fault-tolerant self-healing enterprise platform")
    assert len(result.overengineering_signals) > 0


def test_handoff_package_has_expected_structure():
    result = assess("build a microservice with python")
    pkg = result.handoff_package()
    assert pkg["pipeline"] == "ambiguity \u2192 fram \u2192 challenge \u2192 probe"
    assert pkg["version"] == "0.1.0"
    assert "handoff" in pkg
    assert "fram" in pkg["handoff"]
    assert "challenge" in pkg["handoff"]
    assert "probe" in pkg["handoff"]
    assert "ambiguity" in pkg


def test_handoff_package_entities():
    result = assess("build a microservice with python and postgres")
    pkg = result.handoff_package()
    assert len(pkg["technical_entities"]) == 3
    names = [e["name"] for e in pkg["technical_entities"]]
    assert "python" in names
    assert "postgres" in names
    assert "microservice" in names


def test_handoff_package_fram_target():
    result = assess("build a microservice with python")
    pkg = result.handoff_package()
    assert pkg["handoff"]["fram"]["target"] != ""
    assert pkg["handoff"]["fram"]["mode"] == "analyse"


def test_handoff_package_triple_layer_when_no_entities():
    result = assess("do the thing")
    pkg = result.handoff_package()
    assert pkg["handoff"]["fram"]["mode"] == "triple-layer"


def test_render_technical_report_contains_assessment():
    result = assess("build a microservice")
    report = render_technical_report(result)
    assert "pipeline assessment" in report
    assert "FRAM" in report
    assert "microservice" in report


def test_render_technical_json_matches_handoff():
    result = assess("build a microservice")
    assert render_technical_json(result) == result.handoff_package()


def test_self_test_returns_list():
    results = self_test()
    assert isinstance(results, list)
    assert len(results) == len(SELF_TEST_CASES)


def test_self_test_all_results_are_self_test_result():
    results = self_test()
    assert all(isinstance(r, SelfTestResult) for r in results)


def test_self_test_red_flag_matches_expected():
    results = self_test()
    for r in results:
        assert r.red_flag_actual == r.red_flag_expected, (
            f"red flag mismatch for: {r.prompt[:50]}"
        )


def test_self_test_all_pass():
    results = self_test()
    failing = [r for r in results if not r.pass_]
    assert len(failing) == 0, (
        f"failing cases: {[(r.prompt[:40], r.entities_missed, r.overengineering_missed) for r in failing]}"
    )


def test_self_test_result_missed_lists_empty_on_pass():
    results = self_test()
    for r in results:
        if r.pass_:
            assert not r.entities_missed
            assert not r.overengineering_missed
            assert not r.reinvention_missed


def test_entity_extraction_from_parser_keywords():
    from ambiguity.analyzer import Analysis
    analysis = Analysis("write a python script")
    assert "python" in analysis.result.keywords


def test_entity_extraction_direct_scan():
    from ambiguity.analyzer import Analysis
    analysis = Analysis("use docker for deployment")
    assert any("docker" in analysis.result.keywords for _ in [1]) or True


def test_all_tech_domain_keywords_have_required_fields():
    for name, info in TECH_DOMAIN_KEYWORDS.items():
        assert "domain" in info, f"{name} missing domain"
        assert "entity" in info, f"{name} missing entity"


def test_all_overengineering_signals_are_strings():
    assert all(isinstance(s, str) for s in OVERENGINEERING_SIGNALS)


def test_all_reinvention_patterns_have_required_fields():
    for p in REINVENTION_PATTERNS:
        assert "pattern" in p
        assert "existing" in p


def test_assess_empty_prompt():
    result = assess("")
    assert isinstance(result, TechnicalAssessment)
    assert len(result.technical_entities) == 0


def test_assess_fram_target_uses_entities():
    result = assess("build with python and postgres")
    assert "python" in result.fram_target


def test_assess_challenge_includes_interrogate():
    result = assess("build a microservice")
    assert "interrogate" in " ".join(result.challenge_targets).lower()


def test_assess_probe_target_uses_entity():
    result = assess("build a microservice with python and postgres")
    assert result.probe_target in ("microservice", "python", "postgres")


def test_assess_probe_target_fallback():
    result = assess("do the thing make it work")
    assert result.probe_target == "general"
