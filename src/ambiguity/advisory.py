"""Single-line best practice advisory, deterministic from analysis results."""

from .parser import ParseResult
from .scoring import AmbiguityScore
from .containers import containers_for_verb

_SUPPRESSED: set[str] = set()


def set_suppressed(flags: set[str]):
    _SUPPRESSED.clear()
    _SUPPRESSED.update(flags)


def advisory(result: ParseResult, score: AmbiguityScore) -> str | None:
    """Return the highest-priority single advisory line, or None if prompt is clean."""

    candidates = []

    # priority 1: vague verb
    vague_verbs = [v for v in result.verbs if containers_for_verb(v)[1] < 0.3]
    if vague_verbs and "vague_verb" not in _SUPPRESSED:
        v = vague_verbs[0]
        candidates.append((1, "vague_verb", f"replace vague verb '{v}' with a specific action (implement, convert, verify)"))

    # priority 2: no action verb
    if not result.verbs and result.word_count > 2 and "no_verb" not in _SUPPRESSED:
        candidates.append((2, "no_verb", "start with an action verb - 'write', 'explain', 'convert'"))

    # priority 3: no constraints
    if not result.constraints and result.word_count > 3 and result.verbs and "no_constraints" not in _SUPPRESSED:
        candidates.append((3, "no_constraints", "add at least one constraint - boundaries guide the model"))

    # priority 4: fuzzy verb match (typo verb that we still matched)
    if result.fuzzy_verbs and "fuzzy_verb" not in _SUPPRESSED:
        fv = result.fuzzy_verbs[0]
        candidates.append((4, "fuzzy_verb", f"guessing you meant '{fv.corrected}' for '{fv.original}' — close enough, I matched it"))

    # priority 5: acronyms
    if result.acronyms and "acronym" not in _SUPPRESSED:
        a, e = result.acronyms[0]
        candidates.append((5, "acronym", f"expand '{a}' to '{e}' on first use for consistent reception"))

    # priority 6: vocabulary scope
    if result.vocab_scope and "vocab_scope" not in _SUPPRESSED:
        vt = result.vocab_scope[0]
        candidates.append((6, "vocab_scope", f"define domain term '{vt.term}' before use — not all readers share your vocabulary"))

    # priority 7: multiple instructions
    if result.instruction_count > 3 and "multi_instruction" not in _SUPPRESSED:
        candidates.append((7, "multi_instruction", f"split into separate turns - {result.instruction_count} instructions overload reception"))

    # priority 8: unqualified references
    if result.unqualified_refs and "unqualified_ref" not in _SUPPRESSED:
        ref = result.unqualified_refs[0]
        candidates.append((8, "unqualified_ref", f"replace '{ref}' with a concrete reference"))

    # priority 9: typo words (spelling corrections)
    if result.typo_words and "typo" not in _SUPPRESSED:
        tw = result.typo_words[0]
        candidates.append((9, "typo", f"'{tw.original}' looks like '{tw.corrected}' — no worries, just flagging in case"))

    # priority 10: no terminal punctuation
    if not result.has_terminal_punctuation and result.word_count > 3 and "no_terminal_punct" not in _SUPPRESSED:
        candidates.append((10, "no_terminal_punct", "add a period or question mark at the end to signal completeness"))

    # priority 11: missing space
    if result.missing_spaces and "missing_space" not in _SUPPRESSED:
        ms = result.missing_spaces[0]
        candidates.append((11, "missing_space", f"'{ms.combined}' might be two words: '{ms.split[0]} {ms.split[1]}'"))

    # priority 12: stutter / repeated words
    if result.stutter_words and "stutter" not in _SUPPRESSED:
        sw = result.stutter_words[0]
        candidates.append((12, "stutter", f"'{sw.word}' repeated {sw.occurrences}x — likely a typo"))

    # priority 13: repeated characters
    if result.repeated_chars and "repeated_char" not in _SUPPRESSED:
        rc = result.repeated_chars[0]
        candidates.append((13, "repeated_char", f"'{rc}' has characters repeated 3+ times"))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0])
    return candidates[0][2]
