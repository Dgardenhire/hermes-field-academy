#!/usr/bin/env python3
"""Screenshot Field Academy screens through the harness with headless Chrome.

    python3 harness/shoot.py map                # one screen
    python3 harness/shoot.py map path-ladder    # several, one at a time
    python3 harness/shoot.py --list

Runs one Chrome at a time and exits, so it stays light on a machine short of
memory. Serves the repo root on a free local port for the duration only. PNGs go
to harness/shots/. Needs network for the harness's CDN imports. Runs no Hermes
command and touches nothing under ~/.hermes.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import os
import shutil
import subprocess
import tempfile
import sys
import threading
import time
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "harness" / "shots"
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
MIN_PNG_BYTES = 20_000
DP = "For clients, in practice"  # the Deployer trail's label on the map, which opens its path


def q(state, *clicks, scroll="", extra=""):
    parts = [f"state={state}"] + [f"click={quote(c)}" for c in clicks]
    if scroll:
        parts.append(f"scroll={quote(scroll)}")
    if extra:
        parts.append(extra)
    return "&".join(parts)


# name -> (query, width, height)
SCENARIOS = {
    "map-fresh": (q("fresh"), 1280, 1500),
    "brief-map": (q("progress", scroll="Trail map"), 1280, 900),
    "brief-path": (q("dp_progress", DP), 1280, 900),
    "brief-lab": (q("dp_lab", DP, "The key in the open"), 1280, 1030),
    "map": (q("progress"), 1280, 1700),
    "map-light": (q("progress", extra="theme=light"), 1280, 1700),
    "map-review-queue": (q("progress", scroll="Review queue"), 1280, 1000),
    "map-changes": (q("progress", scroll="What changed since you learned this"), 1280, 1000),
    "path-ladder": (q("progress", "Traveler"), 1280, 1500),
    "path-placement": (q("progress", "Traveler", scroll="Placement check"), 1280, 1000),
    "path-certificate-route": (q("progress", "Traveler", scroll="Your route to the Field Record"), 1280, 1150),
    "path-ready-to-claim": (q("ready", "Messenger", scroll="Your route to the Field Record"), 1280, 1350),
    "mission-story": (q("progress", "Traveler", "Find where Hermes is running"), 1280, 2600),
    "mission-deeper": (q("progress", "Traveler", "Find where Hermes is running", scroll="Check where your Hermes runs"), 1280, 1300),
    "mission": (q("progress", "Traveler", "Make Hermes remember how you work"), 1280, 1700),
    "mission-example": (q("progress", "Traveler", "Make Hermes remember how you work", scroll="See it done"), 1280, 1100),
    "mission-complete": (q("progress", "Crossroads", "Turn a vague request into a first project", scroll="Your turn"), 1280, 1500),
    "mission-links": (q("progress", "Traveler", "Make Hermes remember how you work", scroll="Go deeper"), 1280, 1150),
    "mission-check": (q("fresh", "Start", "Check my work", scroll="Check where your Hermes runs"), 1280, 1000),
    "mission-document": (q("progress", "Crossroads", "Turn a vague request into a first project", scroll="Check your scope document"), 1280, 1000),
    "mission-miss": (q("misses", "Crossroads", "Turn a vague request into a first project", scroll="Check your scope document"), 1280, 1300),
    "review-questions": (q("reviews", "Practice early", extra="review=open"), 1280, 1200),
    "review-waiting": (q("reviews", "Practice early", extra="review=submitted"), 1280, 1200),
    "review-results": (q("reviews", "Practice early", extra="review=graded"), 1280, 1500),
    "placement": (q("placement", "Traveler", "Open the placement check"), 1280, 1700),
    "placement-results": (q("placement", "Traveler", "Open the placement check", "@autopick", "See my result"), 1280, 1900),
    "certificate": (q("issued", "Messenger", "View your Field Record"), 1280, 1150),
    "certificate-saved": (q("issued", "Messenger", "View your Field Record", "Save as a file", scroll="Saved"), 1280, 1000),
    # Foundations: each state is the real backend after the real steps (harness/foundations_fixtures.py).
    "f-map": (q("f_fresh", scroll="Foundations"), 1280, 1000),
    "f-path": (q("f_compare", "Open Foundations"), 1280, 1000),
    "f-recall": (q("f_fresh", "Open Foundations", "Start"), 1280, 1100),
    "f-claim": (q("f_predict", "Open Foundations", "Continue", "Your claim"), 1280, 1200),
    "f-predict": (q("f_predict", "Open Foundations", "Continue"), 1280, 1500),
    "f-setup": (q("f_setup", "Open Foundations", "Continue"), 1280, 1100),
    "f-try": (q("f_lab", "Open Foundations", "Continue", "Practice", "Show memory file"), 1280, 2200),
    "f-idea": (q("f_lab", "Open Foundations", "Continue", "The idea"), 1280, 3400),
    "f-expert": (q("f_lab", "Open Foundations", "Continue", "Watch it done"), 1280, 1500),
    "f-lab": (q("f_lab", "Open Foundations", "Continue"), 1280, 1700),
    "f-check": (q("f_checked", "Open Foundations", "Continue", "Check"), 1280, 2300),
    "f-compare": (q("f_compare", "Open Foundations", "Continue"), 1280, 1700),
    "f-fix": (q("f_record", "Open Foundations", "Continue", "Fix and transfer"), 1280, 2000),
    "f-record": (q("f_record", "Open Foundations", "Continue"), 1280, 2000),
    "f-done": (q("f_done", "Open Foundations", "Open"), 1280, 1600),
    "f-compare-light": (q("f_compare", "Open Foundations", "Continue", extra="theme=light"), 1280, 1700),
    "f-lab-narrow": (q("f_lab", "Open Foundations", "Continue"), 820, 2000),
    "f-path-record": (q("f_done", "Open Foundations", scroll="How well you judge your own work"), 1280, 1100),
    "f-record-view": (q("f_done", "Open Foundations", "Open my Field Record"), 1280, 2600),
    "f-record-excerpts": (q("f_done", "Open Foundations", "Open my Field Record", scroll="Every excerpt"), 1280, 1500),
    "f-record-save": (q("f_done", "Open Foundations", "Open my Field Record", scroll="In your words"), 1280, 1200),
    "f-record-saved": (q("f_saved", "Open Foundations", "Open my Field Record", scroll="Every excerpt"), 1280, 2400),
    "f-record-light": (q("f_saved", "Open Foundations", "Open my Field Record", extra="theme=light"), 1280, 2600),
    "f-record-narrow": (q("f_saved", "Open Foundations", "Open my Field Record"), 820, 3200),
    # Missions 1, 2, 4, 5 and 6 (0.9 M6, part A): one key state each.
    "fa-loop-lab": (q("fa_loop_lab", "Open Foundations", "Continue"), 1280, 2600),
    "fa-cost-try": (q("fa_cost_try", "Open Foundations", "Continue", "Practice"), 1280, 2600),
    "fa-new-chats-lab": (q("fa_new_chats_lab", "Open Foundations", "Continue"), 1280, 2200),
    "fa-new-chats-before-b": (q("fa_new_chats_before_b", "Open Foundations", "Continue"), 1280, 1400),
    "fa-skills-try": (q("fa_skills_try", "Open Foundations", "Continue", "Practice"), 1280, 3400),
    "fa-profiles-lab": (q("fa_profiles_lab", "Open Foundations", "Continue"), 1280, 2400),
    # Missions 7 to 11, one key state each (harness/foundations_fixtures_b.py).
    "f7-lab": (q("f7_lab", "Open Foundations", "Continue"), 1280, 2600),
    "f8-watch": (q("f8_watch", "Open Foundations", "Continue"), 1280, 2400),
    "f9-check": (q("f9_checked", "Open Foundations", "Continue", "Check"), 1280, 2400),
    "f10-lab": (q("f10_lab", "Open Foundations", "Continue"), 1280, 2400),
    "f11-lab": (q("f11_lab", "Open Foundations", "Continue"), 1280, 2600),
    # The Deployer path. Each state is the real backend after the real steps (harness/deployer_fixtures.py).
    "dp-map": (q("dp_progress", scroll="Guide path"), 1280, 1100),
    "dp-path": (q("dp_progress", DP), 1280, 2300),
    "dp-path-light": (q("dp_progress", DP, extra="theme=light"), 1280, 2300),
    "dp-path-narrow": (q("dp_progress", DP), 820, 3000),
    "dp-path-awaiting": (q("dp_review", DP, scroll="Summit"), 1280, 1200),
    "dp-lab-closed": (q("dp_fresh", DP, "The key in the open"), 1280, 1100),
    "dp-lab-open": (q("dp_lab", DP, "The key in the open"), 1280, 1900),
    "dp-lab-miss": (q("dp_progress", DP, "The runaway bill", "Check my repair", scroll="Your repair and your write-up"), 1280, 2200),
    "dp-brief": (q("dp_progress", DP, "A proposal for a three-person firm"), 1280, 1900),
    "dp-brief-scoring": (q("dp_progress", DP, "A proposal for a three-person firm", "Check my proposal", scroll="Check your proposal"), 1280, 1100),
    "dp-scenarios": (q("dp_progress", DP, "Nine judgment scenarios"), 1280, 1300),
    "dp-scenario": (q("dp_progress", DP, "Nine judgment scenarios", "The client wants it to email customers on its own"), 1280, 1100),
    "dp-deploy": (q("dp_deploy", DP, "Run one real service for several days", scroll="Your access record"), 1280, 1500),
    "dp-deploy-unreadable": (q("dp_unreadable", DP, "Run one real service for several days", "Check what Hermes recorded", scroll="Check the run history"), 1280, 1800),
    "dp-drills": (q("dp_drills", DP, "Failure drills"), 1280, 2600),
    "dp-review": (q("dp_review", DP, "Walkthrough and expert review", scroll="Your reviewer"), 1280, 1500),
    "dp-ready": (q("dp_ready", DP, "Walkthrough and expert review", scroll="Create your Field Record"), 1280, 1200),
    "dp-certificate": (q("dp_issued", DP, "View your Field Record"), 1280, 2000),
    "dp-reverify": (q("dp_reverify", DP, "View your Field Record", scroll="Re-verify this Field Record"), 1280, 1300),
    # Design review: the mission pages in both themes, a red and a green accent, wide and narrow.
    "d-first": (q("f_fresh"), 1280, 900),
    "d-first-light-narrow": (q("f_fresh", extra="theme=light&accent=green"), 640, 1500),
    "d-lab-dark": (q("f_lab", "Open Foundations", "Continue"), 1440, 1700),
    "d-lab-light": (q("f_lab", "Open Foundations", "Continue", extra="theme=light"), 1440, 1700),
    "d-lab-red": (q("f_lab", "Open Foundations", "Continue", extra="accent=red"), 1280, 1700),
    "d-lab-green-light": (q("f_lab", "Open Foundations", "Continue", extra="theme=light&accent=green"), 1280, 1700),
    "d-lab-narrow": (q("f_lab", "Open Foundations", "Continue"), 640, 2400),
    "d-check-red-light": (q("f_checked", "Open Foundations", "Continue", "Check", extra="theme=light&accent=red"), 1280, 2300),
    "d-check-green": (q("f_checked", "Open Foundations", "Continue", "Check", extra="accent=green"), 1280, 2300),
    "d-record-light": (q("f_saved", "Open Foundations", "Open my Field Record", extra="theme=light"), 1280, 2600),
    "d-record-narrow-green": (q("f_saved", "Open Foundations", "Open my Field Record", extra="accent=green"), 640, 3400),
    "d-f7-red": (q("f7_lab", "Open Foundations", "Continue", extra="accent=red"), 1280, 2600),
    "d-f8-light-narrow": (q("f8_watch", "Open Foundations", "Continue", extra="theme=light"), 640, 3000),
    # The README, manual and catalog screenshots for 0.9 (copied to docs/shots/ and docs/manual/).
    "doc-home": (q("f_fresh"), 1280, 900),
    "doc-path": (q("f_compare", "Open Foundations"), 1280, 1000),
    "doc-lab": (q("f_lab", "Open Foundations", "Continue"), 1280, 1120),
    "doc-check": (q("f_checked", "Open Foundations", "Continue", "Check"), 1280, 1000),
    "doc-schedule": (q("f8_watch", "Open Foundations", "Continue", extra="theme=light"), 1280, 1300),
    "doc-record": (q("f_saved", "Open Foundations", "Open my Field Record"), 1280, 1000),
    "doc-excerpts": (q("f_saved", "Open Foundations", "Open my Field Record", scroll="Every excerpt"), 1280, 900),
    # 0.9 persona test persona-test fixes, in both themes (docs/STATUS.md).
    "pt-home": (q("f_fresh"), 1280, 1500),
    "pt-home-light": (q("f_fresh", extra="theme=light"), 1280, 1500),
    "pt-path": (q("f_compare", "Open Foundations", "Already use Hermes? Test out of a mission"), 1280, 1500),
    "pt-path-light": (q("f_compare", "Open Foundations", "Already use Hermes? Test out of a mission", extra="theme=light"), 1280, 1500),
    "pt-idea": (q("f_lab", "Open Foundations", "Continue", "The idea", scroll="Check yourself"), 1280, 1300),
    "pt-idea-light": (q("f_lab", "Open Foundations", "Continue", "The idea", scroll="Check yourself", extra="theme=light"), 1280, 1300),
    "pt-try": (q("f_lab", "Open Foundations", "Continue", "Practice"), 1280, 2000),
    "pt-check": (q("f_checked", "Open Foundations", "Continue", "Check"), 1280, 2600),
    "pt-check-light": (q("f_checked", "Open Foundations", "Continue", "Check", extra="theme=light"), 1280, 2600),
    "pt-compare": (q("f_compare", "Open Foundations", "Continue"), 1280, 1700),
    "pt-f7-practice": (q("f7_lab", "Open Foundations", "Continue", "Practice"), 1280, 2200),
    "pt-f7-connector": (q("f7_lab", "Open Foundations", "Continue", scroll="The connector settings text"), 1280, 1100),
    "pt-f7-connector-light": (q("f7_lab", "Open Foundations", "Continue", scroll="The connector settings text", extra="theme=light"), 1280, 1100),
    "pt-f9-practice": (q("f9_checked", "Open Foundations", "Continue", "Practice"), 1280, 2000),
    "pt-f9-practice-light": (q("f9_checked", "Open Foundations", "Continue", "Practice", extra="theme=light"), 1280, 2000),
    "pt-f10-lab": (q("f10_lab", "Open Foundations", "Continue", scroll="The practice profile's tools"), 1280, 1200),
    "pt-record": (q("f_saved", "Open Foundations", "Open my Field Record"), 1280, 2600),
    "pt-record-light": (q("f_saved", "Open Foundations", "Open my Field Record", extra="theme=light"), 1280, 2600),
    "pt-recordstep": (q("f_record", "Open Foundations", "Continue"), 1280, 2200),
    # School 1: the trail map as the school, and the Field Record's trail map.
    "school-home": (q("f_fresh"), 1280, 1100),
    "school-crossroads": (q("progress", "Crossroads", scroll="Camps on this trail"), 1280, 1500),
    "school-boundary": (q("progress", "Boundary Keeper", scroll="Camps on this trail"), 1280, 1500),
    "school-mission": (q("fc_toolsets_lab", "Crossroads", "Give Hermes only the tools a job needs"), 1280, 2200),
    "school-mission-delegation": (q("fc_delegation_lab", "Boundary Keeper", "Hand work to helper agents, and check what each one did"), 1280, 2200),
    "school-guide": (q("dp_progress", DP, scroll="Camps on this trail"), 1280, 1700),
    "school-mission-teach": (q("fc_teach_review_lab", DP, "Judge someone's work from their Field Record"), 1280, 2000),
    "school-record": (q("f_saved", "Open Foundations", "Open my Field Record", scroll="The trail map"), 1280, 1100),
    "offline": (q("offline"), 1280, 720),
    "loading": (q("loading"), 1280, 900),
    "map-narrow": (q("progress"), 820, 1900),
}


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("names", nargs="*", help="scenario names")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args(argv)
    if args.list or not args.names:
        print("\n".join(SCENARIOS))
        return 0
    unknown = [n for n in args.names if n not in SCENARIOS]
    if unknown:
        parser.error(f"unknown scenario: {', '.join(unknown)}")
    if not (ROOT / "harness" / "fixtures.json").exists():
        subprocess.run([sys.executable, str(ROOT / "harness" / "make_fixtures.py")], check=True)
    SHOTS.mkdir(parents=True, exist_ok=True)

    handler = functools.partial(QuietHandler, directory=str(ROOT))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    failed = []
    try:
        for name in args.names:
            query, width, height = SCENARIOS[name]
            target = SHOTS / f"{name}.png"
            url = f"http://127.0.0.1:{port}/harness/index.html?{query}"
            target.unlink(missing_ok=True)
            # Chrome writes the PNG when the virtual time budget ends but can linger afterwards
            # (the kit's working arc and shimmer keep animating), so wait for the file to settle,
            # then stop it. One Chrome at a time.
            # A throwaway profile per shot, removed afterwards: without --user-data-dir headless Chrome leaves a
            # scoped_dir profile behind in the system temp folder on every run.
            profile = tempfile.mkdtemp(prefix="fa-shoot-", dir=os.environ.get("FA_SHOOT_TMP") or None)
            proc = subprocess.Popen(
                [
                    CHROME, "--headless=new", f"--user-data-dir={profile}", "--mute-audio", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--force-prefers-reduced-motion",
                    "--disable-extensions", "--disable-background-networking", "--force-device-scale-factor=1",
                    f"--window-size={width},{height}", "--virtual-time-budget=12000", f"--screenshot={target}", url,
                ],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            deadline, last = time.time() + 120, -1
            while time.time() < deadline and proc.poll() is None:
                time.sleep(1)
                size = target.stat().st_size if target.exists() else -1
                if size > 0 and size == last:
                    break
                last = size
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=10)
            shutil.rmtree(profile, ignore_errors=True)
            if not target.exists() or target.stat().st_size < MIN_PNG_BYTES:
                failed.append(name)
            print(f"{name}: {target}", flush=True)
    finally:
        server.shutdown()
    if failed:
        print(f"blank or near-blank: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
