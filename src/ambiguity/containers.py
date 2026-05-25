"""Verb taxonomy, keyword maps, and container definitions."""

from typing import NamedTuple


class Container(NamedTuple):
    name: str
    description: str
    specificity: float


CONTAINERS: dict[str, Container] = {
    "code_generation": Container("code_generation", "Producing new code artifacts", 0.6),
    "explanation": Container("explanation", "Tutorial or expository content", 0.7),
    "analysis": Container("analysis", "Decomposition or assessment", 0.7),
    "transformation": Container("transformation", "Converting or refactoring existing things", 0.7),
    "retrieval": Container("retrieval", "Factual or informational query", 0.6),
    "ordering": Container("ordering", "Sorting, ranking, or sequencing", 0.8),
    "reasoning": Container("reasoning", "Step-by-step logical deduction", 0.8),
    "general_processing": Container("general_processing", "Non-specific processing action", 0.2),
    "function_definition": Container("function_definition", "Declaring or defining a function", 0.8),
    "python_syntax": Container("python_syntax", "Python-specific language features", 0.6),
    "error_handling": Container("error_handling", "Edge cases, exceptions, robustness", 0.8),
    "performance": Container("performance", "Efficiency, speed, optimization", 0.8),
    "verification": Container("verification", "Checking, validating, confirming", 0.7),
    "query": Container("query", "Asking for information or clarification", 0.5),
    "creation": Container("creation", "Generating novel content", 0.5),
    "constraint": Container("constraint", "Boundary or limitation on scope", 0.9),
}

KNOWN_ACRONYMS: dict[str, str] = {
    "UDL": "Unified Data Layer",
    "CHAP": "Cross-Harness Alignment Protocol",
    "LLM": "Large Language Model",
    "API": "Application Programming Interface",
    "JSON": "JavaScript Object Notation",
    "YAML": "YAML Ain't Markup Language",
    "CSV": "Comma-Separated Values",
    "HTML": "HyperText Markup Language",
    "CSS": "Cascading Style Sheets",
    "JS": "JavaScript",
    "TS": "TypeScript",
    "CLI": "Command Line Interface",
    "TUI": "Terminal User Interface",
    "SDK": "Software Development Kit",
    "IDE": "Integrated Development Environment",
    "DB": "Database",
    "SQL": "Structured Query Language",
    "ORM": "Object-Relational Mapping",
    "REST": "Representational State Transfer",
    "URL": "Uniform Resource Locator",
}

