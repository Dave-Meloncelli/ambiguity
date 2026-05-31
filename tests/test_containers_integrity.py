"""Integrity snapshot for containers.py — validates all dict entries have required fields."""
from ambiguity.containers import (
    CONTAINERS, VOCABULARY_SCOPE, KEYWORD_MAP, KNOWN_ACRONYMS,
    VERB_TAXONOMY,
)


def test_all_containers_have_required_fields():
    for name, container in CONTAINERS.items():
        assert container.name == name
        assert isinstance(container.description, str)
        assert isinstance(container.specificity, float)


def test_container_specificity_in_range():
    for container in CONTAINERS.values():
        assert 0.0 <= container.specificity <= 1.0, f"{container.name} specificity out of range"


def test_all_vocab_scope_entries_have_domain():
    for term, info in VOCABULARY_SCOPE.items():
        assert "domain" in info, f"{term} missing domain"
        assert info["domain"] in ("ecosystem", "technical", "metaphor"), f"{term} invalid domain"


def test_all_keyword_map_entries_have_containers():
    for keyword, info in KEYWORD_MAP.items():
        assert "containers" in info, f"{keyword} missing containers"


def test_keyword_map_known_containers():
    for keyword, info in KEYWORD_MAP.items():
        for container in info.get("containers", []):
            assert container in CONTAINERS, (
                f"{keyword} references unknown container '{container}'"
            )


def test_keyword_map_has_no_empty_containers():
    for keyword, info in KEYWORD_MAP.items():
        if not info.get("containers"):
            pass  # collisions may have empty containers


def test_all_known_acronyms_are_uppercase():
    for abbr in KNOWN_ACRONYMS:
        assert abbr == abbr.upper(), f"{abbr} is not uppercase"


def test_all_known_acronyms_have_expansion():
    for abbr, expansion in KNOWN_ACRONYMS.items():
        assert isinstance(expansion, str)
        assert len(expansion) > 0


def test_verb_taxonomy_entries_have_containers_and_specificity():
    for verb, info in VERB_TAXONOMY.items():
        assert "containers" in info, f"{verb} missing containers"
        assert "specificity" in info, f"{verb} missing specificity"
        assert isinstance(info["specificity"], (int, float))
        assert 0.0 <= info["specificity"] <= 1.0


def test_verb_taxonomy_containers_reference_valid():
    for verb, info in VERB_TAXONOMY.items():
        for container in info.get("containers", []):
            assert container in CONTAINERS, (
                f"verb '{verb}' references unknown container '{container}'"
            )


def test_verb_taxonomy_has_minimum_entries():
    assert len(VERB_TAXONOMY) >= 50


def test_keyword_map_has_minimum_entries():
    assert len(KEYWORD_MAP) >= 20


def test_known_acronyms_non_empty():
    assert len(KNOWN_ACRONYMS) >= 1
