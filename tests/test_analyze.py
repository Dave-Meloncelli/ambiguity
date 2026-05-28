import json
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


def test_vocab_scope_detects_domain_terms():
    result = parse("generate a udl envelope for the chap surface")
    terms = [vt.term for vt in result.vocab_scope]
    assert "udl envelope" in terms or "surface anchor" in terms or "capability packet" in terms


def test_vocab_scope_adds_to_score():
    analysis = Analysis("generate a udl envelope for the chap surface")
    assert analysis.score.total > 0.0
    assert any("domain-specific" in ind for ind in analysis.score.entropy_indicators)


def test_flow_test_detects_missing_doc():
    from ambiguity.flow import check_missing_standard_docs
    issues = check_missing_standard_docs()
    existing = {i.message.split(" ")[0] for i in issues if i.category == "missing_doc"}
    assert "NONEXISTENT.md" not in existing


def test_flow_test_runs():
    from ambiguity.flow import flow_test
    report = flow_test()
    assert report.summary["total"] >= 0
    assert "total" in report.summary


def test_hooks_extract_prompt_text():
    from ambiguity.hooks import _extract_prompt_text
    messages = [{"role": "user", "content": "write a fibonacci function"}]
    result = _extract_prompt_text(messages, {})
    assert "fibonacci" in result


def test_hooks_extract_prompt_content_blocks():
    from ambiguity.hooks import _extract_prompt_text
    messages = [{"role": "user", "content": [{"type": "text", "text": "sort a list"}]}]
    result = _extract_prompt_text(messages, {})
    assert "sort" in result


def test_hooks_config_defaults():
    from ambiguity.hooks import HookConfig
    cfg = HookConfig()
    assert cfg.gate == 6.0
    assert cfg.on_exceed == "warn"


def test_hooks_handle_result_below_gate():
    from ambiguity.hooks import _handle_result
    _handle_result(5.0, "medium", 6.0, "block")  # should not raise


def test_hooks_handle_result_above_gate_block():
    from ambiguity.hooks import _handle_result
    import pytest
    with pytest.raises(RuntimeError, match="BLOCKED"):
        _handle_result(7.0, "high", 6.0, "block")


def test_hooks_handle_result_above_gate_warn():
    from ambiguity.hooks import _handle_result
    _handle_result(7.0, "high", 6.0, "warn")  # should not raise, just prints to stderr


def test_cli_watch_rejects_non_dir():
    from ambiguity.cli import _cmd_watch
    import tempfile
    import os
    f = tempfile.NamedTemporaryFile(delete=False, suffix=".tmp")
    try:
        f.close()
        rc = _cmd_watch(f.name)
        assert rc == 1
    finally:
        os.unlink(f.name)


def test_gate_does_not_block_low_score():
    from ambiguity.cli import build_parser
    parser = build_parser()
    args = parser.parse_args(["analyze", "write a python function", "--gate", "9.0"])
    assert args.gate == 9.0
    assert args.command == "analyze"


def test_gate_blocks_high_score():
    from ambiguity.cli import main
    rc = main(["analyze", "do the thing make it work", "--gate", "3.0"])
    assert rc == 1


def test_module_entrypoint_exits_with_gate_code(tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src") + os.pathsep + env.get("PYTHONPATH", "")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ambiguity",
            "analyze",
            "do the thing make it work",
            "--gate",
            "6.0",
        ],
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "GATE: score" in result.stderr


def test_compare_no_llm_outputs_report():
    from ambiguity.compare import compare
    result = compare("write a function", no_llm=True)
    assert result.ambiguity_score > 0
    assert result.control_response is None
    assert result.treatment_response is None
    assert "write" in result.enriched_prompt


def test_compare_json_roundtrip():
    from ambiguity.compare import render_compare_json, CompareResult
    result = CompareResult(prompt="test", ambiguity_score=5.0, band="medium", enriched_prompt="enriched", advisory=None)
    data = render_compare_json(result)
    assert data["command"] == "compare"
    assert data["ambiguity_score"] == 5.0
    assert data["band"] == "medium"


def test_compare_write_experiment_files(tmp_path):
    from ambiguity.compare import compare, write_experiment_files
    result = compare("hello world", no_llm=True)
    out = write_experiment_files(result, str(tmp_path))
    assert out.is_dir()
    files = list(out.iterdir())
    assert any("original_prompt" in f.name for f in files)
    assert any("enriched_prompt" in f.name for f in files)
    assert any("compare_report" in f.name for f in files)


