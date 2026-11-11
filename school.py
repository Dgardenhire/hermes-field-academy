"""The School of Hermes is the trail map: five trails up Mount Olympus from the Foundations trailhead, each climbing
Beginner, Intermediate, Advanced and Capstone camp to its summit flag.

This module adds nothing new to that system. It does three things with it:

* ``CAMP_LINES``: one plain line per column of the trail map, what you can do once you reach that camp on any trail.
* ``PLACEMENTS``: the capability and teaching missions (the practice-profile kind, like Foundations) placed in the
  camps where they fit, on the trails where they belong. They join their camp's waypoints on the map and its count on
  the path page. A path's own summit, its Field Record, keeps its own route, so nothing that was there before changes.
* ``trails``: camps reached per trail and summits, for the Foundations Field Record.

A placed mission that isn't in ``content/foundations`` yet is left out, so the map never shows a mission that can't
be started.
"""

from __future__ import annotations

import json

from .curriculum import where_of

CAMP_LINES = {
    "beginner": "See what Hermes is doing",
    "intermediate": "Fit it to the work",
    "advanced": "Let it run without you",
    "capstone": "Solve your own problem",
}
SUMMIT_LINE = "Your Field Record"
SCHOOL_LINE = "Get good at Hermes by using it, learn all of what it can do, then learn to help other people use it."

# mission id -> (trail, camp). Trails: ambassador = Messenger, operator = Traveler, integrator = Crossroads,
# architect = Boundary Keeper, deployer = Guide (whose camps are Audit, Architect, Build and Verify).
PLACEMENTS = {
    "f.messaging": ("integrator", "intermediate"),   # where a client's Hermes runs and how people reach it
    "f.toolsets": ("integrator", "intermediate"),    # connect a client's tools safely: only the tools the job needs
    "f.delegation": ("architect", "intermediate"),   # match each job to the right kind of agent
    "f.models": ("architect", "advanced"),           # show the setup is worth what it costs
    "f.teach-profile": ("deployer", "build"),        # set Hermes up for another person
    "f.teach-walkthrough": ("deployer", "verify"),   # a walkthrough they can follow on their own
    "f.teach-review": ("deployer", "verify"),        # judge their work from their Field Record
}


TRAIL_NAMES = {"ambassador": "Messenger", "operator": "Traveler", "integrator": "Crossroads", "architect": "Boundary Keeper",
               "deployer": "Guide"}
CAMP_NAMES = {"beginner": "Beginner", "intermediate": "Intermediate", "advanced": "Advanced", "capstone": "Capstone",
              "audit": "Audit", "architect": "Architect", "build": "Build", "verify": "Verify"}


def trail_of(mission_id: str) -> dict:
    """Where a placed mission sits: its trail and camp, by id and by name. Empty when it isn't placed."""
    if mission_id not in PLACEMENTS:
        return {}
    trail, camp = PLACEMENTS[mission_id]
    return {"id": trail, "name": TRAIL_NAMES.get(trail, trail), "camp": camp, "camp_name": CAMP_NAMES.get(camp, camp)}


def placed_on(track_id: str) -> list:
    return [(mid, camp) for mid, (trail, camp) in PLACEMENTS.items() if trail == track_id]


def _status(mission_id, passes, started) -> str:
    if mission_id in passes:
        return "verified"
    return "in_progress" if mission_id in started else "not_started"


def _rung_status(statuses) -> str:
    if statuses and all(s == "verified" for s in statuses):
        return "passed"
    return "started" if any(s != "not_started" for s in statuses) else "not_started"


