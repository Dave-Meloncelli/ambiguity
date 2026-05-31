from unittest.mock import patch
from pathlib import Path

from ambiguity.profile import Profile
from ambiguity.parser import parse
from ambiguity.scoring import AmbiguityScore
from ambiguity.containers import VERB_TAXONOMY, KNOWN_ACRONYMS, KEYWORD_MAP


def _test_path(tmp_path: Path) -> Path:
    return tmp_path / "profile.json"


def test_profile_defaults(tmp_path):
    tp = _test_path(tmp_path)
    with patch("ambiguity.profile.PROFILE_PATH", tp):
        with patch("ambiguity.profile.PROFILE_DIR", tp.parent):
            p = Profile()
    assert p.entries == []
    assert p.dismissed == {}
    assert p.score_baseline == 5.0
    assert p.threshold == 4.0


def test_profile_dismiss(tmp_path):
    tp = _test_path(tmp_path)
    with patch("ambiguity.profile.PROFILE_PATH", tp):
        with patch("ambiguity.profile.PROFILE_DIR", tp.parent):
            p = Profile()
    p.dismiss("no_terminal_punctuation")
    assert p.dismissed["no_terminal_punctuation"] == 1
    p.dismiss("no_terminal_punctuation")
    assert p.dismissed["no_terminal_punctuation"] == 2


def test_profile_suppressed_flags(tmp_path):
    tp = _test_path(tmp_path)
    with patch("ambiguity.profile.PROFILE_PATH", tp):
        with patch("ambiguity.profile.PROFILE_DIR", tp.parent):
            p = Profile()
    assert p.suppressed_flags() == set()
    p.dismiss("test_flag")
    p.dismiss("test_flag")
    assert "test_flag" not in p.suppressed_flags()
    p.dismiss("test_flag")
    assert "test_flag" in p.suppressed_flags()


def test_profile_adjusted_threshold(tmp_path):
    tp = _test_path(tmp_path)
    with patch("ambiguity.profile.PROFILE_PATH", tp):
        with patch("ambiguity.profile.PROFILE_DIR", tp.parent):
            p = Profile()
    p.threshold = 1.0
    assert p.adjusted_threshold() == 2.0
    p.threshold = 9.0
    assert p.adjusted_threshold() == 8.0


def test_profile_recalibrate_not_enough_entries(tmp_path):
    tp = _test_path(tmp_path)
    with patch("ambiguity.profile.PROFILE_PATH", tp):
        with patch("ambiguity.profile.PROFILE_DIR", tp.parent):
            p = Profile()
    assert p.score_baseline == 5.0
    for i in range(5):
        result = parse(f"test prompt {i}")
        score = AmbiguityScore(result)
        p.record(result, score, "advisory")
    assert p.score_baseline == 5.0


def test_profile_recalibrate_with_entries(tmp_path):
    tp = _test_path(tmp_path)
    with patch("ambiguity.profile.PROFILE_PATH", tp):
        with patch("ambiguity.profile.PROFILE_DIR", tp.parent):
            p = Profile()
    for i in range(15):
        result = parse("test")
        score = AmbiguityScore(result)
        p.record(result, score, "test")
    assert p.score_baseline != 5.0
    assert p.score_std is not None


def test_profile_learn_verb(tmp_path):
    tp = _test_path(tmp_path)
    with patch("ambiguity.profile.PROFILE_PATH", tp):
        with patch("ambiguity.profile.PROFILE_DIR", tp.parent):
            p = Profile()
    p.learn_verb("customize", containers=["code_generation"], specificity=0.7)
    assert "customize" in VERB_TAXONOMY
    assert VERB_TAXONOMY["customize"]["specificity"] == 0.7


def test_profile_learn_acronym(tmp_path):
    tp = _test_path(tmp_path)
    with patch("ambiguity.profile.PROFILE_PATH", tp):
        with patch("ambiguity.profile.PROFILE_DIR", tp.parent):
            p = Profile()
    p.learn_acronym("XYZ", "X Y Zebra")
    assert KNOWN_ACRONYMS.get("XYZ") == "X Y Zebra"


def test_profile_learn_keyword(tmp_path):
    tp = _test_path(tmp_path)
    with patch("ambiguity.profile.PROFILE_PATH", tp):
        with patch("ambiguity.profile.PROFILE_DIR", tp.parent):
            p = Profile()
    p.learn_keyword("widget", ["code_generation"])
    assert "widget" in KEYWORD_MAP


def test_profile_reapply_learned_on_load(tmp_path):
    tp = _test_path(tmp_path)
    with patch("ambiguity.profile.PROFILE_PATH", tp):
        with patch("ambiguity.profile.PROFILE_DIR", tp.parent):
            p1 = Profile()
    p1.learn_verb("glorp", containers=["code_generation"], specificity=0.9)
    p1.learn_acronym("GLP", "Glorp Language Processor")
    p1.learn_keyword("glorpify", ["code_generation"])

    with patch("ambiguity.profile.PROFILE_PATH", tp):
        with patch("ambiguity.profile.PROFILE_DIR", tp.parent):
            p2 = Profile()
    p2._load()
    assert "glorp" in VERB_TAXONOMY
    assert KNOWN_ACRONYMS.get("GLP") == "Glorp Language Processor"
    assert "glorpify" in KEYWORD_MAP


def test_profile_save_and_load(tmp_path):
    tp = _test_path(tmp_path)
    with patch("ambiguity.profile.PROFILE_PATH", tp):
        with patch("ambiguity.profile.PROFILE_DIR", tp.parent):
            p1 = Profile()
    p1.learn_verb("deploy", containers=["code_generation"], specificity=0.8)

    with patch("ambiguity.profile.PROFILE_PATH", tp):
        with patch("ambiguity.profile.PROFILE_DIR", tp.parent):
            p2 = Profile()
    p2._load()
    assert "deploy" in p2.learned_verbs
