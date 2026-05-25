"""Deterministic prompt parser — extracts verbs, keywords, constraints, references."""

import re
from typing import NamedTuple

from .containers import (
    KEYWORD_MAP,
    KNOWN_ACRONYMS,
    SPELLING_CORRECTIONS,
    VERB_TAXONOMY,
    fuzzy_verb_match,
    levenshtein_distance,
)


class FuzzyMatch(NamedTuple):
    original: str
    corrected: str
    distance: int


class StutterPair(NamedTuple):
    word: str
    occurrences: int


class MissingSpace(NamedTuple):
    combined: str
    split: tuple[str, str]


class ParseResult(NamedTuple):
    text: str
    verbs: list[str]
    fuzzy_verbs: list[FuzzyMatch]
    keywords: list[str]
    constraints: list[str]
    acronyms: list[tuple[str, str]]
    unqualified_refs: list[str]
    typo_words: list[FuzzyMatch]
    stutter_words: list[StutterPair]
    missing_spaces: list[MissingSpace]
    repeated_chars: list[str]
    has_terminal_punctuation: bool
    word_count: int
    sentence_count: int
    instruction_count: int


VERB_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in VERB_TAXONOMY) + r")\b", re.IGNORECASE
)

CONSTRAINT_PATTERNS = [
    (re.compile(r"\b(only|exactly|specifically|strictly)\b", re.IGNORECASE), "exact"),
    (re.compile(r"\b(must|need to|have to|required)\b", re.IGNORECASE), "requirement"),
    (re.compile(r"\b(don't|do not|without|avoid|never|no |not)\b", re.IGNORECASE), "negation"),
    (re.compile(r"\b(import|require|dependency|library)\b", re.IGNORECASE), "dependency"),
]

ACRONYM_PATTERN = re.compile(r"\b([A-Z]{2,})\b")

UNQUALIFIED_REF_PATTERNS = [
    re.compile(r"\bthe (thing|file|solution)\b", re.IGNORECASE),
    re.compile(r"\bit\b", re.IGNORECASE),
    re.compile(r"\b(as we discussed|as i said|as mentioned|as we know)\b", re.IGNORECASE),
]

SENTENCE_SPLIT = re.compile(r"[.!?]+")
INSTRUCTION_SPLIT = re.compile(r"[,;]|(?:and|then|next|after that)", re.IGNORECASE)

VERB_SET = set(VERB_TAXONOMY.keys())
KEYWORD_SET = set(KEYWORD_MAP.keys())


def _build_common_words() -> set[str]:
    base = {
        "the", "be", "to", "of", "and", "a", "in", "that", "have", "it",
        "for", "not", "on", "with", "he", "as", "you", "do", "at", "this",
        "but", "his", "by", "from", "they", "we", "say", "her", "she", "or",
        "an", "will", "my", "one", "all", "would", "there", "their", "what",
        "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
        "when", "make", "can", "like", "time", "no", "just", "him", "know",
        "take", "people", "into", "year", "your", "good", "some", "could",
        "them", "see", "other", "than", "then", "now", "look", "only", "come",
        "its", "over", "think", "also", "back", "after", "use", "two", "how",
        "our", "work", "first", "well", "way", "even", "new", "want", "because",
        "any", "these", "give", "day", "most", "us", "need", "should", "does",
        "code", "file", "test", "data", "function", "class", "method", "module",
        "app", "api", "ui", "fix", "add", "remove", "change", "update", "read",
        "write", "run", "set", "get", "show", "help", "info", "list", "sort",
        "implement", "convert", "verify", "explain", "create", "describe",
        "feature", "system", "config", "schema", "query", "route", "view",
        "page", "link", "path", "name", "type", "mode", "role", "flag",
        "user", "admin", "guest", "owner", "table", "field", "form",
        "item", "list", "log", "map", "key", "doc", "row", "col",
    }
    base.update(VERB_SET)
    base.update(KEYWORD_SET)
    return base


COMMON_WORDS = _build_common_words()


def _detect_missing_spaces(word_tokens: list[str]) -> list[MissingSpace]:
    found = []
    seen = set()
    for token in word_tokens:
        if len(token) < 8 or token in seen:
            continue
        for i in range(3, len(token) - 3):
            left = token[:i]
            right = token[i:]
            if left in COMMON_WORDS and right in COMMON_WORDS:
                found.append(MissingSpace(combined=token, split=(left, right)))
                seen.add(token)
                break
    return found


