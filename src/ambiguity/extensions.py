"""Extension/plugin system for ambiguity — lightweight hooks for the analysis pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExtensionResult:
    annotations: list[str] = field(default_factory=list)
    score_modifier: float = 0.0
    block: bool = False
    block_reason: str | None = None


class BaseExtension:
    def on_pre_parse(self, prompt: str) -> ExtensionResult:
        return ExtensionResult()

    def on_post_parse(self, parse_result: dict[str, Any]) -> ExtensionResult:
        return ExtensionResult()

    def on_pre_score(self, score_state: dict[str, Any]) -> ExtensionResult:
        return ExtensionResult()

    def on_post_score(self, score_result: dict[str, Any]) -> ExtensionResult:
        return ExtensionResult()

    def name(self) -> str:
        return self.__class__.__name__


class ExtensionRegistry:
    def __init__(self):
        self._extensions: list[BaseExtension] = []

    def register(self, ext: BaseExtension) -> None:
        self._extensions.append(ext)

    def all(self) -> list[BaseExtension]:
        return list(self._extensions)

    def pre_parse(self, prompt: str) -> list[ExtensionResult]:
        return [ext.on_pre_parse(prompt) for ext in self._extensions]

    def post_parse(self, parse_result: dict[str, Any]) -> list[ExtensionResult]:
        return [ext.on_post_parse(parse_result) for ext in self._extensions]

    def pre_score(self, score_state: dict[str, Any]) -> list[ExtensionResult]:
        return [ext.on_pre_score(score_state) for ext in self._extensions]

    def post_score(self, score_result: dict[str, Any]) -> list[ExtensionResult]:
        return [ext.on_post_score(score_result) for ext in self._extensions]


def get_registry() -> ExtensionRegistry:
    if not hasattr(get_registry, "_cache"):
        get_registry._cache = ExtensionRegistry()
    return get_registry._cache


class MaxWordCountExtension(BaseExtension):
    def __init__(self, max_words: int = 500):
        self.max_words = max_words

    def on_pre_parse(self, prompt: str) -> ExtensionResult:
        word_count = len(prompt.split())
        if word_count > self.max_words:
            return ExtensionResult(
                block=True,
                block_reason=f"Prompt exceeds max word count ({word_count} > {self.max_words})",
            )
        return ExtensionResult()

    def name(self) -> str:
        return "MaxWordCountExtension"


__all__ = [
    "ExtensionResult",
    "BaseExtension",
    "ExtensionRegistry",
    "get_registry",
    "MaxWordCountExtension",
]