def inject(track: dict, engine: dict, passes: dict, started: set) -> dict:
    """List this trail's placed missions on the track as ``placed``, in place. The path's own ``missions`` and
    ``levels`` stay exactly as the path built them; the page merges ``placed`` into the camps (trail.js withPlaced).
    ``engine``: mission id -> {title, minutes, order}."""
    placed = []
    for mid, camp in placed_on(track.get("id", "")):
        if mid not in engine:
            continue
        info = engine[mid]
        rung = next((r for r in track.get("levels") or [] if r.get("id") == camp), None)
        status = _status(mid, passes, started)
        minutes = info.get("minutes") or {}
        placed.append({"id": mid, "engine": "foundations", "where": where_of({"engine": "foundations"}), "title": info.get("title", ""), "status": status, "level": camp,
                       "level_name": rung.get("name", "") if rung else "",
                       "minutes": (minutes.get("read", 0) + minutes.get("do", 0)) if isinstance(minutes, dict) else 0,
                       "completed_steps": 1 if status == "verified" else 0, "total_steps": 1})
    track["placed"] = placed
    return track


def with_placed(track: dict) -> dict:
    """A copy of the track with its placed missions in their camps, counts and statuses made again. For the record."""
    placed = track.get("placed") or []
    if not placed:
        return track
    out = dict(track)
    out["missions"] = list(track.get("missions") or []) + [m for m in placed if m["id"] not in {x.get("id") for x in track.get("missions") or []}]
    by_id = {m["id"]: m for m in out["missions"]}
    levels = []
    for rung in track.get("levels") or []:
        ids = list(rung.get("missions") or []) + [m["id"] for m in placed if m["level"] == rung.get("id") and m["id"] not in (rung.get("missions") or [])]
        statuses = [by_id[i]["status"] for i in ids if i in by_id]
        levels.append({**rung, "missions": ids, "passed": sum(1 for x in statuses if x == "verified"), "total": len(statuses),
                       "status": _rung_status(statuses)})
    out["levels"] = levels
    return out


def trails(tracks) -> list:
    """Camps reached per trail, and the summit, for the Field Record."""
    out = []
    for track in tracks or []:
        track = with_placed(track)
        camps = [{"id": r.get("id", ""), "name": r.get("name", ""), "passed": int(r.get("passed") or 0), "total": int(r.get("total") or 0),
                  "reached": r.get("status") == "passed"} for r in track.get("levels") or []]
        cert = track.get("certificate") or {}
        by_id = {m.get("id"): m for m in track.get("missions") or []}
        passed = [{"title": by_id[i].get("title", ""), "camp": r.get("name", ""), "practice": by_id[i].get("engine") == "foundations"}
                  for r in track.get("levels") or [] for i in r.get("missions") or [] if by_id.get(i, {}).get("status") == "verified"]
        out.append({"id": track.get("id", ""), "name": track.get("name", ""), "eyebrow": track.get("eyebrow", ""), "camps": camps,
                    "summit": cert.get("status") == "issued", "passed": passed})
    return out


# ------------------------------------------------------------------ readers --


def record_passes() -> dict:
    """Mission id -> how it passed, from the Field Record entries the learner added."""
    from . import field_record, foundations

    out = {}
    with foundations._conn() as conn:
        rows = [r for r in field_record._rows(conn) if not r["corrects_id"]]
    for n, row in enumerate(rows, start=1):
        try:
            entry = field_record._entry(n, row, json.loads(row["body_json"]), set())
        except (ValueError, KeyError, TypeError):
            continue
        how = field_record._passed(entry)
        if how and (entry["mission"] not in out or how == "first"):
            out[entry["mission"]] = how
    return out


def engine_state():
    """(placed missions that exist, by id; their passes; the ones with a try started)."""
    from . import foundations, foundations_content

    missions = foundations_content.load_all(foundations.CONTENT_DIR)
    engine = {mid: {"title": m.get("title", ""), "minutes": m.get("minutes"), "order": m.get("order")} for mid, m in missions.items() if mid in PLACEMENTS}
    if not engine:
        return {}, {}, set()
    with foundations._conn() as conn:
        started = {r["mission_id"] for r in conn.execute("SELECT DISTINCT mission_id FROM f_attempts")}
    return engine, record_passes(), started


def inject_all(tracks) -> list:
    """Place the capability and teaching missions on the trails. Never raises: on a read problem the trails stay as
    the paths built them."""
    try:
        engine, passes, started = engine_state()
    except Exception:  # noqa: BLE001 - the home page must load even when the record can't be read
        return tracks
    for track in tracks or []:
        inject(track, engine, passes, started)
    return tracks
