"""The human review: a packet for the reviewer the learner chose, and a signed sign-off the plugin verifies.

The Guide Field Record rests on three kinds of evidence a script can judge
(lab graders, brief checks, run history) and three it cannot (whether the
learner reasons well, whether their evidence is plausibly their own, whether
they could stand in front of a client). A person judges those. This file builds
what that person reads and checks what they send back.

The packet is a folder: packet.json (everything, with a fingerprint), packet.md
(the same, readable), rubric.md (what the reviewer scores) and
signoff-template.json (what the reviewer fills in and signs). The fingerprint is
a SHA-256 over the packet's own contents, so a reviewer signs exactly this
packet and an edit afterwards stops matching.

The sign-off is a JSON file signed with the reviewer's Ed25519 key
(ed25519.py). The plugin verifies four things: the signature is valid; it names
this packet's fingerprint; the scores meet the floor on every rubric line and
the decision is "approved"; and the reviewer's public key is one it trusts. A
key on the published list shipped with the plugin (reviewers/trusted-reviewers.json)
counts as a reviewer Field Academy lists. A key on the learner's own local list
(reviewers.local.json in Field Academy's data folder) counts too, and the
Field Record says the reviewer is not on the published list.

What this proves: the sign-off was made with a key the plugin trusts, over this
exact packet, with the scores shown. What it does not prove: who holds the key,
or that the reviewer did the review well. A learner who edits their own copy of
the plugin can add their own key to their own local list, which is why the
Field Record states which list the key came from, and a third party can compare
it with the published list in the Field Academy repository.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

from . import ed25519

RUBRIC_VERSION = 1
FLOOR = 2
SCALE = (0, 3)

RUBRIC = [
    {"id": "diagnosis", "title": "Diagnostic reasoning",
     "look_for": "In the lab write-ups and the walkthrough, causes come from evidence in the logs and files, and the learner says how they knew. Guessing and checklist reciting score low.",
     "scores": {"0": "Names symptoms only.", "1": "Names a cause with little evidence.", "2": "Names causes and points at the evidence.", "3": "Weighs more than one cause and says what ruled the others out."}},
    {"id": "safety", "title": "Safe setup",
     "look_for": "Secrets stay out of settings files, each helper gets the smallest permission that still does its job, risky actions need a person's approval, and unsafe requests are refused with an alternative offered.",
     "scores": {"0": "Grants broad access or complies with an unsafe request.", "1": "Mostly safe with a clear gap.", "2": "Consistently safe.", "3": "Safe, and explains the reasons in the client's own terms."}},
    {"id": "scope_honesty", "title": "Scoping and price honesty",
     "look_for": "The proposal promises what can be delivered for the price and time, says what is left out, and says no where it should.",
     "scores": {"0": "Promises what cannot be delivered.", "1": "Vague about limits.", "2": "Clear limits and a credible price.", "3": "Clear limits, a credible price and a plan for when scope changes."}},
    {"id": "client_communication", "title": "Plain words for the client",
     "look_for": "A non-technical owner could read the proposal, the decline and the handover and know what to do on a bad Monday.",
     "scores": {"0": "Jargon throughout.", "1": "Mixed.", "2": "Plain and usable.", "3": "Plain, warm and ready to hand over as written."}},
    {"id": "lifecycle", "title": "Audit, design, build, staged test",
     "look_for": "The work goes in the order a deployment goes: audit what is there, design the boundaries, build and connect, then test away from live work before go-live.",
     "scores": {"0": "Builds first.", "1": "Tests after go-live.", "2": "Follows the order.", "3": "Follows the order and says what would make it go back a step."}},
    {"id": "evidence_integrity", "title": "Evidence is plausibly the learner's own",
     "look_for": "The run history, the drill gaps, the lab seeds and the learner's explanation agree with each other, and the walkthrough names details only someone who did the work would know.",
     "scores": {"0": "Evidence conflicts or looks copied.", "1": "Thin or hard to tell.", "2": "Consistent.", "3": "Consistent, and the learner volunteers where it went wrong."}},
]
RUBRIC_IDS = [item["id"] for item in RUBRIC]


# ------------------------------------------------------------- fingerprints --


def canonical(body) -> str:
    return json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def packet_fingerprint(body: dict) -> str:
    unsigned = {key: value for key, value in body.items() if key != "fingerprint"}
    return hashlib.sha256(canonical(unsigned).encode("utf-8")).hexdigest()


def key_fingerprint(public_key_hex: str) -> str:
    return hashlib.sha256(bytes.fromhex(public_key_hex)).hexdigest()[:16].upper()


# ------------------------------------------------------------------- packet --


def build_packet(evidence: dict, created_at: str) -> dict:
    """The packet body from everything the learner has done. ``evidence`` is assembled by deployer.py."""
    body = {
        "packet": "Field Academy Deployer review packet",
        "version": 1,
        "rubric_version": RUBRIC_VERSION,
        "created_at": created_at,
        **evidence,
    }
    body["fingerprint"] = packet_fingerprint(body)
    return body


def packet_markdown(packet: dict) -> str:
    lines = [
        f"# Deployer review packet for {packet.get('learner', '')}",
        "",
        f"Packet fingerprint: `{packet['fingerprint']}`",
        f"Created: {packet['created_at']}. Hermes version recorded: {packet.get('hermes_version', {}).get('value') or 'none'} ({packet.get('hermes_version', {}).get('source') or 'not read'}).",
        "",
        "The learner chose you to review their work on Field Academy's Guide path: setting up, deploying and managing Hermes Agent for small clients. "
        "Your signature goes on their own Field Record, which they keep. It is self-issued with Field Academy, a community plugin, and not issued or endorsed by Nous Research. "
        "Read this, score the six lines in rubric.md from 0 to 3, fill in signoff-template.json and sign it with scripts/sign_review.py. "
        "Approval needs every line at 2 or more. Ask the learner for anything missing instead of guessing.",
        "",
        "## Labs",
        "",
    ]
    for lab in packet["labs"]:
        lines += [
            f"### {lab['title']} (seed {lab['seed']})",
            f"Passed {lab['passed_at']} after {lab['attempts']} {'check' if lab['attempts'] == 1 else 'checks'}. Repaired folder fingerprint `{lab['tree_fingerprint'][:16]}`.",
            "Files the learner changed: " + (", ".join(f"{c['path']} ({c['change']})" for c in lab["changed"]) or "none"),
            "", "Their diagnosis:", "", f"> {lab['diagnosis']}", "",
        ]
    brief = packet["brief"]
    lines += ["## Client proposal", "", f"Fictional firm: {brief['firm']}. Document `{brief['document']}` fingerprint `{brief['sha256'][:16]}`. Scored {brief['score']} by the learner's own Hermes.", "", "```", brief["text"], "```", "", "## Judgment scenarios", ""]
    for item in packet["scenarios"]:
        lines += [f"### {item['title']} (score {item['score']})", "", f"> {item['answer']}", ""]
    lines += ["## Real deployment", ""]
    deploy = packet["deployment"]
    lines += [f"Service: {deploy.get('service', '')}. Job: {deploy.get('job', '')}. Status: {deploy.get('status', '')}.", f"Evidence: {deploy.get('evidence_note', '')}", ""]
    lines += ["## Failure drills", ""]
    for drill in packet["drills"]:
        lines += [f"- {drill['title']}: {drill['status']}. {drill.get('evidence_note', '')}"]
    fall = packet.get("fallback_evidence") or []
    if fall:
        lines += ["", "## Evidence Field Academy could not read from Hermes", "", "For each item below the learner's Hermes did not show run history, so this excerpt is the only evidence. It is the learner's own account until you accept it. Accept it only if it is consistent with the rest of the packet.", ""]
        for item in fall:
            lines += [f"### {item['item']} (excerpt fingerprint `{item['sha256'][:16]}`, {item['timestamps']} timestamps over {item['days']} days)", "", "```", item["excerpt"], "```", ""]
    walk = packet["walkthrough"]
    lines += ["## Walkthrough, in the learner's words", "", walk["explanation"], ""]
    if walk.get("media"):
        lines += [f"Recording on the learner's computer: `{walk['media']['name']}`, {walk['media']['bytes']} bytes, SHA-256 `{walk['media']['sha256'][:16]}`. Ask them to send it.", ""]
    lines += ["## What the plugin could and could not check", "", packet["limits"], ""]
    return "\n".join(lines)


def rubric_markdown() -> str:
    lines = ["# Reviewer rubric", "", f"Rubric version {RUBRIC_VERSION}. Score each line from 0 to 3. Approval needs {FLOOR} or more on every line.", ""]
    for item in RUBRIC:
        lines += [f"## {item['id']}: {item['title']}", "", item["look_for"], ""]
        lines += [f"- {score}: {words}" for score, words in item["scores"].items()]
        lines.append("")
    lines += ["## Evidence the plugin could not read", "", "If the packet has a section for evidence Field Academy could not read from Hermes, list the item ids you accept in `accepted_evidence` in the sign-off. Leave an item out and it stays unpassed.", ""]
    return "\n".join(lines)


def signoff_template(fingerprint: str, fallback_items: list) -> dict:
    return {
        "signoff": "Field Academy Deployer review",
        "version": 1,
        "packet_fingerprint": fingerprint,
        "reviewer": {"name": "", "role": "", "public_key": ""},
        "decision": "approved or changes_requested",
        "scores": {rid: None for rid in RUBRIC_IDS},
        "accepted_evidence": list(fallback_items),
        "comments": "",
        "signed_at": "",
        "signature": "",
    }


def write_packet(folder: Path, packet: dict, lab_sources: dict) -> dict:
    """Write the packet folder. Repaired lab folders are copied in so the reviewer can open them. Returns the paths."""
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "packet.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    (folder / "packet.md").write_text(packet_markdown(packet), encoding="utf-8")
    (folder / "rubric.md").write_text(rubric_markdown(), encoding="utf-8")
    fallback = [item["item"] for item in packet.get("fallback_evidence") or []]
    (folder / "signoff-template.json").write_text(json.dumps(signoff_template(packet["fingerprint"], fallback), indent=2), encoding="utf-8")
    copies = folder / "labs"
    if copies.exists():
        shutil.rmtree(copies)
    for lab_id, source in lab_sources.items():
        if Path(source).is_dir():
            shutil.copytree(source, copies / lab_id.split(".")[1])
    return {"folder": str(folder), "packet_json": str(folder / "packet.json"), "packet_md": str(folder / "packet.md"), "rubric": str(folder / "rubric.md"), "template": str(folder / "signoff-template.json")}


# ------------------------------------------------------------------ sign-off --


def sign_body(signoff: dict) -> bytes:
    return canonical({key: value for key, value in signoff.items() if key != "signature"}).encode("utf-8")


def sign(signoff: dict, secret_key: bytes) -> dict:
    """What the reviewer's script does: fill in the public key and signature. Runs on the reviewer's computer."""
    out = json.loads(json.dumps(signoff))
    out.setdefault("reviewer", {})["public_key"] = ed25519.public_key(secret_key).hex()
    out["signature"] = ""
    out["signature"] = ed25519.sign(secret_key, sign_body(out)).hex()
    return out


def load_trusted(published_path: Path, local_path: Path | None) -> dict:
    """{public key hex: {"name", "list": "published" | "local"}}"""
    trusted = {}
    for path, which in ((local_path, "local"), (published_path, "published")):
        if path and Path(path).is_file():
            try:
                data = json.loads(Path(path).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            for item in data.get("reviewers", []):
                key = str(item.get("public_key", "")).lower()
                if len(key) == 64:
                    trusted[key] = {"name": item.get("name", ""), "list": which}
    return trusted


def verify_signoff(signoff, packet: dict, trusted: dict) -> dict:
    """Check a sign-off against a packet. Returns {"valid", "approved", "problems", ...}. Never raises on bad input."""
    problems = []
    result = {"valid": False, "approved": False, "problems": problems, "reviewer": {}, "scores": {}, "accepted_evidence": [], "list": "", "key_fingerprint": ""}
    if not isinstance(signoff, dict):
        problems.append("The sign-off is not a JSON object.")
        return result
    reviewer = signoff.get("reviewer") if isinstance(signoff.get("reviewer"), dict) else {}
    key_hex = str(reviewer.get("public_key", "")).lower()
    try:
        public = bytes.fromhex(key_hex)
        signature = bytes.fromhex(str(signoff.get("signature", "")))
    except ValueError:
        problems.append("The reviewer key or the signature is not valid hexadecimal.")
        return result
    if not ed25519.verify(public, sign_body(signoff), signature):
        problems.append("The signature does not match the sign-off. It was edited after signing, or it was signed with a different key.")
        return result
    result["valid"] = True
    result["reviewer"] = {"name": reviewer.get("name", ""), "role": reviewer.get("role", ""), "public_key": key_hex}
    result["key_fingerprint"] = key_fingerprint(key_hex)
    if signoff.get("packet_fingerprint") != packet.get("fingerprint") or packet_fingerprint(packet) != packet.get("fingerprint"):
        problems.append("The sign-off is for a different packet, or the packet was changed after it was made. Build a new packet and ask the reviewer to sign that one.")
    if key_hex not in trusted:
        problems.append("The signature is valid, but the reviewer's key is on neither the published list nor your local list, so Field Academy does not count it.")
    else:
        result["list"] = trusted[key_hex]["list"]
    scores = signoff.get("scores") if isinstance(signoff.get("scores"), dict) else {}
    clean = {}
    for rid in RUBRIC_IDS:
        value = scores.get(rid)
        if not isinstance(value, int) or isinstance(value, bool) or not SCALE[0] <= value <= SCALE[1]:
            problems.append(f"The score for {rid} is missing or not a whole number from 0 to 3.")
        else:
            clean[rid] = value
    result["scores"] = clean
    if signoff.get("decision") != "approved":
        problems.append("The reviewer did not approve. Their comments say what to change.")
    low = [rid for rid, value in clean.items() if value < FLOOR]
    if low:
        problems.append(f"Approval needs {FLOOR} or more on every line. Below the floor: {', '.join(low)}.")
    signed = signoff.get("signed_at", "")
    try:
        when = datetime.fromisoformat(str(signed).replace("Z", "+00:00"))
        made = datetime.fromisoformat(str(packet.get("created_at", "")).replace("Z", "+00:00"))
        if when < made:
            problems.append("The sign-off is dated before the packet was made.")
    except ValueError:
        problems.append("The sign-off has no readable signing date.")
    needed = [item["item"] for item in packet.get("fallback_evidence") or []]
    accepted = [a for a in (signoff.get("accepted_evidence") or []) if isinstance(a, str)]
    result["accepted_evidence"] = accepted
    result["comments"] = str(signoff.get("comments", ""))[:2000]
    result["signed_at"] = str(signed)
    result["needs_acceptance"] = [n for n in needed if n not in accepted]
    result["approved"] = not problems
    return result
