"""The path map, the level ladder and the route to a Field Record.

Pure functions over the passport's tracks: they add what the map, the path
screen and the Field Record screen read, and never touch storage. state.py
calls ``decorate`` once per snapshot.

Copy here is learner-facing and follows docs/curriculum-voice.md: plain
English, headings that name the thing, no period at the end of a heading.

A Field Record is the learner's own learning record for one path. Field Academy
writes it on the learner's computer from checks that ran there. Nobody else
issues it: not Nous Research, not the Hermes team, not Field Academy's author.
Records made before 0.8.3 were called certificates and carry record format 1;
their stored text is never rewritten, because the record number is a hash over it.
"""

from __future__ import annotations

from .curriculum import LEVEL_NAMES, LEVELS, TRACKS

RECORD = "Field Record"

# The one line every shareable record carries, on screen, in the .md and in the .json.
DISCLAIMER = (
    "Self-issued with Field Academy, a community plugin for Hermes Agent. "
    "Not issued or endorsed by Nous Research."
)

# Bumped when the stored wording of a new record changes. Format 1 (0.8.2 and earlier)
# has no record_format key and called itself a certificate.
RECORD_FORMAT = 2

ABOUT = (
    "A Field Record is your own learning record for a path. You build it mission by mission, "
    "and Field Academy writes it on your computer with the proof of what you did. "
    "Field Academy is a free community plugin by Damon Gardenhire. "
    "Nous Research doesn't issue, review or endorse Field Records."
)

ISSUER = "Created by its holder with the Field Academy plugin."

WHAT_IT_SHOWS = (
    "It records work that passed its checks on the holder's own computer, with the proof attached. "
    "Anyone who reads it can see exactly what was checked."
)

RECEIVE = [
    "A Field Record with your name, the path, and the date you finished it",
    "The proof behind every mission: what each check found, your score on each question, "
    "and the fingerprint of every document you wrote",
    "A record number calculated from that proof. Change any line and the number stops matching",
    "The version of each check you passed, and a note on any mission where a placement check skipped the reading",
    "A copy saved as a file on your computer, to keep or share",
]

EACH_MISSION = (
    "A mission passes when you have:\n"
    "1. Read the lesson and a finished example\n"
    "2. Filled in a half-finished one\n"
    "3. Tried the practice\n"
    "4. Scored 70 or more on its question\n"
    "5. Passed its check"
)

EXPLAIN_PROOF = "Your answer to one question, in your own words, scored 70 or more by Hermes."


def _level_status(missions):
    if missions and all(item["status"] == "verified" for item in missions):
        return "passed"
    if any(item["status"] != "not_started" for item in missions):
        return "started"
    return "not_started"


def ladder(track):
    """Three rungs, Beginner to Advanced, each with what it means and its missions.

    Nothing is locked: anyone can open any mission. "current" marks the first
    rung that isn't passed yet, which is where the map says "You are here".
    """
    meanings = TRACKS[track["id"]]["level_meanings"]
    rungs = []
    current_found = False
    for number, level in enumerate(LEVELS, start=1):
        missions = [item for item in track["missions"] if item["level"] == level]
        status = _level_status(missions)
        is_current = not current_found and status != "passed"
        current_found = current_found or is_current
        rungs.append(
            {
                "id": level,
                "number": number,
                "name": LEVEL_NAMES[level],
                "meaning": meanings[level],
                "missions": [item["id"] for item in missions],
                "passed": sum(item["status"] == "verified" for item in missions),
                "total": len(missions),
                "status": status,
                "current": is_current,
            }
        )
    return rungs


def here(track):
    """The mission the learner is on: the first one on the path that hasn't passed."""
    for level in LEVELS:
        for item in track["missions"]:
            if item["level"] == level and item["status"] != "verified":
                return item["id"]
    return ""


def certificate_route(track, issued=None):
    """The route to the path's Field Record. The name stays certificate_route for the API."""
    total = len(track["missions"])
    passed = sum(item["status"] == "verified" for item in track["missions"])
    started = any(item["status"] != "not_started" for item in track["missions"])
    if issued:
        status = "issued"
    elif passed == total and total:
        status = "ready"
    elif started:
        status = "in_progress"
    else:
        status = "not_started"
    ordered = sorted(track["missions"], key=lambda item: LEVELS.index(item["level"]))
    return {
        "title": f"{track['name']} {RECORD}",
        "status": status,
        "passed": passed,
        "total": total,
        "remaining": total - passed,
        "steps": [
            {
                "title": "Pass every mission on this path",
                "detail": (
                    f"{total} missions: three levels, Beginner to Advanced, then a capstone on your own problem. "
                    f"You've passed {passed} of {total}. {EACH_MISSION}"
                ),
            },
            {
                "title": "Show the proof each one asks for",
                "detail": "Every check reads real work on this computer, and only a passing check counts.",
            },
            {
                "title": "Create your Field Record",
                "detail": "Type the name you want on it. Field Academy writes it on your computer straight away and saves a copy.",
            },
        ],
        "proof": [
            {
                "mission_id": item["id"],
                "title": item["title"],
                "level": item["level"],
                "level_name": item["level_name"],
                "check": item["proof"],
                "explain": EXPLAIN_PROOF,
                "passed": item["status"] == "verified",
                "passed_at": item.get("passed_at", ""),
            }
            for item in ordered
        ],
        "receive": list(RECEIVE),
        "shows": WHAT_IT_SHOWS,
        "issuer": ISSUER,
        "disclaimer": DISCLAIMER,
        "issued": issued or None,
    }


def decorate(tracks, certificates):
    """Add levels, the current mission and the route to the Field Record to each track."""
    for track in tracks:
        track["levels"] = ladder(track)
        current = next((rung for rung in track["levels"] if rung["current"]), None)
        track["current_level"] = current["id"] if current else "complete"
        track["here"] = here(track)
        track["certificate"] = certificate_route(track, certificates.get(track["id"]))
    return tracks


def next_up(tracks, goal_track, goal_text=""):
    """The one mission the map offers first: the current mission on the learner's path.

    Carries the mission's "why this matters to you" line, built from the
    learner's own goal when they gave one, and the time it will take.
    """
    ordered = sorted(tracks, key=lambda track: track["id"] != goal_track)
    for track in ordered:
        mission_id = track.get("here") or here(track)
        if mission_id:
            item = next(m for m in track["missions"] if m["id"] == mission_id)
            if item["status"] == "not_started" and not any(m["status"] != "not_started" for m in track["missions"]):
                reason = f"It's where the {track['name']} path starts."
            elif item["status"] == "not_started":
                reason = f"It's the next mission on your {track['name']} path."
            else:
                reason = "You've started it. Pick up where you left off."
            return {
                "mission_id": mission_id,
                "track_id": track["id"],
                "track_name": track["name"],
                "title": item["title"],
                "level_name": item["level_name"],
                "minutes": item["minutes"],
                "reason": reason,
                "use_text": item.get("use_text", ""),
            }
    return None
