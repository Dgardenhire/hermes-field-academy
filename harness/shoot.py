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
import subprocess
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
            proc = subprocess.Popen(
                [
                    CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--force-prefers-reduced-motion",
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
