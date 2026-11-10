"""Plain text matching for the Foundations checks: does a memory line hold the fact the learner said they saved?

Token overlap, not exact text: Hermes often rewords what it saves ("Harbor Bakery uses QuickBooks Online" may land as
"Harbor Bakery: QuickBooks Online"). Short words and common words are ignored. Stdlib only, no file access.
"""

from __future__ import annotations

import re

MAX_LINE = 300
THRESHOLD = 0.6
STOP = frozenset("""
a an and are as at be but by for from has have he her his i if in into is it its me my no not of on or our she so
that the their them they this to was we were what when which who will with you your uses use used save saved memory
remember please
""".split())


def tokens(text) -> list:
    words = re.findall(r"[a-z0-9][a-z0-9'+.-]*[a-z0-9]|[a-z0-9]", str(text or "").lower())
    return [w for w in words if len(w) >= 3 and w not in STOP]


def overlap(line, fact) -> float:
    want = set(tokens(fact))
    if not want:
        return 0.0
    return len(want & set(tokens(line))) / len(want)


def best_line(lines, fact, max_len: int = MAX_LINE):
    """(line, score) of the line that best holds the fact, among lines no longer than max_len, or (None, 0.0)."""
    best, score = None, 0.0
    for line in lines or []:
        if not isinstance(line, str) or len(line) > max_len:
            continue
        here = overlap(line, fact)
        if here > score:
            best, score = line, here
    return best, score


def holds(lines, fact, threshold: float = THRESHOLD, max_len: int = MAX_LINE):
    """The matching line, or None."""
    line, score = best_line(lines, fact, max_len)
    return line if line is not None and score >= threshold else None


def mentions(text, term) -> bool:
    """Does the text use the key term (whole words, any case)?"""
    term = str(term or "").strip().lower()
    if not term:
        return False
    return re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", str(text or "").lower()) is not None
