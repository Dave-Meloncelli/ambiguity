"""Optional embedding-based semantic analysis — graceful fallback when sentence-transformers not installed."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field

_HAS_SENTENCE_TRANSFORMERS = False
_model = None

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    _HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    np = None  # type: ignore
    SentenceTransformer = None  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingAnalysis:
    has_embeddings: bool
    semantic_gaps: list[str] = field(default_factory=list)
    keyword_clusters: dict[str, list[str]] = field(default_factory=dict)
    model_name: str = "not_loaded"
    dimension: int = 0


_MODEL_INSTANCE = None
_MODEL_NAME = "not_loaded"
_DIMENSION = 0
_LOAD_ATTEMPTED = False
_LOAD_LOCK = __import__("threading").Lock()


def _load_model(timeout: float = 15.0) -> bool:
    global _MODEL_INSTANCE, _MODEL_NAME, _DIMENSION, _LOAD_ATTEMPTED
    if _MODEL_INSTANCE is not None:
        return True
    if not _HAS_SENTENCE_TRANSFORMERS:
        return False
    if _LOAD_ATTEMPTED:
        return False
    if not os.environ.get("AMBIGUITY_EMBEDDINGS"):
        return False
    if _LOAD_ATTEMPTED:
        return False

    import concurrent.futures

    _LOAD_LOCK.acquire()
    if _MODEL_INSTANCE is not None:
        _LOAD_LOCK.release()
        return True
    if _LOAD_ATTEMPTED:
        _LOAD_LOCK.release()
        return False

    def _try_load():
        for name, dim in [
            ("all-MiniLM-L6-v2", 384),
            ("all-mpnet-base-v2", 768),
        ]:
            try:
                m = SentenceTransformer(name)
                _MODEL_INSTANCE = m
                _MODEL_NAME = name
                _DIMENSION = dim
                return True
            except Exception:
                continue
        return False

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(_try_load)
        try:
            result = fut.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            logger.warning("embedding model loading timed out after %ss", timeout)
            result = False

    _LOAD_ATTEMPTED = True
    _LOAD_LOCK.release()
    return result


def detect_semantic_gaps(
    existing_keywords: list[str],
    domain_keywords: list[str],
    threshold: float = 0.3,
) -> list[str]:
    """Detect domain keywords that lack semantic coverage in the prompt keywords."""
    if not _load_model():
        return []
    if not existing_keywords or not domain_keywords:
        return []

    assert _MODEL_INSTANCE is not None
    if np is None:
        return []

    all_texts = existing_keywords + domain_keywords
    embeddings = _MODEL_INSTANCE.encode(all_texts, convert_to_numpy=True, normalize_embeddings=True)
    if len(embeddings) < len(all_texts):
        return []

    existing_embs = embeddings[: len(existing_keywords)]
    domain_embs = embeddings[len(existing_keywords) :]

    gaps = []
    for i, dk in enumerate(domain_keywords):
        if i >= len(domain_embs):
            continue
        sims = np.dot(domain_embs[i], existing_embs.T)
        max_sim = float(np.max(sims)) if sims.size > 0 else 0.0
        if max_sim < threshold:
            gaps.append(dk)
    return gaps


def cluster_keywords_by_meaning(
    keywords: list[str],
    similarity_threshold: float = 0.7,
) -> dict[str, list[str]]:
    """Cluster keywords by semantic similarity (greedy single-pass)."""
    if not _load_model():
        return {}
    if len(keywords) < 2:
        return {k: [k] for k in keywords} if keywords else {}

    assert _MODEL_INSTANCE is not None
    if np is None:
        return {}

    embeddings = _MODEL_INSTANCE.encode(keywords, convert_to_numpy=True, normalize_embeddings=True)
    clusters: dict[str, list[str]] = {}
    assigned: set[str] = set()

    for i, kw in enumerate(keywords):
        if kw in assigned:
            continue
        cluster = [kw]
        assigned.add(kw)
        for j, other in enumerate(keywords):
            if i != j and other not in assigned:
                sim = float(np.dot(embeddings[i], embeddings[j]))
                if sim >= similarity_threshold:
                    cluster.append(other)
                    assigned.add(other)
        clusters[kw] = cluster
    return clusters


def analyze_keyword_coverage(
    existing_keywords: list[str],
    domain_keywords: list[str],
    gap_threshold: float = 0.3,
    cluster_threshold: float = 0.7,
) -> EmbeddingAnalysis:
    """Full keyword coverage analysis: gaps + clusters."""
    if not _HAS_SENTENCE_TRANSFORMERS or not _load_model():
        return EmbeddingAnalysis(has_embeddings=False)
    gaps = detect_semantic_gaps(existing_keywords, domain_keywords, gap_threshold)
    clusters = cluster_keywords_by_meaning(existing_keywords, cluster_threshold)
    return EmbeddingAnalysis(
        has_embeddings=True,
        semantic_gaps=gaps,
        keyword_clusters=clusters,
        model_name=_MODEL_NAME,
        dimension=_DIMENSION,
    )


DOMAIN_KEYWORDS: list[str] = [
    "constraint",
    "exact",
    "requirement",
    "negation",
    "dependency",
    "input",
    "output",
    "specification",
    "format",
    "type",
    "boundary",
    "limit",
    "deadline",
    "scope",
    "condition",
    "rule",
    "policy",
    "standard",
    "quality",
    "performance",
    "security",
    "reliability",
    "accuracy",
    "precision",
    "completeness",
]
