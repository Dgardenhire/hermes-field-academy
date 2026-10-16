"""Read a learner's document and say exactly what is missing.

Pure functions over text: no storage, no file access, no Hermes. state.py reads
the file and calls ``analyze``. Keeping this apart is what lets the tests prove
the worked example in every document mission passes the very rules the learner
is held to, so an example can never disagree with its own check.

A document gate lists its sections. For each one the step carries a rule:

    {"heading": "Price", "min_words": 6, "needs": ["money"],
     "what": "what you will charge and for what",
     "hint": "...", "example": "..."}

``needs`` draws from NEEDS below. Each is a plain, checkable property of the
text (a number, a person's name, a dollar figure), never a judgment about
quality. Hermes can't be asked from here, so a pass means the document has the
parts a real one has. It does not mean the document is good, and the pass
message says so.
"""

from __future__ import annotations

import re

DEFAULT_MIN_WORDS = 8

# Unfilled template text. Each of these is what a stub looks like.
PLACEHOLDER = re.compile(
    r"\b(?:todo|tbd|tbc|lorem ipsum|your text here|fill (?:this )?in)\b"
    r"|\[(?:\.\.\.|…|insert[^\]]*|your [^\]]*|[^\]]{0,24} here)\]"
    r"|<(?:insert|your|name|client)[^>]*>"
    r"|_{3,}"
    r"|\bx{3,}\b",
    re.I,
)

_NUMBER_WORDS = (
    r"one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|thirty|forty|fifty|"
    r"hundred|thousand|dozen|half|once|twice"
)

# Words that start with a capital but are products, places in the app or months,
# so they do not show that a person was named.
_NOT_A_PERSON = {
    "hermes", "nous", "research", "field", "academy", "kanban", "mcp", "ssh", "cron", "docker", "telegram",
    "slack", "teams", "microsoft", "google", "gmail", "outlook", "notion", "github", "linux", "mac", "macos",
    "windows", "chrome", "safari", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "january", "february", "march", "april", "june", "july", "august", "september", "october", "november",
    "december", "the", "this", "that", "they", "then", "there", "when", "what", "who", "why", "how", "our",
    "your", "his", "her", "its", "and", "but", "for", "with", "from", "into", "out", "all", "any", "one",
    "two", "yes", "not", "none", "see", "use", "add", "new", "old", "set", "run", "ask", "per", "api",
    "gateway", "profile", "session", "skill", "cloud", "client", "owner", "price", "scope", "status",
}

NEEDS = {
    "number": (re.compile(rf"\d|\b(?:{_NUMBER_WORDS})\b", re.I), "a number"),
    "money": (
        re.compile(r"[$£€]\s?\d|\b\d[\d,.]*\s*(?:dollars?|usd|euros?|pounds?)\b|\b\d+\s?k\b|\bper (?:hour|month|week|year|seat)\b", re.I),
        "a price or a cost in money",
    ),
    "time": (
        re.compile(
            rf"\b(?:\d+|{_NUMBER_WORDS}|an?|several|few)[\s-]*(?:seconds?|minutes?|mins?|hours?|hrs?|days?|weeks?|months?|years?|percent)\b"
            r"|\d\s*%"
            r"|\b(?:daily|weekly|monthly|hourly|nightly|every (?:day|week|month|hour|morning|night|friday|monday))\b"
            r"|\b\d{1,2}:\d{2}\b|\b\d{1,2}\s?(?:am|pm)\b",
            re.I,
        ),
        "an amount of time or how often",
    ),
    "name": (None, "a person's name"),
    "list": (None, "at least two separate items"),
    "verdict": (re.compile(r"\b(?:met|not met|partly|partially|failed|passed|missed|yes|no)\b", re.I), "a verdict"),
    "decision": (re.compile(r"^\W*(?:yes|later|no)\b", re.I), "a decision (yes, later or no) as the first word"),
}


def words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9$%'’-]+", text)