def _detect_stutter(word_tokens: list[str]) -> list[StutterPair]:
    found = []
    seen = set()
    i = 1
    while i < len(word_tokens):
        if word_tokens[i] == word_tokens[i - 1] and word_tokens[i] not in seen:
            seen.add(word_tokens[i])
            count = 2
            while i + count - 1 < len(word_tokens) and word_tokens[i + count - 1] == word_tokens[i]:
                count += 1
            found.append(StutterPair(word=word_tokens[i], occurrences=count))
        i += 1
    return found


def _detect_repeated_chars(word_tokens: list[str]) -> list[str]:
    found = []
    seen = set()
    repeat = re.compile(r"(.)\1{2,}")
    for token in word_tokens:
        if len(token) > 3 and repeat.search(token) and token not in seen:
            seen.add(token)
            found.append(token)
    return found


def parse(text: str) -> ParseResult:
    word_tokens = re.findall(r"\b[a-z]+\b", text.lower())
    verbs: list[str] = []
    fuzzy_verbs: list[FuzzyMatch] = []
    typo_words: list[FuzzyMatch] = []
    seen_verbs: set[str] = set()
    seen_fuzzy: set[str] = set()
    seen_typo: set[str] = set()

    for token in word_tokens:
        fuzzy = fuzzy_verb_match(token)
        if fuzzy and fuzzy["distance"] == 0 and fuzzy["verb"] not in seen_verbs:
            seen_verbs.add(fuzzy["verb"])
            verbs.append(fuzzy["verb"])
        elif fuzzy and fuzzy["distance"] > 0 and fuzzy["verb"] not in seen_fuzzy:
            seen_fuzzy.add(fuzzy["verb"])
            verbs.append(fuzzy["verb"])
            fuzzy_verbs.append(
                FuzzyMatch(original=token, corrected=fuzzy["verb"], distance=fuzzy["distance"])
            )
        elif fuzzy is None:
            correction = SPELLING_CORRECTIONS.get(token)
            if correction and token not in seen_typo:
                seen_typo.add(token)
                typo_words.append(
                    FuzzyMatch(
                        original=token,
                        corrected=correction,
                        distance=levenshtein_distance(token, correction),
                    )
                )

    if not verbs:
        for m in VERB_PATTERN.finditer(text):
            v = m.group(1).lower()
            if v not in seen_verbs:
                seen_verbs.add(v)
                verbs.append(v)

    keywords = []
    kw_set = set()
    for kw in KEYWORD_MAP:
        if re.search(r"\b" + re.escape(kw) + r"\b", text, re.IGNORECASE):
            if kw not in kw_set:
                kw_set.add(kw)
                keywords.append(kw)

    constraints = []
    for pattern, kind in CONSTRAINT_PATTERNS:
        if pattern.search(text):
            constraints.append(kind)

    acronyms = []
    seen = set()
    for m in ACRONYM_PATTERN.finditer(text):
        word = m.group(1)
        if word in KNOWN_ACRONYMS and word not in seen:
            seen.add(word)
            acronyms.append((word, KNOWN_ACRONYMS[word]))

    unqualified_refs = []
    for pattern in UNQUALIFIED_REF_PATTERNS:
        matches = pattern.findall(text)
        unqualified_refs.extend(m.lower().strip() for m in matches if m.strip())
    unqualified_refs = list(set(unqualified_refs))

    word_count = len(re.findall(r"\b\w+\b", text))
    sentences = SENTENCE_SPLIT.split(text)
    sentence_count = len([s for s in sentences if s.strip()])

    instructions = INSTRUCTION_SPLIT.split(text)
    instruction_count = len([i for i in instructions if i.strip()])

    missing_spaces = _detect_missing_spaces(word_tokens)
    stutter_words = _detect_stutter(word_tokens)
    repeated_chars = _detect_repeated_chars(word_tokens)

    trimmed = text.strip()
    has_terminal_punctuation = bool(trimmed and trimmed[-1] in ".!?")

    return ParseResult(
        text=text,
        verbs=verbs,
        fuzzy_verbs=fuzzy_verbs,
        keywords=keywords,
        constraints=constraints,
        acronyms=acronyms,
        unqualified_refs=unqualified_refs,
        typo_words=typo_words,
        stutter_words=stutter_words,
        missing_spaces=missing_spaces,
        repeated_chars=repeated_chars,
        has_terminal_punctuation=has_terminal_punctuation,
        word_count=word_count,
        sentence_count=sentence_count,
        instruction_count=instruction_count,
    )
