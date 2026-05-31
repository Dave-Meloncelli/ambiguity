from ambiguity.embeddings import (
    EmbeddingAnalysis, analyze_keyword_coverage,
    detect_semantic_gaps, cluster_keywords_by_meaning,
    DOMAIN_KEYWORDS,
)


def test_embedding_analysis_defaults():
    ea = EmbeddingAnalysis(has_embeddings=False)
    assert ea.has_embeddings is False
    assert ea.semantic_gaps == []
    assert ea.keyword_clusters == {}
    assert ea.model_name == "not_loaded"
    assert ea.dimension == 0


def test_analyze_keyword_coverage_noop_without_sentence_transformers():
    result = analyze_keyword_coverage(["python"], ["constraint"])
    assert result.has_embeddings is False
    assert result.semantic_gaps == []


def test_detect_semantic_gaps_noop_without_model():
    assert detect_semantic_gaps(["python"], ["constraint"]) == []


def test_cluster_keywords_noop_without_model():
    assert cluster_keywords_by_meaning(["python", "java"]) == {}


def test_cluster_keywords_empty():
    assert cluster_keywords_by_meaning([]) == {}


def test_cluster_keywords_single_without_model():
    # Without sentence-transformers, returns empty dict
    assert cluster_keywords_by_meaning(["python"]) == {}


def test_domain_keywords_list_non_empty():
    assert len(DOMAIN_KEYWORDS) > 0
    assert "constraint" in DOMAIN_KEYWORDS
    assert "security" in DOMAIN_KEYWORDS
