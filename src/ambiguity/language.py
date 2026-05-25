"""Language detection and per-language configuration."""

import re
from typing import NamedTuple


class LanguageProfile(NamedTuple):
    code: str
    name: str
    rtl: bool
    tokenization_notes: str


LANGUAGE_PROFILES: dict[str, LanguageProfile] = {
    "en": LanguageProfile("en", "English", False, "BPE splits common words; 'I'll' may be 1-2 tokens"),
    "zh": LanguageProfile("zh", "Chinese", False, "Each character is typically 1 token; high token density"),
    "ja": LanguageProfile("ja", "Japanese", False, "Mixed script; kanji compounds may split unexpectedly"),
    "ko": LanguageProfile("ko", "Korean", False, "Each hangul syllable block is 1-2 tokens"),
    "ar": LanguageProfile("ar", "Arabic", True, "RTL; prefix/suffix morphology creates variable token splits"),
    "he": LanguageProfile("he", "Hebrew", True, "RTL; prefix chains increase token count"),
    "fr": LanguageProfile("fr", "French", False, "Article+noun contractions may fuse tokens"),
    "de": LanguageProfile("de", "German", False, "Compound nouns split into multiple tokens"),
    "es": LanguageProfile("es", "Spanish", False, "Verb conjugation produces longer token sequences"),
    "pt": LanguageProfile("pt", "Portuguese", False, "Similar token profile to Spanish"),
    "ru": LanguageProfile("ru", "Russian", False, "Cyrillic; rich morphology creates variable token splits"),
    "hi": LanguageProfile("hi", "Hindi", False, "Devanagari script; matra combinations affect tokenization"),
}

LANGUAGE_MARKERS: dict[str, list[bytes]] = {
    "zh": [b"[\u4e00-\u9fff]", b"[\u3400-\u4dbf]"],
    "ja": [b"[\u3040-\u309f]", b"[\u30a0-\u30ff]", b"[\u4e00-\u9fff]"],
    "ko": [b"[\uac00-\ud7af]", b"[\u1100-\u11ff]"],
    "ar": [b"[\u0600-\u06ff]", b"[\u0750-\u077f]"],
    "he": [b"[\u0590-\u05ff]"],
    "ru": [b"[\u0400-\u04ff]"],
    "hi": [b"[\u0900-\u097f]"],
}

COMMON_EN_WORDS: set[str] = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
    "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "say", "her",
    "she", "or", "an", "will", "my", "one", "all", "would", "there",
    "their", "what", "so", "up", "out", "if", "about", "who", "get",
    "which", "go", "me", "when", "make", "can", "like", "time", "no",
    "just", "him", "know", "take", "people", "into", "year", "your",
    "good", "some", "could", "them", "see", "other", "than", "then",
    "now", "look", "only", "come", "its", "over", "think", "also",
    "back", "after", "use", "two", "how", "our", "work", "first",
    "well", "way", "even", "new", "want", "because", "any", "these",
    "give", "day", "most", "us", "write", "function", "list", "code",
    "data", "file", "string", "number", "value", "return", "class",
    "import", "print", "input", "output", "error", "test", "sort",
    "python", "javascript", "typescript", "html", "css",
}

EN_SPECIFIC_STOPWORDS: set[str] = {
    "would", "could", "should", "might", "may", "shall",
    "therefore", "however", "furthermore", "nevertheless",
}


def detect_language(text: str) -> LanguageProfile:
    """Detect the dominant language of a prompt.

    Uses a combination of script detection (CJK, RTL, Cyrillic, etc.)
    and English word frequency. Falls back to English for ASCII text.
    """
    if not text.strip():
        return LANGUAGE_PROFILES["en"]

    for code, markers in LANGUAGE_MARKERS.items():
        for marker in markers:
            if marker and re.search(marker.decode("utf-8") if isinstance(marker, bytes) else marker, text):
                return LANGUAGE_PROFILES[code]

    words = re.findall(r"[a-zA-Z]+", text)
    if not words:
        return LANGUAGE_PROFILES["en"]

    lower_words = {w.lower() for w in words}
    en_ratio = len(lower_words & COMMON_EN_WORDS) / len(lower_words)

    if en_ratio > 0.15:
        return LANGUAGE_PROFILES["en"]

    return LANGUAGE_PROFILES["en"]


def tokenization_warning(text: str, profile: LanguageProfile) -> str | None:
    if profile.code == "en":
        i_contractions = len(re.findall(r"\b\w+'\w+\b", text))
        if i_contractions > 0:
            return f"Contains {i_contractions} contraction(s); may split into unexpected tokens"
        return None
    return f"{profile.name} tokenization: {profile.tokenization_notes}"
