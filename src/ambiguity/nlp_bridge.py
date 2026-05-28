"""Optional spaCy bridge — deep parsing with graceful fallback to regex."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# Try importing spaCy; everything below is guarded
_HAS_SPACY = False
_nlp = None

try:
    import spacy
    _HAS_SPACY = True
except ImportError:
    pass

# ── dependency parse result ──────────────────────────────────────────


@dataclass
class DependencyEdge:
    token: str
    pos: str
    dep: str
    head: str | None
    children: list[str] = field(default_factory=list)


@dataclass
class ParseTree:
    root: str | None
    tokens: list[DependencyEdge]


@dataclass
class NlpResult:
    has_spacy: bool
    pos_tags: dict[str, str] = field(default_factory=dict)
    dependency_tree: ParseTree | None = None
    named_entities: list[tuple[str, str]] = field(default_factory=list)
    subject_verb_pairs: list[tuple[str, str]] = field(default_factory=list)
    verb_objects: list[tuple[str, str]] = field(default_factory=list)


# ── attempt model load ───────────────────────────────────────────────

_MODEL_LOADED = False


def _load_model() -> bool:
    global _nlp, _MODEL_LOADED
    if _MODEL_LOADED:
        return True
    if not _HAS_SPACY:
        return False
    for model in ("en_core_web_sm", "en_core_web_md", "en_core_web_lg"):
        try:
            _nlp = spacy.load(model)
            _MODEL_LOADED = True
            return True
        except OSError:
            continue
    return False


# ── public analysis functions ────────────────────────────────────────


def analyze(text: str) -> NlpResult:
    """Deep-parse with spaCy if available; fallback returns has_spacy=False."""
    if not _load_model():
        return NlpResult(has_spacy=False)

    assert _nlp is not None
    doc = _nlp(text)

    # POS tags
    pos_tags: dict[str, str] = {}
    for tok in doc:
        if tok.is_alpha and not tok.is_stop:
            pos_tags[tok.text.lower()] = tok.pos_

    # Dependency tree
    tokens = [
        DependencyEdge(
            token=t.text,
            pos=t.pos_,
            dep=t.dep_,
            head=t.head.text if t.head != t else None,
            children=[c.text for c in t.children],
        )
        for t in doc
    ]

    root = next((t.text for t in doc if t.dep_ == "ROOT"), None)
    tree = ParseTree(root=root, tokens=tokens)

    # Named entities
    entities = [(ent.text, ent.label_) for ent in doc.ents]

    # Subject-verb pairs (nsubj / nsubjpass)
    sv_pairs: list[tuple[str, str]] = []
    vo_pairs: list[tuple[str, str]] = []
    for tok in doc:
        if tok.dep_ in ("nsubj", "nsubjpass") and tok.head.pos_ == "VERB":
            sv_pairs.append((tok.text.lower(), tok.head.lemma_.lower()))
        if tok.dep_ == "dobj" and tok.head.pos_ == "VERB":
            vo_pairs.append((tok.head.lemma_.lower(), tok.text.lower()))
        if tok.dep_ == "pobj" and tok.head.dep_ == "prep" and tok.head.head.pos_ == "VERB":
            vo_pairs.append((tok.head.head.lemma_.lower(), f"{tok.head.text} {tok.text}"))

    return NlpResult(
        has_spacy=True,
        pos_tags=pos_tags,
        dependency_tree=tree,
        named_entities=entities,
        subject_verb_pairs=sv_pairs,
        verb_objects=vo_pairs,
    )


def detect_semantic_ambiguity(result: NlpResult) -> list[str]:
    """Detect ambiguous constructions from dependency parse (spaCy only)."""
    if not result.has_spacy or not result.dependency_tree:
        return []
    warnings: list[str] = []

    # Missing subjects on verbs
    verb_tokens = {
        t.token for t in result.dependency_tree.tokens
        if t.pos == "VERB" and t.dep != "ROOT"
    }
    subjects = {s for s, _ in result.subject_verb_pairs}
    orphan_verbs = verb_tokens - {v for _, v in result.subject_verb_pairs} - subjects
    if orphan_verbs:
        verbs_list = ", ".join(sorted(orphan_verbs)[:3])
        warnings.append(f"verbs without explicit subjects: {verbs_list}")

    # Unclear pronoun antecedants (dummy subjects)
    for tok in result.dependency_tree.tokens:
        if tok.token.lower() == "it" and tok.dep == "nsubj":
            warnings.append("impersonal 'it' subject (unclear reference)")

    # Ambiguous prepositional attachment
    prep_count = sum(1 for t in result.dependency_tree.tokens if t.pos == "ADP")
    if prep_count > 3:
        warnings.append(f"{prep_count} prepositional phrases (may obscure attachment)")

    return warnings


def detect_implicit_relations(result: NlpResult) -> list[str]:
    """Detect implied but unstated relationships (requires spaCy)."""
    if not result.has_spacy or not result.dependency_tree:
        return []
    signals: list[str] = []

    coord_conj = sum(1 for t in result.dependency_tree.tokens if t.dep == "CC")
    if coord_conj > 2:
        signals.append(f"{coord_conj} coordinations (parallel clauses, may conflate distinct intents)")

    # Copular constructions (X is Y) — may be under-specified
    copula = sum(1 for t in result.dependency_tree.tokens if t.pos == "AUX" and t.dep == "cop")
    if copula > 1:
        signals.append(f"{copula} copular constructions (X is Y — may hide implied properties)")

    return signals


def render_nlp_report(result: NlpResult) -> str:
    lines: list[str] = []
    sep = "=" * 60
    if not result.has_spacy:
        lines.append(sep)
        lines.append("  NLP bridge: spaCy not available (falling back to regex)")
        lines.append(f"  Install: pip install spacy && python -m spacy download en_core_web_sm")
        lines.append(sep)
        return "\n".join(lines)

    lines.append(sep)
    lines.append("  NLP deep parse (spaCy)")
    lines.append(sep)
    if result.subject_verb_pairs:
        pairs = [f"{s} → {v}" for s, v in result.subject_verb_pairs[:5]]
        lines.append(f"  Subject→Verb: {', '.join(pairs)}")
    if result.verb_objects:
        pairs = [f"{v} → {o}" for v, o in result.verb_objects[:5]]
        lines.append(f"  Verb→Object: {', '.join(pairs)}")
    if result.named_entities:
        entities = [f"{e[0]} ({e[1]})" for e in result.named_entities[:5]]
        lines.append(f"  Entities: {', '.join(entities)}")
    if result.dependency_tree and result.dependency_tree.root:
        lines.append(f"  Root: {result.dependency_tree.root}")

    semantic = detect_semantic_ambiguity(result)
    if semantic:
        for w in semantic:
            lines.append(f"  ! {w}")
    implicit = detect_implicit_relations(result)
    if implicit:
        for s in implicit:
            lines.append(f"  ! {s}")
    lines.append(sep)
    return "\n".join(lines)
