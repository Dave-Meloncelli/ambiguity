"""Core analysis pipeline — orchestrates parse, score, and report."""

from .parser import parse, ParseResult, VERB_SET
from .scoring import AmbiguityScore
from .report import render_report, render_json
from .bridges import as_udl_envelope, as_minimal_envelope
from .rhetoric import analyze_rhetoric, RhetoricResult
from .chunking import chunk, ChunkResult
from .constraints import ConstraintAnalysis
from .embeddings import analyze_keyword_coverage, EmbeddingAnalysis, DOMAIN_KEYWORDS
from .profile import get_profile


class Analysis:
    result: ParseResult
    score: AmbiguityScore
    rhetoric: RhetoricResult
    chunking: ChunkResult
    constraint_analysis: ConstraintAnalysis
    embedding_analysis: EmbeddingAnalysis
    udl_envelope: str | None
    minimal_envelope: dict

    def __init__(self, text: str):
        self.raw_text = text
        self.result = parse(text)
        self.rhetoric = analyze_rhetoric(text)
        self.chunking = chunk(text, known_verbs=VERB_SET)
        self.profile = get_profile()
        self.score = AmbiguityScore(self.result, self.rhetoric, self.chunking, profile=self.profile)

        self.constraint_analysis = ConstraintAnalysis.from_parse(self.result)
        self.embedding_analysis = analyze_keyword_coverage(
            existing_keywords=self.result.keywords + self.result.verbs,
            domain_keywords=DOMAIN_KEYWORDS,
        )

        udl = as_udl_envelope(self.result, self.score)
        self.udl_envelope = udl if isinstance(udl, str) else None

        self.minimal_envelope = as_minimal_envelope(self.result, self.score)

    def terminal_report(self) -> str:
        return render_report(self.result, self.score)

    def json_report(self) -> dict:
        return render_json(self.result, self.score)

    def full_output(self, include_udl: bool = False) -> dict:
        output = self.json_report()
        output["_envelope"] = self.minimal_envelope
        if include_udl and self.udl_envelope:
            import json
            try:
                output["_udl_envelope"] = json.loads(self.udl_envelope)
            except (json.JSONDecodeError, TypeError):
                output["_udl_envelope"] = self.udl_envelope
        return output