VERB_TAXONOMY: dict[str, dict] = {
    "write": {"containers": ["code_generation", "creation"], "specificity": 0.6},
    "create": {"containers": ["code_generation", "creation"], "specificity": 0.5},
    "generate": {"containers": ["code_generation", "creation"], "specificity": 0.5},
    "build": {"containers": ["code_generation"], "specificity": 0.6},
    "implement": {"containers": ["code_generation"], "specificity": 0.7},
    "produce": {"containers": ["code_generation", "creation"], "specificity": 0.5},
    "explain": {"containers": ["explanation", "reasoning"], "specificity": 0.7},
    "describe": {"containers": ["explanation"], "specificity": 0.6},
    "clarify": {"containers": ["explanation"], "specificity": 0.7},
    "walk through": {"containers": ["explanation"], "specificity": 0.7},
    "elaborate": {"containers": ["explanation"], "specificity": 0.7},
    "analyze": {"containers": ["analysis"], "specificity": 0.7},
    "compare": {"containers": ["analysis"], "specificity": 0.8},
    "evaluate": {"containers": ["analysis"], "specificity": 0.8},
    "diagnose": {"containers": ["analysis"], "specificity": 0.8},
    "audit": {"containers": ["analysis", "verification"], "specificity": 0.8},
    "convert": {"containers": ["transformation"], "specificity": 0.8},
    "translate": {"containers": ["transformation"], "specificity": 0.8},
    "refactor": {"containers": ["transformation", "code_generation"], "specificity": 0.8},
    "rewrite": {"containers": ["transformation"], "specificity": 0.7},
    "adapt": {"containers": ["transformation"], "specificity": 0.7},
    "sort": {"containers": ["ordering", "code_generation"], "specificity": 0.8},
    "order": {"containers": ["ordering"], "specificity": 0.7},
    "rank": {"containers": ["ordering", "analysis"], "specificity": 0.8},
    "sorts": {"containers": ["ordering", "code_generation"], "specificity": 0.8},
    "sorted": {"containers": ["ordering", "code_generation"], "specificity": 0.8},
    "sorting": {"containers": ["ordering", "code_generation"], "specificity": 0.8},
    "handle": {"containers": ["general_processing"], "specificity": 0.2},
    "do": {"containers": [], "specificity": 0.1},
    "deal": {"containers": ["general_processing"], "specificity": 0.2},
    "make": {"containers": ["creation"], "specificity": 0.3},
    "get": {"containers": ["retrieval"], "specificity": 0.3},
    "find": {"containers": ["retrieval"], "specificity": 0.4},
    "tell": {"containers": ["explanation"], "specificity": 0.4},
    "give": {"containers": ["retrieval", "creation"], "specificity": 0.3},
    "check": {"containers": ["verification"], "specificity": 0.6},
    "verify": {"containers": ["verification"], "specificity": 0.8},
    "validate": {"containers": ["verification"], "specificity": 0.8},
    "confirm": {"containers": ["verification"], "specificity": 0.7},
    "review": {"containers": ["verification", "analysis"], "specificity": 0.7},
    "think": {"containers": ["reasoning"], "specificity": 0.5},
    "reason": {"containers": ["reasoning"], "specificity": 0.7},
    "fix": {"containers": ["code_generation", "transformation"], "specificity": 0.7},
    "debug": {"containers": ["analysis", "code_generation"], "specificity": 0.8},
    "test": {"containers": ["verification"], "specificity": 0.7},
    "improve": {"containers": ["code_generation", "transformation"], "specificity": 0.6},
    "optimise": {"containers": ["performance", "code_generation"], "specificity": 0.8},
    "enhance": {"containers": ["code_generation", "creation"], "specificity": 0.5},
    "uplift": {"containers": ["transformation", "creation"], "specificity": 0.5},
    "expand": {"containers": ["creation", "explanation"], "specificity": 0.5},
    "upgrade": {"containers": ["transformation"], "specificity": 0.7},
    "migrate": {"containers": ["transformation"], "specificity": 0.8},
    "integrate": {"containers": ["code_generation", "transformation"], "specificity": 0.7},
    "automate": {"containers": ["code_generation"], "specificity": 0.8},
    "deploy": {"containers": ["code_generation"], "specificity": 0.8},
    "monitor": {"containers": ["analysis", "verification"], "specificity": 0.7},
    "log": {"containers": ["analysis"], "specificity": 0.6},
    "notify": {"containers": ["explanation"], "specificity": 0.6},
    "render": {"containers": ["code_generation", "creation"], "specificity": 0.7},
    "parse": {"containers": ["analysis", "transformation"], "specificity": 0.8},
    "extract": {"containers": ["analysis", "transformation"], "specificity": 0.7},
    "merge": {"containers": ["transformation"], "specificity": 0.8},
    "split": {"containers": ["transformation", "analysis"], "specificity": 0.7},
    "remove": {"containers": ["transformation"], "specificity": 0.7},
    "add": {"containers": ["code_generation"], "specificity": 0.5},
    "update": {"containers": ["code_generation", "transformation"], "specificity": 0.5},
    "register": {"containers": ["code_generation", "creation"], "specificity": 0.6},
    "process": {"containers": ["general_processing"], "specificity": 0.3},
    "configure": {"containers": ["code_generation"], "specificity": 0.6},
    "install": {"containers": ["code_generation"], "specificity": 0.7},
    "uninstall": {"containers": ["code_generation"], "specificity": 0.8},
    "start": {"containers": ["code_generation", "explanation"], "specificity": 0.4},
    "stop": {"containers": ["code_generation"], "specificity": 0.6},
    "restart": {"containers": ["code_generation"], "specificity": 0.6},
    "optimize": {"containers": ["performance", "code_generation"], "specificity": 0.8},
    "refine": {"containers": ["code_generation", "transformation"], "specificity": 0.7},
    "clean": {"containers": ["code_generation"], "specificity": 0.5},
    "document": {"containers": ["creation", "explanation"], "specificity": 0.7},
    "summarize": {"containers": ["analysis", "creation"], "specificity": 0.7},
    "include": {"containers": ["code_generation", "creation"], "specificity": 0.4},
    "consider": {"containers": ["reasoning"], "specificity": 0.6},
    "cite": {"containers": ["explanation", "verification"], "specificity": 0.7},
    "follow": {"containers": ["general_processing"], "specificity": 0.4},
    "provide": {"containers": ["creation", "explanation"], "specificity": 0.4},
    "perform": {"containers": ["general_processing"], "specificity": 0.3},
    "require": {"containers": [], "specificity": 0.2},
    "assume": {"containers": ["reasoning"], "specificity": 0.5},
    "search": {"containers": ["retrieval"], "specificity": 0.7},
    "mention": {"containers": ["explanation"], "specificity": 0.4},
    "apply": {"containers": ["code_generation", "transformation"], "specificity": 0.5},
    "support": {"containers": ["verification", "explanation"], "specificity": 0.5},
    "reference": {"containers": ["explanation", "verification"], "specificity": 0.6},
    "respond": {"containers": ["explanation", "creation"], "specificity": 0.3},
    "replace": {"containers": ["transformation"], "specificity": 0.7},
    "return": {"containers": ["code_generation", "explanation"], "specificity": 0.5},
    "execute": {"containers": ["code_generation", "general_processing"], "specificity": 0.6},
    "call": {"containers": ["code_generation", "retrieval"], "specificity": 0.5},
    "modify": {"containers": ["code_generation", "transformation"], "specificity": 0.5},
    "output": {"containers": ["code_generation", "creation"], "specificity": 0.4},
    "select": {"containers": ["retrieval", "analysis"], "specificity": 0.6},
    "specify": {"containers": ["explanation", "code_generation"], "specificity": 0.5},
    "match": {"containers": ["verification", "analysis"], "specificity": 0.6},
    "note": {"containers": ["explanation"], "specificity": 0.4},
    "help": {"containers": ["explanation", "code_generation"], "specificity": 0.3},
    "answer": {"containers": ["explanation", "creation"], "specificity": 0.4},
    "discuss": {"containers": ["reasoning", "explanation"], "specificity": 0.5},
    "block": {"containers": ["code_generation", "general_processing"], "specificity": 0.5},
    "limit": {"containers": ["code_generation", "transformation"], "specificity": 0.5},
    "commit": {"containers": ["code_generation"], "specificity": 0.7},
    "print": {"containers": ["code_generation", "creation"], "specificity": 0.5},
    "quote": {"containers": ["explanation", "verification"], "specificity": 0.6},
}