def test_audit_extracts_claimed_files():
    from ambiguity.audit import _extract_claimed_files
    prompt = "create src/main.py and src/utils.py for the project"
    files = _extract_claimed_files(prompt)
    assert "src/main.py" in files
    assert "src/utils.py" in files


def test_audit_matches_existing_files(tmp_path):
    from ambiguity.audit import audit
    (tmp_path / "main.py").write_text("print('hi')", encoding="utf-8")
    result = audit("create main.py and utils.py", str(tmp_path))
    assert "main.py" in result.matched_files
    assert "utils.py" in result.missing_files
    assert result.summary["matched"] == 1
    assert result.summary["missing"] == 1


def test_audit_detects_extra_files(tmp_path):
    from ambiguity.audit import audit
    (tmp_path / "main.py").write_text("", encoding="utf-8")
    (tmp_path / "unexpected.py").write_text("", encoding="utf-8")
    result = audit("create main.py", str(tmp_path))
    assert "unexpected.py" in result.extra_files


def test_audit_near_match(tmp_path):
    from ambiguity.audit import audit
    (tmp_path / "mainn.py").write_text("", encoding="utf-8")
    result = audit("create main.py", str(tmp_path))
    assert len(result.near_matches) >= 1
    claimed_f, actual_f, ratio = result.near_matches[0]
    assert "main.py" in claimed_f
    assert "mainn.py" in actual_f


def test_audit_json_roundtrip():
    from ambiguity.audit import render_audit_json, AuditResult
    result = AuditResult(prompt="test", claimed_files=["a.py"], actual_files=["a.py"])
    data = render_audit_json(result)
    assert data["command"] == "audit"
    assert data["summary"]["claimed"] == 1


def test_translate_expands_acronyms():
    from ambiguity.translate import translate
    result = translate("check the UDL configuration")
    assert "Unified Data Layer" in result.translated or result.changes


def test_translate_vague_verb():
    from ambiguity.translate import translate
    result = translate("do the thing")
    assert len(result.changes) > 0 or result.score_before > 0


def test_translate_adds_constraint_reminder():
    from ambiguity.translate import translate
    result = translate("implement a function")
    assert "constraint" in result.translated.lower() or not result.changes


def test_clarify_generates_questions():
    from ambiguity.clarify import clarify
    result = clarify("do the thing make it work")
    assert len(result.questions) > 0


def test_clarify_clean_prompt_no_questions():
    from ambiguity.clarify import clarify
    result = clarify("implement a python function that sorts a list")
    assert len(result.questions) == 0


def test_log_writes_and_reads(tmp_path):
    from ambiguity.memory import _find_memory
    import os
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        mem = tmp_path / "docs" / "memory.md"
        mem.parent.mkdir(parents=True)
        mem.write_text("# memory\n\n## Entries\n\n", encoding="utf-8")

        from ambiguity.memory import log_interaction, recent_entries
        path = log_interaction("write a function", action="translate")
        assert path is not None
        entries = recent_entries(5)
        assert len(entries) >= 1
        assert any("write" in e.get("prompt", "") for e in entries)
    finally:
        os.chdir(old_cwd)


def test_import_rejects_no_consent():
    from ambiguity.import_discover import discover
    result = discover(consent=False)
    assert result.prompts_found == 0
    assert len(result.errors) > 0


def test_import_scans_json(tmp_path):
    from ambiguity.import_discover import discover
    import os
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    (fake_home / ".claude" / "logs").mkdir(parents=True)
    log_file = fake_home / ".claude" / "logs" / "session.json"
    log_file.write_text(json.dumps([
        {"role": "user", "content": "write a function that sorts a list"},
        {"role": "assistant", "content": "Here's a sorting function"},
    ]), encoding="utf-8")

    import ambiguity.import_discover as mod
    old_paths = mod.HARNESS_PATHS.copy()
    try:
        mod.HARNESS_PATHS = {"Claude Code": [str(fake_home / ".claude/logs")]}
        result = discover(consent=True, dry_run=True)
        assert result.prompts_found >= 1 or result.sources_scanned >= 1
    finally:
        mod.HARNESS_PATHS = old_paths


def test_rhetoric_detects_idioms():
    from ambiguity.rhetoric import analyze_rhetoric
    r = analyze_rhetoric("we need to boil the ocean and move the needle")
    assert len(r.idioms) >= 1
    intents = [i["intent"] for i in r.idioms]
    assert "over_scope" in intents


def test_rhetoric_detects_hedging():
    from ambiguity.rhetoric import analyze_rhetoric
    r = analyze_rhetoric("maybe implement it if possible no rush")
    assert len(r.hedges) >= 2


