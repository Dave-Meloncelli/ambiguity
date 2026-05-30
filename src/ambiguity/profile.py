"""Self-learning profile — local history, threshold adjustment, vocabulary learning."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .parser import ParseResult
from .scoring import AmbiguityScore
from .containers import VERB_TAXONOMY, KEYWORD_MAP, KNOWN_ACRONYMS


PROFILE_DIR = Path(os.environ.get("AMBIGUITY_PROFILE", Path.home() / ".ambiguity"))
PROFILE_PATH = PROFILE_DIR / "profile.json"
HISTORY_MAX = 500


class Profile:
    PROFILE_PATH: Path = PROFILE_PATH
    entries: list[dict[str, Any]]
    dismissed: dict[str, int]
    learned_verbs: dict[str, dict]
    learned_acronyms: dict[str, str]
    learned_keywords: dict[str, dict]
    score_baseline: float
    score_std: float | None
    threshold: float

    def __init__(self):
        self.entries = []
        self.dismissed = {}
        self.learned_verbs = {}
        self.learned_acronyms = {}
        self.learned_keywords = {}
        self.score_baseline = 5.0
        self.score_std = None
        self.threshold = 4.0
        self._load()

    def _load(self):
        if not PROFILE_PATH.exists():
            return
        try:
            data = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
            self.entries = data.get("entries", [])
            self.dismissed = data.get("dismissed", {})
            self.learned_verbs = data.get("learned_verbs", {})
            self.learned_acronyms = data.get("learned_acronyms", {})
            self.learned_keywords = data.get("learned_keywords", {})
            self.score_baseline = data.get("score_baseline", 5.0)
            self.score_std = data.get("score_std")
            self.threshold = data.get("threshold", 4.0)
            self._reapply_learned()
            self._recalibrate()
        except (json.JSONDecodeError, OSError):
            pass

    def _reapply_learned(self):
        for verb, entry in self.learned_verbs.items():
            VERB_TAXONOMY[verb] = {
                "containers": entry.get("containers", []),
                "specificity": entry.get("specificity", 0.5),
            }
        for abbr, expansion in self.learned_acronyms.items():
            KNOWN_ACRONYMS[abbr.upper()] = expansion
        for keyword, entry in self.learned_keywords.items():
            KEYWORD_MAP[keyword.lower()] = {"containers": entry.get("containers", [])}

    def _save(self):
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "entries": self.entries[-HISTORY_MAX:],
            "dismissed": self.dismissed,
            "learned_verbs": self.learned_verbs,
            "learned_acronyms": self.learned_acronyms,
            "learned_keywords": self.learned_keywords,
            "score_baseline": self.score_baseline,
            "score_std": self.score_std,
            "threshold": self.threshold,
        }
        PROFILE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def record(self, result: ParseResult, score: AmbiguityScore, advisory: str | None):
        entry = {
            "prompt": result.text[:200],
            "score": round(score.total, 1),
            "band": score.band,
            "verb_specificity": round(score.verb_specificity, 2),
            "container_count": score.container_overlap,
            "constraint_count": score.constraint_count,
            "advisory": advisory,
            "word_count": result.word_count,
            "instruction_count": result.instruction_count,
            "verbs": result.verbs,
            "acronyms": [a for a, _ in result.acronyms],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.entries.append(entry)
        self._recalibrate()
        self._save()

    def dismiss(self, flag_type: str):
        self.dismissed[flag_type] = self.dismissed.get(flag_type, 0) + 1
        self._save()

    def learn_verb(self, verb: str, containers: list[str] | None = None, specificity: float | None = None):
        self.learned_verbs[verb.lower()] = {
            "containers": containers or [],
            "specificity": specificity or 0.5,
            "learned_at": datetime.now(timezone.utc).isoformat(),
        }
        VERB_TAXONOMY[verb.lower()] = {
            "containers": containers or [],
            "specificity": specificity or 0.5,
        }
        self._save()

    def learn_acronym(self, abbr: str, expansion: str):
        self.learned_acronyms[abbr.upper()] = expansion
        KNOWN_ACRONYMS[abbr.upper()] = expansion
        self._save()

    def learn_keyword(self, keyword: str, containers: list[str]):
        self.learned_keywords[keyword.lower()] = {
            "containers": containers,
            "learned_at": datetime.now(timezone.utc).isoformat(),
        }
        KEYWORD_MAP[keyword.lower()] = {"containers": containers}
        self._save()

    def _recalibrate(self):
        if len(self.entries) < 10:
            return
        scores = [e["score"] for e in self.entries[-50:]]
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        self.score_baseline = round(mean, 1)
        self.score_std = round(variance ** 0.5, 1)
        self.threshold = round(mean - self.score_std * 0.5, 1)

    def suppressed_flags(self) -> set[str]:
        result = set()
        for flag_type, count in self.dismissed.items():
            if count >= 3:
                result.add(flag_type)
        return result

    def adjusted_threshold(self) -> float:
        return max(2.0, min(8.0, self.threshold))


def get_profile() -> Profile:
    if not hasattr(get_profile, "_cache"):
        get_profile._cache = Profile()
    return get_profile._cache