KEYWORD_MAP: dict[str, dict] = {
    "function": {"containers": ["code_generation", "function_definition"]},
    "def": {"containers": ["function_definition"]},
    "python": {"containers": ["python_syntax"]},
    "list": {"containers": ["code_generation"], "collision": ["data_structure", "shopping_list"]},
    "error": {"containers": ["error_handling"]},
    "exception": {"containers": ["error_handling"]},
    "edge case": {"containers": ["error_handling"]},
    "efficient": {"containers": ["performance"]},
    "fast": {"containers": ["performance"]},

    "import": {"containers": ["constraint"]},
    "only": {"containers": ["constraint"]},
    "exactly": {"containers": ["constraint"]},
    "must": {"containers": ["constraint"]},
    "specifically": {"containers": ["constraint"]},
    "dont": {"containers": ["constraint"]},
    "do not": {"containers": ["constraint"]},
    "avoid": {"containers": ["constraint"]},
    "never": {"containers": ["constraint"]},
    "without": {"containers": ["constraint"]},
    "no": {"containers": ["constraint"]},
    "why": {"containers": ["explanation", "analysis"]},
    "how": {"containers": ["explanation"]},
    "what": {"containers": ["retrieval", "explanation"]},
    "step by step": {"containers": ["reasoning"]},
    "think": {"containers": ["reasoning"]},
}

SPECIFICITY_BANDS = {
    "vague": (0.0, 0.3),
    "moderate": (0.3, 0.6),
    "specific": (0.6, 0.8),
    "precise": (0.8, 1.0),
}


def specificity_band(score: float) -> str:
    for band, (lo, hi) in SPECIFICITY_BANDS.items():
        if lo <= score < hi:
            return band
    return "precise"


def containers_for_verb(verb: str) -> tuple[list[str], float]:
    verb_lower = verb.lower()
    entry = VERB_TAXONOMY.get(verb_lower)
    if entry:
        return entry["containers"], entry["specificity"]
    return [], 0.0


def containers_for_keyword(keyword: str) -> list[str]:
    kw_lower = keyword.lower()
    entry = KEYWORD_MAP.get(kw_lower)
    if entry:
        return entry["containers"]
    return []


def collisions_for_keyword(keyword: str) -> list[str]:
    kw_lower = keyword.lower()
    entry = KEYWORD_MAP.get(kw_lower)
    if entry and "collision" in entry:
        return entry["collision"]
    return []


