"""Evidence that something ran over time, read from Hermes and judged here.

Two parts, kept apart on purpose.

The judging part is pure: it takes a list of timestamps and says whether they
show a deployment that ran for several days, or a drill that went wrong and was
recovered. It never touches a file, so it can be tested with made-up times.

The reading part collects timestamps without ever writing: from what the desktop
half reads off Hermes's own scheduler list, from Hermes's run history file when
one is there, and from Hermes's log files. Every read is bounded in size and
count, opens files for reading only, and keeps only timestamps and counts, never
a prompt, a message or a secret. Nothing in this file runs a program, starts a
job, or changes anything in the learner's Hermes. A test fails if a write call
appears in this file.

What could not be verified when this was written: the exact layout of Hermes's
run history and logs. The sources below read whatever shape they find and say so
when they find nothing, instead of guessing. Where Hermes state cannot be read,
the result says that on screen and the learner falls back to a packet an expert
reviewer checks. Self-attestation alone never passes (see deployer.py).
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

ISO = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?")
MAX_TIMES = 2000
MAX_FILES = 25
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_ROWS = 20000
EPOCH_LOW, EPOCH_HIGH = 1_500_000_000, 2_500_000_000

# Words that mark a failed run, in a status column or a log line.
FAILED = re.compile(r"\b(?:fail(?:ed|ure)?|error|errored|exception|timeout|timed out|denied|unauthori[sz]ed|forbidden|revoked|rate[- ]?limit(?:ed)?|429|401|403)\b", re.I)

# Secret shapes removed from any pasted excerpt before it is kept.
SECRET_SHAPES = (
    re.compile(r"\b(?:sk|pk|rk|ghp|gho|xox[abp])[-_][A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}", re.I),
    re.compile(r"\b[A-Za-z0-9+/=_-]{40,}\b"),
    re.compile(r"(?i)\b(?:api[_-]?key|token|secret|password)\s*[=:]\s*\S+"),
)


def parse_ts(value) -> datetime | None:
    """An ISO string or an epoch number as an aware UTC time, or None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        if number > EPOCH_HIGH * 100:
            number /= 1000.0
        if EPOCH_LOW <= number <= EPOCH_HIGH:
            return datetime.fromtimestamp(number, tz=timezone.utc)
        return None
    if isinstance(value, str):
        match = ISO.search(value)
        if not match:
            return None
        text = match.group(0).replace(" ", "T")
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            moment = datetime.fromisoformat(text)
        except ValueError:
            return None
        return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)
    return None


def times_in(text: str) -> list:
    out = []
    for match in ISO.finditer(text or ""):
        moment = parse_ts(match.group(0))
        if moment:
            out.append(moment)
    return out


def iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def redact(text: str, limit: int = 8000) -> str:
    out = text or ""
    for pattern in SECRET_SHAPES:
        out = pattern.sub("[removed]", out)
    return out[:limit]


# ---------------------------------------------------------------- judging --


def _outcome(passed, title, detail, missing, facts, readable=True):
    return {"passed": bool(passed), "title": title, "detail": detail, "missing": missing, "facts": facts, "readable": readable}


def _miss(id_, what):
    return {"id": id_, "what": what}


def clean_times(raw, now: datetime) -> list:
    """Parse, drop the impossible (the future, before 2020), sort and cap."""
    out = []
    for item in raw or []:
        moment = item if isinstance(item, datetime) else parse_ts(item)
        if moment is None:
            continue
        if moment > now + timedelta(minutes=5) or moment.year < 2020:
            continue
        out.append(moment)
    return sorted(set(out))[-MAX_TIMES:]


def unreadable(what: str):
    """The result when Hermes state could not be read. It names the fallback and never passes."""
    return _outcome(
        False,
        "Field Academy could not read this from Hermes",
        what + " Field Academy cannot check this by itself, and it will not take your word for it. Add your own log excerpt to the review packet instead: an expert reviewer checks it and signs off.",
        [_miss("unreadable", what)],
        [],
        readable=False,
    )


