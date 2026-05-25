"""Core analysis pipeline — orchestrates parse, score, and report."""

from .parser import parse, ParseResult
from .scoring import AmbiguityScore
from .report import render_report, render_json
from .bridges import as_udl_envelope, as_minimal_envelope


class Analysis:
    result: ParseResult
    score: AmbiguityScore
    udl_envelope: str | None
    minimal_envelope: dict

    def __init__(self, text: str):
        self.result = parse(text)
        self.score = AmbiguityScore(self.result)

        udl = as_udl_envelope(self.result, self.score)
        self.udl_envelope = udl if isinstance(udl, str) else None

        self.minimal_envelope = as_minimal_envelope(self.result, self.score)

    def terminal_report(self) -> str:
        udl_info = None
        if self.udl_envelope:
            udl_info = f"envelope written ({len(self.udl_envelope)} bytes)"
        return render_report(self.result, self.score, udl_info=udl_info)

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
