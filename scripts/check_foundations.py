#!/usr/bin/env python3
"""Validate Foundations missions (content/foundations/) against ENGINEERING-PLAN section 4.

    python3 scripts/check_foundations.py
    python3 scripts/check_foundations.py --dir path/to/missions --tests tests
    HERMES_SOURCE=~/hermes-agent python3 scripts/check_foundations.py     # also check every "as of Hermes" fact
    HERMES_SOURCE=~/hermes-agent python3 scripts/check_foundations.py --hermes-ref v0.23.0   # ...at a release tag

Rules: the idea is 800-1,200 words per TEACHING-STANDARD (fails under 600, warns under 800 and over 1,300); the expert run has 4 or more
steps, each with Did, Saw, Noticed and Ruled out; the standard has 3-5 checks, each proved by a live check of the
mission or the rubric; every reader is registered and has a fixture test; every planted problem has a planter, a
detector and a fix-verifier; the rubric has exactly four levels and a pass level of 2-4; a transfer task and an
expected cost are present; and the voice rules of docs/curriculum-voice.md hold (scripts/check_content.py).

With HERMES_SOURCE (or --hermes-source) set, every ``as_of`` pattern must still match its file in that Hermes source
tree. A miss fails: the lesson says something Hermes no longer does. The first catch was sessions.auto_prune turning
off by default between Hermes 0.22.2 and 0.22.4. Reading the source is all it does; it never runs Hermes.

scripts/check_content.py stays as it is for the four paths.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Notes for the authors that must never reach a learner: interview slots, build notes, stamps, and meta headers about
# how the lesson was written (review 2, Oct 22).
MARKERS = re.compile(r"\[(?:DAMON|BUILD|STAMP)\b", re.I)
META = re.compile(r"(?im)^\s*(?:#+\s*)?(?:build notes|changed from the first draft|facts re-checked|rewritten oct|draft for|todo\b)"
                  r"|TEACHING-STANDARD|ENGINEERING-PLAN|SAMPLE-MISSION|\.planning/")
PROOF = re.compile(r"^(?:live:([\w.-]+)|rubric:explain|live:([\w.-]+)\+rubric:explain)$")


def _package():
    os.environ.setdefault("FIELD_ACADEMY_DATA_DIR", tempfile.mkdtemp(prefix="fa-foundations-check-"))
    package = sys.modules.get("fa_foundations_check")
    if package is None:
        package = types.ModuleType("fa_foundations_check")
        package.__path__ = [str(ROOT)]
        sys.modules["fa_foundations_check"] = package
    from importlib import import_module

    return (import_module("fa_foundations_check.foundations_content"), import_module("fa_foundations_check.foundations_checks"),
            import_module("fa_foundations_check.plants"))


def _voice():
    spec = importlib.util.spec_from_file_location("fa_check_content_voice", ROOT / "scripts" / "check_content.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.NEGATION, module.EMOJI


def words(text) -> int:
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’.-]*", str(text or "")))


def _prose(mission) -> list:
    out = [("title", mission.get("title", "")), ("claim", (mission.get("claim") or {}).get("text", "")),
           ("lab", (mission.get("lab") or {}).get("body", "")), ("transfer", (mission.get("transfer") or {}).get("body", "")),
           ("explain", (mission.get("explain") or {}).get("question", "")), ("idea", mission.get("_idea_text", "")),
           ("expert", mission.get("_expert_text", "")), ("try", mission.get("_try_text", "")),
           ("lab checks", (mission.get("lab") or {}).get("checks_text", "")), ("record example", mission.get("_record_example", "")),
           ("expert lead", mission.get("expert_lead", ""))]
    out += [(f"seed note {n}", note.get("text", "")) for n, note in enumerate((mission.get("lab") or {}).get("seed_notes") or [], start=1)]
    out += [(f"standard {c.get('id')}", c.get("text", "")) for c in mission.get("standard", [])]
    out += [(f"rubric {k}", v) for k, v in ((mission.get("explain") or {}).get("rubric") or {}).items()]
    return out


def broken_list(text) -> str:
    """A bold-led line followed straight by '- ' items: the first item of a list lost its marker, so it renders as a
    paragraph above the list. Returns that line, or ""."""
    lines = str(text or "").split("\n")
    for i, line in enumerate(lines):
        if not line.startswith("**") or re.match(r"\*\*\d+\.", line):
            continue
        j = i + 1
        while j < len(lines) and lines[j].startswith("  "):
            j += 1
        if j < len(lines) and lines[j].startswith("- "):
            return line
    return ""


def check_mission(mission, readers, registry, negation, emoji, tested, problems, warnings):
    mid = mission.get("id", "?")

    def bad(message):
        problems.append(f"{mid}: {message}")

    if not str(mid).startswith("f."):
        bad("the id must start with f.")
    # An assessment mission (kind "review", mission 11) has no worked example and no taught idea of its own length.
    review = mission.get("kind") == "review"
    for key in ("title", "level", "minutes", "cost", "idea", "expert", "lab", "live_checks", "explain", "transfer", "standard", "claim"):
        if not mission.get(key) and not (review and key == "expert"):
            bad(f"{key} is missing")
    cost = mission.get("cost") or {}
    if mission.get("cost") and not (cost.get("chats") and cost.get("words")):
        bad("cost needs the number of chats and the expected fee in words")
    count = words(mission.get("_idea_text"))
    if review:
        pass
    elif count < 600:
        bad(f"the idea has {count} words; it needs 800 to 1,200")
    elif count < 800:
        warnings.append(f"{mid}: the idea has {count} words; aim for 800 to 1,200")
    elif count > 1300:
        warnings.append(f"{mid}: the idea has {count} words; aim for 800 to 1,200")
    steps = mission.get("_expert_steps") or []
    for label, text in (("idea", mission.get("_idea_text", "")), ("try", mission.get("_try_text", "")), ("expert", mission.get("_expert_text", ""))):
        line = broken_list(text)
        if line:
            bad(f"the {label} has a list whose first item lost its '- ': {line[:60]}")
    if len(steps) < 4 and not review:
        bad(f"the expert run has {len(steps)} steps; it needs 4 or more")
    for n, step in enumerate(steps, start=1):
        for key, label in (("did", "did"), ("saw", "saw"), ("noticed", "noticed"), ("ruled_out", "ruled out")):
            if not step.get(key):
                bad(f"expert step {n} has no '{label}' line")
    live = {c.get("id"): c for c in mission.get("live_checks", [])}
    for check in mission.get("live_checks", []):
        if check.get("reader") not in readers:
            bad(f"live check {check.get('id')} uses reader {check.get('reader')}, which is not registered")
    standard = mission.get("standard", [])
    if not 3 <= len(standard) <= 5:
        bad(f"the standard has {len(standard)} checks; it needs 3 to 5")
    for check in standard:
        match = PROOF.match(str(check.get("proves_by", "")))
        if not match:
            bad(f"standard {check.get('id')} has no valid proves_by")
            continue
        ref = match.group(1) or match.group(2)
        if ref and ref not in live:
            bad(f"standard {check.get('id')} is proved by live:{ref}, which is not a live check")
    lab = mission.get("lab") or {}
    kinds = lab.get("plants") or []
    for kind in kinds:
        parts = registry.get(kind) or {}
        if set(parts) != {"plant", "detect", "verify"}:
            bad(f"planted problem {kind} needs a planter, a detector and a fix-verifier")
    for level, n in (lab.get("plants_at") or {}).items():
        if not isinstance(n, int) or not 1 <= n <= max(1, len(kinds)):
            bad(f"plants_at {level} must be 1 to {len(kinds)}")
    seeds = lab.get("seed_notes") or []
    params = lab.get("seed_params") or {}
    if seeds:
        raw = [str(n.get("text", "")) for n in seeds if isinstance(n, dict)]
        if len(raw) != len(seeds) or not all(raw):
            bad("each seed note needs its text")
        for text in raw:
            for name in re.findall(r"\{([a-z_]+)\}", text):
                if not params.get(name):
                    bad(f"a seed note names {{{name}}}, which seed_params doesn't give choices for")
        # Lengths are judged with the longest choice of every parameter.
        longest = {k: max((str(v) for v in vals), key=len) for k, vals in params.items() if vals}

        def fill(text):
            return re.sub(r"\{([a-z_]+)\}", lambda m: longest.get(m.group(1), m.group(0)), text)

        texts = [fill(text) for text in raw]
        seeds = [dict(n, text=fill(str(n.get("text", "")))) for n in seeds if isinstance(n, dict)]
        draw = lab.get("seed_draw") or {}
        keys = sorted((len(str(n.get("text", ""))) for n in seeds if isinstance(n, dict) and n.get("key")), reverse=True)
        others = sorted((len(str(n.get("text", ""))) for n in seeds if isinstance(n, dict) and not n.get("key")), reverse=True)
        if draw and (int(draw.get("key", 0)) > len(keys) or int(draw.get("other", 0)) > len(others) or int(draw.get("key", 0)) < 1):
            bad("seed_draw asks for more notes than the pool has, or for no protected note")
        worst = sum(keys[:int(draw.get("key", len(keys)))]) + sum(others[:int(draw.get("other", len(others)))]) if draw else sum(len(t) for t in texts)
        if worst > 900:
            bad("the seed notes can take more than 900 characters; they should leave most of memory free")
        if any(len(t) > 240 or "\n" in t for t in texts):
            bad("a seed note must be one short line")
        if not any(n.get("key") for n in seeds if isinstance(n, dict)):
            bad("the seed notes need at least one key note the practice jobs rely on")
    if mission.get("try") and not mission.get("_try_text", "").strip():
        bad(f"the try file {mission.get('try')} is missing or empty")
    explain = mission.get("explain") or {}
    rubric = explain.get("rubric") or {}
    if sorted(str(k) for k in rubric) != ["1", "2", "3", "4"] or not all(str(v).strip() for v in rubric.values()):
        bad("the rubric needs exactly four levels, 1 to 4, each described")
    if explain.get("pass_level") not in (2, 3, 4):
        bad("the rubric's pass_level must be 2, 3 or 4")
    transfer = mission.get("transfer") or {}
    if not transfer.get("body") or not transfer.get("live_checks"):
        bad("the transfer task needs a body and its live checks")
    for check_id in transfer.get("live_checks") or []:
        if check_id not in live:
            bad(f"the transfer names {check_id}, which is not a live check")
    for where, text in _prose(mission):
        for pattern in negation:
            hit = pattern.search(str(text or ""))
            if hit:
                bad(f"voice (negation device or filler) in {where}: {hit.group(0)[:60]!r}")
        if emoji.search(str(text or "")):
            bad(f"voice (emoji) in {where}")
        marker = MARKERS.search(str(text or ""))
        if marker:
            bad(f"an author's note ({marker.group(0)}...) in {where}; it must not reach a learner")
        meta = META.search(str(text or ""))
        if meta:
            bad(f"a note about how the lesson was made ({meta.group(0).strip()[:40]!r}) in {where}")
    for item in mission.get("as_of") or []:
        if not all(item.get(k) for k in ("fact", "file", "pattern", "since")):
            bad("each as_of entry needs fact, file, pattern and since")


def source_reader(source: Path, ref: str = ""):
    """A function that returns one file of the Hermes source as text, or None. With ``ref`` (a tag such as v0.23.0, the
    release learners run) the file is read from git's objects with ``git show``, so a checkout on a newer branch can
    check the release without switching branches. Reading is all it does; it never runs Hermes."""
    if not ref:
        def read(rel):
            try:
                return (source / rel).read_text(encoding="utf-8")
            except OSError:
                return None
        return read
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+/-]{0,80}", ref):
        raise SystemExit(f"not a git ref: {ref!r}")

    def read(rel):
        import subprocess
        if not re.fullmatch(r"[A-Za-z0-9_./-]{1,200}", rel) or ".." in rel.split("/"):
            return None
        out = subprocess.run(["git", "-C", str(source), "show", f"{ref}:{rel}"], capture_output=True, timeout=30)
        return out.stdout.decode("utf-8") if out.returncode == 0 else None
    return read


def check_sources(missions, source: Path, problems, ref: str = "") -> int:
    matched = 0
    read = source_reader(source, ref)
    where = f"{source} at {ref}" if ref else str(source)
    for mission in missions.values():
        for item in mission.get("as_of") or []:
            text = read(item.get("file", ""))
            if text is None:
                problems.append(f"{mission['id']}: as of Hermes: {item.get('file')} is not in the Hermes source at {where}")
                continue
            if re.search(item["pattern"], text, re.M):
                matched += 1
            else:
                problems.append(f"{mission['id']}: as of Hermes {item.get('since')}: '{item['fact']}' no longer matches "
                                f"{item['file']} in the Hermes source at {where}. Check the lesson against Hermes.")
    return matched


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dir", default=str(ROOT / "content" / "foundations"))
    parser.add_argument("--tests", default=str(ROOT / "tests"))
    parser.add_argument("--hermes-source", default=os.environ.get("HERMES_SOURCE", ""))
    parser.add_argument("--hermes-ref", default=os.environ.get("HERMES_REF", ""),
                        help="check the as-of facts at this git ref of the Hermes source (for example v0.23.0)")
    args = parser.parse_args(argv)
    content, checks, plants = _package()
    content.clear_cache()
    missions = content.load_all(Path(args.dir))
    negation, emoji = _voice()
    tested = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in sorted(Path(args.tests).glob("*.py")))
    problems, warnings = [], []
    for reader_id in sorted(checks.READERS):
        if f'"""{reader_id}"""' not in tested:
            problems.append(f"reader {reader_id} has no fixture test (a test class whose docstring is the reader id)")
    for mission in missions.values():
        check_mission(mission, checks.READERS, plants.REGISTRY, negation, emoji, tested, problems, warnings)
    if args.hermes_source:
        matched = check_sources(missions, Path(args.hermes_source).expanduser(), problems, args.hermes_ref)
        at = f" at {args.hermes_ref}" if args.hermes_ref else ""
        print(f"{matched} as-of facts match the Hermes source at {args.hermes_source}{at}")
    for line in warnings:
        print(f"warning: {line}")
    for line in problems:
        print(line)
    print(f"{len(missions)} mission(s), {len(problems)} problem(s), {len(warnings)} warning(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