def has_name(text: str) -> bool:
    """A name-shaped word: a capital letter in the middle of a sentence, or two capitalised words in a row.

    It cannot tell Priya from Prague. It tells a document that names someone from
    one that says "the owner", which is the gap the check is for.
    """
    text = re.sub(r"\b(Mr|Mrs|Ms|Dr|Prof)\.", r"\1", text)
    tokens = re.findall(r"[A-Za-z][A-Za-z'’-]*|[.!?:;\n]", text)
    sentence_start = True
    previous_capital = False
    for token in tokens:
        if token in ".!?:;\n":
            sentence_start = True
            previous_capital = False
            continue
        if token in ("Mr", "Mrs", "Ms", "Dr", "Prof"):
            # A title says a name is coming; the next capital word is it.
            previous_capital = True
            sentence_start = False
            continue
        capital = token[0].isupper() and len(token) >= 3 and token.lower() not in _NOT_A_PERSON and not token.isupper()
        if capital and (not sentence_start or previous_capital):
            return True
        previous_capital = capital
        sentence_start = False
    return False


def list_items(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if re.match(r"\s*(?:[-*•]|\d+[.)])\s+\S", line)]


def has_need(kind: str, body: str) -> bool:
    if kind == "name":
        return has_name(body)
    if kind == "list":
        return len(list_items(body)) >= 2
    pattern, _ = NEEDS[kind]
    return bool(pattern.search(body))


def need_words(kind: str) -> str:
    return NEEDS[kind][1]


def _heading_pattern(heading: str) -> re.Pattern[str]:
    escaped = re.escape(heading)
    return re.compile(
        rf"^\s{{0,3}}(?:#{{1,6}}\s*|[-*]\s+|\d+[.)]\s+)?(?:\*\*|__)?{escaped}(?:\*\*|__)?"
        rf"(?:\s*[:–—-]\s*(?P<rest>.*)|\s*(?P<paren>\(.*\))?\s*)$",
        re.I,
    )


def sections(text: str, headings: list[str]) -> dict[str, str | None]:
    """Each required heading's body, or None when the heading isn't there.

    A heading is a line that starts with the heading's words, optionally after
    #, a bullet or bold marks. Its body runs to the next required heading or the
    next Markdown heading of any kind.
    """
    lines = text.splitlines()
    patterns = {heading: _heading_pattern(heading) for heading in headings}
    found: dict[str, tuple[int, str]] = {}
    for index, line in enumerate(lines):
        for heading, pattern in patterns.items():
            if heading in found:
                continue
            match = pattern.match(line)
            if match:
                found[heading] = (index, (match.groupdict().get("rest") or "").strip())
    starts = sorted(index for index, _ in found.values())
    out: dict[str, str | None] = {}
    for heading in headings:
        if heading not in found:
            out[heading] = None
            continue
        index, rest = found[heading]
        stop = len(lines)
        for later in range(index + 1, len(lines)):
            if later in starts or re.match(r"\s{0,3}#{1,6}\s+\S", lines[later]):
                stop = later
                break
        body = "\n".join([rest] + lines[index + 1:stop]).strip()
        out[heading] = body
    return out