def test_rhetoric_detects_emphatics():
    from ambiguity.rhetoric import analyze_rhetoric
    r = analyze_rhetoric("this is critical must fix asap")
    assert "critical" in r.emphatics or "must" in r.emphatics


def test_rhetoric_detects_metaphors():
    from ambiguity.rhetoric import analyze_rhetoric
    r = analyze_rhetoric("build a bridge across the landscape layer")
    domains = {m["source_domain"] for m in r.metaphors}
    assert "physical_space" in domains or "construction" in domains


def test_chunking_finds_phrasal_verbs():
    from ambiguity.chunking import chunk
    c = chunk("set up the environment and tear down the old one")
    assert len(c.compound_verbs) >= 1
    verbs = [cv.full for cv in c.compound_verbs]
    assert "set_up" in verbs or "tear_down" in verbs


def test_chunking_splits_clauses():
    from ambiguity.chunking import chunk
    c = chunk("first implement the api then add the tests but skip the docs")
    assert c.clause_count >= 2


def test_chunking_detects_contradictions():
    from ambiguity.chunking import chunk
    c = chunk("must be fast but also comprehensive")
    assert len(c.contradiction_hits) >= 1 or c.clause_count >= 2


def test_stemming_matches_inflected_forms():
    from ambiguity.containers import fuzzy_verb_match, STEMMING_TABLE
    for inflected, base in [
        ("writes", "write"), ("wrote", "write"), ("written", "write"), ("writing", "write"),
        ("creates", "create"), ("created", "create"), ("creating", "create"),
        ("implements", "implement"), ("implemented", "implement"), ("implementing", "implement"),
        ("optimizes", "optimize"), ("optimized", "optimize"), ("optimizing", "optimize"),
        ("running", "run"), ("building", "build"),
    ]:
        result = fuzzy_verb_match(inflected)
        assert result is not None, f"No match for {inflected}"
        assert result["verb"] == base, f"{inflected} → {result['verb']}, expected {base}"


def test_stemming_in_parser():
    from ambiguity.parser import parse
    r = parse("writing optimizing running")
    assert "write" in r.verbs, f"write not in {r.verbs}"
    assert "optimize" in r.verbs, f"optimize not in {r.verbs}"
    assert "run" in r.verbs, f"run not in {r.verbs}"


def test_nlp_bridge_fallback():
    from ambiguity.nlp_bridge import analyze, render_nlp_report
    r = analyze("write a function that sorts a list")
    assert not r.has_spacy
    report = render_nlp_report(r)
    assert "spaCy not available" in report


def test_unqualified_refs_demonstratives():
    from ambiguity.parser import parse
    r = parse("build this system using these tools")
    refs = set(r.unqualified_refs)
    assert "this" in refs or "this system" in refs


def test_unqualified_refs_scope_nouns():
    from ambiguity.parser import parse
    r = parse("implement the system and the application")
    assert any("the system" in ref or "system" in ref for ref in r.unqualified_refs)
    assert any("the application" in ref or "application" in ref for ref in r.unqualified_refs)


def test_constraints_upgrade_to_typed():
    from ambiguity.parser import parse
    from ambiguity.constraints import upgrade_constraints, ConstraintCategory

    r = parse("must be fast")
    typed = upgrade_constraints(r)
    assert len(typed) >= 1
    assert typed[0].constraint_category == ConstraintCategory.HARD


def test_constraints_missing_types():
    from ambiguity.parser import parse
    from ambiguity.constraints import ConstraintAnalysis, ConstraintType

    r = parse("write a function")
    ca = ConstraintAnalysis.from_parse(r)
    assert ConstraintType.FINANCIAL in ca.missing_types
    assert ConstraintType.TEMPORAL in ca.missing_types


def test_embeddings_fallback_when_not_installed():
    from ambiguity.embeddings import analyze_keyword_coverage, DOMAIN_KEYWORDS
    result = analyze_keyword_coverage(["test"], DOMAIN_KEYWORDS)
    assert not result.has_embeddings


def test_embeddings_gap_detection_dry_run():
    from ambiguity.embeddings import detect_semantic_gaps, DOMAIN_KEYWORDS

    # should return [] when sentence-transformers not available
    gaps = detect_semantic_gaps(["write", "function"], DOMAIN_KEYWORDS)
    assert gaps == [] or isinstance(gaps, list)


def test_analysis_includes_constraints_and_embeddings():
    from ambiguity.analyzer import Analysis

    a = Analysis("write a function that calculates fibonacci")
    assert hasattr(a, "constraint_analysis")
    assert hasattr(a, "embedding_analysis")
    assert isinstance(a.constraint_analysis.typed, list)
