from ambiguity.chunking import (
    chunk, _split_clauses, _detect_compound_verbs, _detect_contradictions,
    _count_topic_shifts, _detect_verbs_in_clause, _detect_constraints_in_clause,
    ChunkResult, Clause, CompoundVerb, render_chunk_report,
)


def test_chunk_result_defaults():
    cr = ChunkResult(text="test")
    assert cr.text == "test"
    assert cr.clauses == []
    assert cr.compound_verbs == []
    assert cr.topic_shifts == 0
    assert cr.contradiction_hits == []


def test_chunk_result_properties():
    cr = ChunkResult(text="a b c", clauses=[Clause(text="a"), Clause(text="b")])
    assert cr.clause_count == 2
    assert cr.has_contradictions is False


def test_clause_dataclass():
    c = Clause(text="hello world", verbs=["write"], constraints=["exact"])
    assert c.text == "hello world"
    assert c.verbs == ["write"]
    assert c.has_negation is False
    assert c.has_hedging is False
    assert c.has_emphasis is False


def test_compound_verb_dataclass():
    cv = CompoundVerb(verb="set", particle="up", full="set_up", position=0)
    assert cv.verb == "set"
    assert cv.particle == "up"
    assert cv.full == "set_up"


def test_split_clauses_simple():
    result = _split_clauses("do this and do that")
    assert len(result) >= 2
    assert any("do this" in c for c in result)


def test_split_clauses_with_period():
    result = _split_clauses("First do this. Then do that.")
    assert len(result) >= 2


def test_split_clauses_empty():
    assert _split_clauses("") == []


def test_detect_compound_verbs():
    tokens = ["set", "up", "a", "server"]
    found = _detect_compound_verbs(tokens)
    assert len(found) == 1
    assert found[0].full == "set_up"


def test_detect_compound_verbs_no_match():
    tokens = ["run", "quickly"]
    assert _detect_compound_verbs(tokens) == []


def test_detect_compound_verbs_multiple():
    tokens = ["set", "up", "and", "tear", "down"]
    found = _detect_compound_verbs(tokens)
    assert len(found) == 2
    assert found[0].full == "set_up"
    assert found[1].full == "tear_down"


def test_detect_compound_verbs_last_token():
    tokens = ["break"]
    assert _detect_compound_verbs(tokens) == []


def test_detect_contradictions():
    clauses = [
        Clause(text="must do this but prioritize speed", has_emphasis=True),
        Clause(text="however avoid that", has_negation=True),
    ]
    hits = _detect_contradictions(clauses)
    assert len(hits) >= 1


def test_detect_contradictions_no_hit():
    clauses = [Clause(text="do this"), Clause(text="then that")]
    assert _detect_contradictions(clauses) == []


def test_count_topic_shifts():
    clauses = [Clause(text="first do this"), Clause(text="next do that")]
    assert _count_topic_shifts(clauses) >= 1


def test_detect_verbs_in_clause():
    found = _detect_verbs_in_clause("write a function", {"write", "read"})
    assert "write" in found
    assert "read" not in found


def test_detect_verbs_in_clause_partial():
    # word-boundary match only — "writing" does not match "write"
    found = _detect_verbs_in_clause("writing code", {"write"})
    assert found == []


def test_detect_constraints_in_clause_negation():
    cons = _detect_constraints_in_clause("do not use recursion")
    assert "negation" in cons


def test_detect_constraints_in_clause_requirement():
    cons = _detect_constraints_in_clause("must use python")
    assert "requirement" in cons


def test_detect_constraints_in_clause_exact():
    cons = _detect_constraints_in_clause("only standard library")
    assert "exact" in cons


def test_detect_constraints_in_clause_dependency():
    cons = _detect_constraints_in_clause("using flask")
    assert "dependency" in cons


def test_chunk_integration():
    result = chunk("set up a server and tear down the old one", {"set", "tear"})
    assert len(result.compound_verbs) >= 1
    assert result.clause_count >= 1


def test_chunk_clause_indicators_single():
    cr = ChunkResult(text="hello")
    assert cr.clause_indicators == []


def test_chunk_clause_indicators_many_clauses():
    clauses = [Clause(text=str(i)) for i in range(5)]
    cr = ChunkResult(text="", clauses=clauses)
    indicators = cr.clause_indicators
    assert any("clauses" in i for i in indicators)


def test_chunk_clause_indicators_contradiction():
    cr = ChunkResult(text="", contradiction_hits=["c1 vs c2"])
    indicators = cr.clause_indicators
    assert any("contradictory" in i for i in indicators)


def test_render_chunk_report_contains_clauses():
    cr = ChunkResult(text="test", clauses=[Clause(text="hello")])
    report = render_chunk_report(cr)
    assert "Chunk analysis" in report
    assert "Clauses" in report


def test_render_chunk_report_compound_verbs():
    cr = ChunkResult(text="", compound_verbs=[CompoundVerb("set", "up", "set_up")])
    report = render_chunk_report(cr)
    assert "set_up" in report