SPELLING_CORRECTIONS: dict[str, str] = {
    "allign": "align",
    "alligns": "aligns",
    "alligned": "aligned",
    "allignment": "alignment",
    "recieve": "receive",
    "recieved": "received",
    "seperate": "separate",
    "definately": "definitely",
    "occured": "occurred",
    "occuring": "occurring",
    "ocur": "occur",
    "wierd": "weird",
    "acheive": "achieve",
    "acheiving": "achieving",
    "beleive": "believe",
    "beleived": "believed",
    "writting": "writing",
    "writen": "written",
    "untill": "until",
    "enviroment": "environment",
    "enviromental": "environmental",
    "dependancy": "dependency",
    "dependancies": "dependencies",
    "maintenence": "maintenance",
    "maintanance": "maintenance",
    "impliment": "implement",
    "implimentation": "implementation",
    "implimented": "implemented",
    "optimise": "optimize",
    "optimised": "optimized",
    "optimising": "optimizing",
    "normalise": "normalize",
    "normalised": "normalized",
    "normalising": "normalizing",
    "customise": "customize",
    "customised": "customized",
    "customising": "customizing",
    "initialise": "initialize",
    "initialised": "initialized",
    "initialising": "initializing",
    "finalise": "finalize",
    "finalised": "finalized",
    "finalising": "finalizing",
    "utilises": "utilize",
    "utilised": "utilized",
    "utilising": "utilizing",
    "orginize": "organize",
    "orginised": "organized",
    "orginising": "organizing",
}


FUZZY_IGNORE: set[str] = {
    "and", "the", "for", "with", "from", "this", "that", "these", "those",
    "to", "in", "of", "at", "by", "on", "as", "a", "an", "or", "but", "nor",
    "asap", "aka", "etc", "ie", "eg", "via", "vs", "per",
    "about", "above", "after", "before", "between", "through", "during",
    "because", "while", "until", "since", "although", "though",
    "into", "onto", "upon", "within", "without", "across", "against",
    "under", "over", "out", "off", "down", "up", "all", "any", "each",
    "every", "both", "few", "many", "some", "much", "very", "too",
    "also", "just", "then", "now", "here", "there", "than", "else",
    "their", "your", "our", "its", "his", "her", "my",
    "working", "looking", "making", "taking", "giving", "coming",
    "going", "doing", "having", "being", "saying", "seeing",
    "using", "calling", "trying", "asking", "telling", "showing",
    "running", "putting", "setting", "letting", "getting",
    "thing", "things", "stuff", "something", "anything", "nothing",
    "people", "person", "place", "time", "way", "number", "world",
    "life", "hand", "part", "child", "eye", "woman", "man", "men",
    "work", "study", "family", "point", "city", "state", "area",
    "water", "group", "country", "problem", "system", "program",
    "already", "always", "never", "often", "sometimes", "usually",
    "today", "tomorrow", "yesterday", "morning", "evening", "night",
    "please", "thanks", "sorry", "hello", "goodbye", "welcome",
    "so", "long", "text", "top", "set", "short", "fit", "real",
    "kind", "well", "move", "old", "new", "big", "small", "high", "low",
    "end", "next", "last", "first", "second", "third",
    "left", "right", "top", "bottom", "front", "back", "side",
    "still", "yet", "already", "quite", "rather", "pretty",
    "might", "must", "shall", "should", "could", "would", "may", "can",
    "say", "says", "said", "want", "need", "like", "love", "hate",
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
}


def levenshtein_distance(a: str, b: str) -> int:
    a_len, b_len = len(a), len(b)
    matrix = [[0] * (b_len + 1) for _ in range(a_len + 1)]
    for i in range(a_len + 1):
        matrix[i][0] = i
    for j in range(b_len + 1):
        matrix[0][j] = j
    for i in range(1, a_len + 1):
        for j in range(1, b_len + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            matrix[i][j] = min(
                matrix[i - 1][j] + 1,
                matrix[i][j - 1] + 1,
                matrix[i - 1][j - 1] + cost,
            )
    return matrix[a_len][b_len]


def fuzzy_verb_match(word: str) -> dict | None:
    lower = word.lower()
    if lower in FUZZY_IGNORE:
        return None
    if lower in VERB_TAXONOMY:
        return {"verb": lower, "distance": 0}
    best = None
    for known in VERB_TAXONOMY:
        d = levenshtein_distance(lower, known)
        if d == 0:
            return {"verb": known, "distance": 0}
        max_dist = 1  # distance 2 produces too many false positives from common nouns
        if d <= max_dist:
            if best is None or d < best["distance"]:
                best = {"verb": known, "distance": d}
    return best


def resolve_acronym(word: str) -> str | None:
    return KNOWN_ACRONYMS.get(word.upper())