def analyze_run_history(times, *, since: datetime, now: datetime, min_runs: int = 5, min_days: int = 3, min_span_hours: int = 48, failed=None) -> dict:
    """Did a job run, on its own, across several days after the learner started the clock?"""
    runs = [t for t in clean_times(times, now) if t >= since]
    bad = [t for t in clean_times(failed or [], now) if t >= since]
    if not runs and not bad:
        return unreadable("Hermes showed no run times for this job since you started.")
    facts = []
    missing = []
    days = sorted({t.date() for t in runs})
    span = (runs[-1] - runs[0]) if len(runs) > 1 else timedelta(0)
    facts.append({"label": "Runs seen since you started", "value": str(len(runs))})
    facts.append({"label": "Different days", "value": str(len(days))})
    facts.append({"label": "Time from first to last run", "value": f"{int(span.total_seconds() // 3600)} hours"})
    if len(runs) < min_runs:
        missing.append(_miss("few_runs", f"Hermes shows {len(runs)} {'run' if len(runs) == 1 else 'runs'} since you started. The check needs at least {min_runs}."))
    if len(days) < min_days:
        missing.append(_miss("few_days", f"The runs fall on {len(days)} {'day' if len(days) == 1 else 'days'}. They need to span at least {min_days} different days."))
    if span < timedelta(hours=min_span_hours):
        missing.append(_miss("short_span", f"The first and last runs are {int(span.total_seconds() // 3600)} hours apart. Let it run for at least {min_span_hours} hours."))
    if runs and (runs[-1] - runs[0]) > timedelta(0) and len({t.replace(second=0, microsecond=0) for t in runs}) < max(2, len(runs) // 2):
        missing.append(_miss("clustered", "Most of the runs have the same minute. A real scheduled job runs on its own schedule, spread over time."))
    if bad and len(bad) > len(runs):
        missing.append(_miss("mostly_failed", "More runs failed than succeeded. Fix the failures, then let it run again."))
    if len(runs) >= 2 and now - runs[-1] > timedelta(days=3):
        missing.append(_miss("stopped", "The last run was more than 3 days ago. A deployment you manage is still running."))
    passed = not missing
    return _outcome(
        passed,
        "It ran over several days" if passed else "Not enough run history yet",
        "Hermes's own record shows the job ran on its schedule across several days." if passed else missing[0]["what"],
        missing,
        facts,
    )


def analyze_recovery(times, *, started: datetime, ended: datetime | None, now: datetime, failed=None) -> dict:
    """Did a drill leave a visible gap, and then a run that worked after the fix?"""
    if ended is None:
        return _outcome(False, "The drill is still open", "Say when you fixed it, then check again.", [_miss("open", "You have not said you recovered yet.")], [])
    runs = clean_times(times, now)
    bad = clean_times(failed or [], now)
    if not runs and not bad:
        return unreadable("Hermes showed no run times around your drill.")
    before = [t for t in runs if t <= started]
    during = [t for t in runs if started < t <= ended]
    after = [t for t in runs if t > ended]
    failed_during = [t for t in bad if started - timedelta(minutes=1) <= t <= ended + timedelta(minutes=5)]
    elapsed = ended - started
    missing = []
    facts = [
        {"label": "Runs before the drill", "value": str(len(before))},
        {"label": "Runs during the drill", "value": str(len(during))},
        {"label": "Failed runs during the drill", "value": str(len(failed_during))},
        {"label": "Runs after you recovered", "value": str(len(after))},
    ]
    if len(before) < 2:
        missing.append(_miss("no_before", "The check needs at least two runs before the drill, to see how often the job normally runs."))
    interval = None
    if len(before) >= 2:
        gaps = sorted((b2 - a2).total_seconds() for a2, b2 in zip(before[-7:], before[-6:]))
        interval = gaps[len(gaps) // 2]
        facts.append({"label": "Usual time between runs", "value": f"{int(interval // 60)} minutes"})
    if elapsed < timedelta(minutes=2):
        missing.append(_miss("too_quick", "The drill lasted under 2 minutes. Leave it broken long enough for a scheduled run to miss."))
    elif during and not failed_during:
        missing.append(_miss("no_gap", f"{len(during)} {'run' if len(during) == 1 else 'runs'} still succeeded while you say it was broken, so no gap shows. Check that the drill really broke the job."))
    elif interval and not failed_during and elapsed.total_seconds() < interval * 0.9:
        missing.append(_miss("too_short", "The drill was shorter than the usual time between runs, so no scheduled run had to miss. Keep it broken through at least one scheduled run."))
    if not after:
        missing.append(_miss("no_recovery", "No run after you recovered. Wait for the next scheduled run, then check again."))
    if ended > now:
        missing.append(_miss("future", "The recovery time is in the future."))
    passed = not missing
    return _outcome(
        passed,
        "The gap and the recovery both show" if passed else "The drill is not proven yet",
        "Hermes's run history shows it working, a gap while it was broken, and a run after you recovered." if passed else missing[0]["what"],
        missing,
        facts,
    )


# ---------------------------------------------------------------- reading --


def _ro_connect(path: Path):
    """Open a SQLite file read-only and immutable, so no journal or lock file is made beside it."""
    uri = f"file:{quote(path.as_posix())}?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True, timeout=1)
    conn.execute("PRAGMA query_only = ON")
    return conn


def read_run_history(home, job_name: str, now: datetime) -> dict:
    """Timestamps for one job from a Hermes run-history database, if there is one. Read only.

    The database's layout was not verified. This reads every table it finds,
    keeps rows that mention the job (by name, or by the job's id from jobs.json),
    and keeps only the times in those rows and whether the row looks failed.
    """
    home = Path(home)
    candidates = [home / "cron" / "executions.db", home / "cron" / "runs.db", home / "executions.db"]
    db = next((p for p in candidates if p.is_file()), None)
    out = {"source": "history", "found": False, "times": [], "failed": [], "tables": []}
    if db is None:
        return out
    needles = {job_name.lower()}
    for rel in ("jobs.json", "cron/jobs.json"):
        path = home / rel
        if path.is_file() and path.stat().st_size < MAX_FILE_BYTES:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            items = data.get("jobs", data) if isinstance(data, dict) else data
            for job in items if isinstance(items, list) else []:
                if isinstance(job, dict) and str(job.get("name", "")).lower() == job_name.lower() and job.get("id"):
                    needles.add(str(job["id"]).lower())
    try:
        conn = _ro_connect(db)
    except sqlite3.Error:
        return out
    try:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
        for table in tables[:30]:
            try:
                rows = conn.execute(f'SELECT * FROM "{table}" LIMIT {MAX_ROWS}').fetchall()
            except sqlite3.Error:
                continue
            kept = 0
            for row in rows:
                text = " ".join(str(v).lower() for v in row if isinstance(v, str))
                if not any(n in text or any(str(v).lower() == n for v in row) for n in needles):
                    continue
                stamps = [m for m in (parse_ts(v) for v in row) if m]
                if not stamps:
                    continue
                kept += 1
                bucket = out["failed"] if FAILED.search(text) else out["times"]
                bucket.extend(stamps[:1])
            if kept:
                out["tables"].append(table)
    except sqlite3.Error:
        pass
    finally:
        conn.close()
    out["found"] = bool(out["times"] or out["failed"])
    out["times"] = [iso(t) for t in clean_times(out["times"], now)]
    out["failed"] = [iso(t) for t in clean_times(out["failed"], now)]
    return out


def read_logs(home, job_name: str, now: datetime) -> dict:
    """Timestamps of log lines that mention the job, from Hermes's log folder. Read only, bounded, lines never kept."""
    folder = Path(home) / "logs"
    out = {"source": "logs", "found": False, "times": [], "failed": [], "files": 0}
    if not folder.is_dir():
        return out
    needle = job_name.lower()
    files = sorted((p for p in folder.iterdir() if p.is_file() and p.suffix in (".log", ".txt", "")), key=lambda p: p.stat().st_mtime, reverse=True)[:MAX_FILES]
    for path in files:
        if path.stat().st_size > MAX_FILE_BYTES * 4:
            continue
        out["files"] += 1
        with path.open("rb") as handle:
            raw = handle.read(MAX_FILE_BYTES)
        for line in raw.decode("utf-8", errors="replace").splitlines():
            if needle not in line.lower():
                continue
            stamps = times_in(line)
            if not stamps:
                continue
            (out["failed"] if FAILED.search(line) else out["times"]).append(stamps[0])
    out["found"] = bool(out["times"] or out["failed"])
    out["times"] = [iso(t) for t in clean_times(out["times"], now)]
    out["failed"] = [iso(t) for t in clean_times(out["failed"], now)]
    return out


def collect(home, job_name: str, now: datetime) -> dict:
    """Every read-only source at once. Returns merged times and which sources said anything."""
    sources = [read_run_history(home, job_name, now), read_logs(home, job_name, now)]
    times = sorted({t for s in sources for t in s["times"]})
    failed = sorted({t for s in sources for t in s["failed"]})
    return {
        "times": times,
        "failed": failed,
        "sources": [{"source": s["source"], "found": s["found"]} for s in sources],
        "found": any(s["found"] for s in sources),
    }


def excerpt_summary(text: str, now: datetime) -> dict:
    """What can be said about a log excerpt the learner pasted: how many timestamps, over how many days. Never a pass."""
    stamps = clean_times(times_in(text), now)
    return {
        "times": [iso(t) for t in stamps],
        "count": len(stamps),
        "days": len({t.date() for t in stamps}),
        "first": iso(stamps[0]) if stamps else "",
        "last": iso(stamps[-1]) if stamps else "",
    }


# --------------------------------------------------------------- versions --

_VERSION = re.compile(r"v?(\d+)(?:\.(\d+))?(?:\.(\d+))?")


def parse_version(text: str):
    match = _VERSION.search(str(text or ""))
    if not match:
        return None
    return tuple(int(g) if g else 0 for g in match.groups())


def version_series(text: str) -> str:
    """The part of a version that marks a breaking change: the major number, or the minor while the major is 0."""
    parts = parse_version(text)
    if not parts:
        return ""
    return f"{parts[0]}" if parts[0] > 0 else f"0.{parts[1]}"


def reverify_status(earned_on: str, current: str) -> dict:
    """Current, or re-verify needed, or unknown. Compared by series, so a patch release never expires a Field Record."""
    if not earned_on:
        return {"status": "unknown", "words": "The Field Record does not record a Hermes version."}
    if not current:
        return {"status": "unknown", "words": "Field Academy could not read the Hermes version in use, so it cannot say whether this Field Record is current."}
    if version_series(earned_on) == version_series(current):
        return {"status": "current", "words": f"Recorded on Hermes {earned_on}. Still the same series as {current}."}
    return {"status": "reverify", "words": f"Re-verify needed. Recorded on Hermes {earned_on}, and this is Hermes {current}."}


def _stamp_version(stamp_path) -> str:
    """baseVersion from a Hermes install-stamp.json, or "" when it is missing or unreadable."""
    try:
        stamp = json.loads(Path(stamp_path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return ""
    value = stamp.get("baseVersion") if isinstance(stamp, dict) else ""
    return value.strip() if isinstance(value, str) and re.match(r"^\d+\.\d+", value.strip()) else ""


def detect_version() -> tuple:
    """The installed Hermes version, never by running Hermes. Returns (version, source) or ("", "").

    Hermes reports its version from install-stamp.json at the top of its checkout. The
    package metadata can lag behind it (0.21.5 in metadata on a 0.22.0 install, October
    2026), so the stamp comes first. find_spec locates the checkout without importing it.
    """
    try:
        import importlib.util

        spec = importlib.util.find_spec("hermes_cli")
    except (ImportError, ValueError):
        spec = None
    if spec is not None and spec.origin:
        found = _stamp_version(Path(spec.origin).resolve().parents[1] / "install-stamp.json")
        if found:
            return found, "install stamp"
    try:
        from importlib import metadata
    except ImportError:  # pragma: no cover
        return "", ""
    for name in ("hermes-agent", "hermes_agent", "hermes"):
        try:
            return metadata.version(name), f"package {name}"
        except metadata.PackageNotFoundError:
            continue
    return "", ""
