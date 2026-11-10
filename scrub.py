"""One scrubber for every excerpt Field Academy keeps or shows.

Merged from two places that used to keep their own lists: the Guide's run-history reader (``evidence.py``, 0.6) and
Cabinet's safety checks (``cab-0311/safety.py``: sk-, GitHub, AWS, Slack, Google, PEM, JWT and key=value). Added for
Foundations, which reads a practice profile's memory, logs and chat records: Telegram bot tokens, and ``.env``-style
``NAME=value`` lines for any name ending in KEY, TOKEN or SECRET.

The rule for anything kept as evidence: scrub first, then cut to length, then hash. The hash is always of the scrubbed
excerpt, so no fingerprint of a secret is ever stored. Stdlib only, no file access.
"""

from __future__ import annotations

import hashlib
import re

REMOVED = "[removed]"

# .env-style lines: the name stays (so a reader sees which setting it was), the value goes.
_ENV_LINE = re.compile(
    r"(?im)^(?P<lead>[ \t]*(?:export[ \t]+)?)(?P<name>[A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD))[ \t]*=[ \t]*(?P<value>.+?)[ \t]*$"
)

# (pattern, plain name). Order matters only for readability: every pattern runs.
_NAMED = (
    (re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"), "an API key"),
    (re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}|\bgithub_pat_[A-Za-z0-9_]{20,}"), "a GitHub token"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "an AWS key"),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"), "a Slack token"),
    (re.compile(r"\bAIza[0-9A-Za-z_-]{35}"), "a Google key"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----(?:.*?-----END [A-Z ]*PRIVATE KEY-----)?", re.S), "a private key"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"), "a login token"),
    (re.compile(r"(?<![\w:])\d{8,10}:[A-Za-z0-9_-]{35}(?![A-Za-z0-9_-])"), "a Telegram bot token"),
    (re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}", re.I), "a bearer token"),
    (re.compile(r"\b(?:sk|pk|rk|ghp|gho|xox[abp])[-_][A-Za-z0-9_-]{16,}\b"), "a key"),
    # Added in the 0.9 audit: shapes Hermes users hold that the list above missed (each shorter than the catch-all).
    (re.compile(r"\bhf_[A-Za-z0-9]{30,}\b"), "a Hugging Face token"),
    (re.compile(r"\b(?:fc|tvly|gsk|xapp)-[A-Za-z0-9_-]{20,}\b"), "an API key"),
    (re.compile(r"\b[MNO][A-Za-z0-9_-]{23,27}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27,40}\b"), "a Discord bot token"),
    (re.compile(r"(?i)https?://(?:hooks\.slack\.com/(?:services|workflows|triggers)|(?:[a-z0-9-]+\.)?discord(?:app)?\.com/api/webhooks)/[^\s'\"<>)]+"),
     "a webhook address"),
    (re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://[^\s/:@'\"]+:[^\s/@'\"]+@"), "a password in an address"),
    (re.compile(r"(?i)\bBasic\s+[A-Za-z0-9+/=]{16,}"), "a login header"),
    # key: value, key=value, and JSON's "key": "value" (the closing quote after the name used to stop the match).
    (re.compile(r"(?i)\b(?:api[_ -]?key|token|secret|passw(?:or)?d|passphrase)\b['\"]?\s*[:=]\s*['\"]?[^\s'\",}]+"), "a password or key"),
    # The Guide's catch-all: any run of 40 or more key-like characters.
    (re.compile(r"\b[A-Za-z0-9+/=_-]{40,}\b"), "a long key-like string"),
)

# The Guide's original four shapes, kept by name so evidence.py's readers behave as before (plus the new shapes, which
# evidence.redact now also removes through scrub()).
SHAPES_FOR_GUIDE = (
    re.compile(r"\b(?:sk|pk|rk|ghp|gho|xox[abp])[-_][A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}", re.I),
    re.compile(r"\b[A-Za-z0-9+/=_-]{40,}\b"),
    re.compile(r"(?i)\b(?:api[_-]?key|token|secret|password)\s*[=:]\s*\S+"),
)


def _text(value) -> str:
    if value is None:
        return ""
    return value if isinstance(value, str) else str(value)


def scrub(value, limit: int | None = None) -> str:
    """The text with every secret shape replaced by [removed], then cut to ``limit`` characters."""
    out = _text(value)
    out = _ENV_LINE.sub(lambda m: f"{m.group('lead')}{m.group('name')}={REMOVED}", out)
    for pattern, _ in _NAMED:
        out = pattern.sub(REMOVED, out)
    if limit is not None and limit >= 0:
        out = out[:limit]
    return out


def clip(value, limit: int) -> str:
    """Scrubbed, then cut to at most ``limit`` characters at a word boundary, ending in "…" when anything was cut.

    Record excerpts used to be cut mid-word ("the shared folder Ops/20"). A line that fits is kept whole; a longer one
    ends at the last space before the limit, unless that would drop more than half the text (one very long word).
    """
    out = scrub(value)
    if limit is None or limit < 0 or len(out) <= limit:
        return out
    if limit < 2:
        return out[:limit]
    head = out[:limit - 1]
    if not out[limit - 1].isspace():
        space = max(head.rfind(" "), head.rfind("\n"), head.rfind("\t"))
        if space >= (limit - 1) // 2:
            head = head[:space]
    return head.rstrip() + "…"


def scrub_name(value, limit: int | None = None) -> str:
    """A file or folder name, scrubbed of every secret shape. The 40-character catch-all applies only when the name
    isn't made of short words (each piece between - _ . or a space at most 24 characters), so
    ``harbor-bakery-quarterly-reconciliation-2026`` stays readable while a random key-like run is still removed."""
    text = _text(value)
    wordy = all(len(piece) <= 24 for piece in re.split(r"[-_. ]+", text))
    if not wordy:
        return scrub(text, limit)
    out = _ENV_LINE.sub(lambda m: f"{m.group('lead')}{m.group('name')}={REMOVED}", text)
    for pattern, _ in _NAMED[:-1]:
        out = pattern.sub(REMOVED, out)
    return out[:limit] if limit is not None and limit >= 0 else out


def kinds(value) -> list:
    """Plain names of the secret shapes found in the text, never the values."""
    text = _text(value)
    found = []
    if _ENV_LINE.search(text):
        found.append("a key, token or secret setting")
    for pattern, name in _NAMED:
        if pattern.search(text) and name not in found:
            found.append(name)
    return found


def excerpt(value, limit: int = 300) -> tuple:
    """(scrubbed excerpt, sha256 of that excerpt). Scrub first, then cut, then hash."""
    clean = scrub(value, limit)
    return clean, hashlib.sha256(clean.encode("utf-8")).hexdigest()