def _normal(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", text.lower()).split())


def shingles(text: str, size: int = 5) -> set[tuple[str, ...]]:
    tokens = _normal(text).split()
    return {tuple(tokens[i:i + size]) for i in range(max(0, len(tokens) - size + 1))}


def copied_share(text: str, models: list[str]) -> float:
    """The share of this document's five-word runs that also sit in a model document."""
    mine = shingles(text)
    if len(mine) < 10:
        return 0.0
    best = 0.0
    for model in models:
        theirs = shingles(model)
        if theirs:
            best = max(best, len(mine & theirs) / len(mine))
    return best


def _numbered(body: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^\s*(?:\d+[.)]|[-*•])\s+(.+)$", body, re.M)]


def check_criteria(found: dict[str, str | None]) -> list[dict[str, str]]:
    """The capstone's cross-check: what you said would count as success, and what you found.

    Needs three or more criteria, each a real sentence, most of them measurable,
    and one evidence line per criterion that carries a verdict.
    """
    problems: list[dict[str, str]] = []
    criteria_body = found.get("Criteria") or ""
    evidence_body = found.get("Evidence") or ""
    criteria = _numbered(criteria_body)
    if len(criteria) < 3:
        problems.append({
            "id": "criteria_count",
            "what": f'The Criteria section lists {len(criteria)} items. List at least three, one per line, starting each with a number.',
        })
    thin = [c for c in criteria if len(words(c)) < 4]
    if criteria and thin:
        problems.append({"id": "criteria_thin", "what": f'Criterion "{thin[0][:50]}" is too short to test. Say what you would see when it is met.'})
    measurable = [c for c in criteria if has_need("number", c) or has_need("time", c)]
    if len(criteria) >= 3 and len(measurable) < 2:
        problems.append({
            "id": "criteria_measurable",
            "what": "Fewer than two criteria carry a number or an amount of time. A criterion you can't count can't fail.",
        })
    evidence = _numbered(evidence_body)
    if len(criteria) >= 3 and len(evidence) < len(criteria):
        problems.append({
            "id": "evidence_count",
            "what": f"You listed {len(criteria)} criteria and {len(evidence)} pieces of evidence. Write one numbered evidence line for each criterion.",
        })
    without_verdict = [e for e in evidence if not has_need("verdict", e)]
    if evidence and without_verdict:
        problems.append({
            "id": "evidence_verdict",
            "what": f'The evidence line "{without_verdict[0][:50]}" gives no verdict. End each line with met, partly met or not met.',
        })
    return problems


def analyze(text: str, step: dict, models: list[str] | None = None) -> dict:
    """Check a document against a gate step. Returns misses, never a verdict word.

    ``step`` carries ``sections`` (the rules) and may carry ``cross``. ``models``
    are the worked and partial examples; a document that is mostly one of them
    is the example, so it fails.
    """
    rules = step.get("sections") or []
    names = [rule["heading"] for rule in rules]
    found = sections(text, names)
    missing: list[dict[str, str]] = []
    word_total = 0
    bodies: list[tuple[str, str]] = []
    for rule in rules:
        heading = rule["heading"]
        body = found[heading]
        if body is None:
            missing.append({
                "id": f"section:{heading}",
                "what": f'There is no "{heading}" section. Add a heading called {heading} and write it underneath.',
            })
            continue
        count = len(words(body))
        word_total += count
        bodies.append((heading, body))
        floor = int(rule.get("min_words", DEFAULT_MIN_WORDS))
        if count < floor:
            missing.append({
                "id": f"section:{heading}",
                "what": f'"{heading}" has {count} {"word" if count == 1 else "words"}. It needs at least {floor}: {rule.get("what", "say it in full")}.',
            })
            continue
        stub = PLACEHOLDER.search(body)
        if stub:
            missing.append({
                "id": f"section:{heading}",
                "what": f'"{heading}" still has placeholder text ("{stub.group(0)[:30]}"). Replace it with your own.',
            })
            continue
        for kind in rule.get("needs", []):
            if not has_need(kind, body):
                missing.append({
                    "id": f"section:{heading}",
                    "what": f'"{heading}" has no {need_words(kind)}. {rule.get("fix") or f"Add {need_words(kind)}."}',
                })
                break
    seen: dict[str, str] = {}
    for heading, body in bodies:
        key = _normal(body)
        if len(key) > 20 and key in seen:
            missing.append({
                "id": "duplicate",
                "what": f'"{heading}" says exactly what "{seen[key]}" says. Each section answers a different question.',
            })
            break
        seen.setdefault(key, heading)
    all_words = [w.lower() for _, body in bodies for w in words(body)]
    if len(all_words) >= 40 and len(set(all_words)) / len(all_words) < 0.3:
        missing.append({
            "id": "repetition",
            "what": "The same few words repeat all the way through. Write each section out in its own words.",
        })
    if step.get("cross") == "criteria" and not any(m["id"].startswith("section:") for m in missing):
        missing.extend(check_criteria(found))
    share = copied_share(text, models or [])
    if share > 0.5:
        missing.append({
            "id": "copied",
            "what": f"About {round(share * 100)} percent of this is the example, word for word. Write yours about your own case.",
        })
    return {
        "found": sum(1 for value in found.values() if value is not None),
        "total": len(names),
        "words": word_total,
        "missing": missing,
        "sections": {heading: body for heading, body in bodies},
    }
