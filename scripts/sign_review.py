#!/usr/bin/env python3
"""For a reviewer a learner chose: make a key, and sign a Field Academy Guide review packet.

Runs on the reviewer's own computer. It needs only Python 3 and this plugin's folder. It reads the packet,
shows what it is about to sign, and writes a signed JSON file the learner pastes into Field Academy. It never
runs Hermes and never touches a Hermes home.

    # once: make a key. The secret stays in a file only you can read; the public key is what you publish.
    python3 scripts/sign_review.py keygen --out ~/reviewer.key

    # for each packet: read packet.md and rubric.md in the learner's packet folder, then
    python3 scripts/sign_review.py sign \\
        --packet "<packet folder>/packet.json" --key ~/reviewer.key \\
        --name "Your Name" --role "Hermes consultant" \\
        --score diagnosis=3 --score safety=2 --score scope_honesty=3 \\
        --score client_communication=2 --score lifecycle=3 --score evidence_integrity=2 \\
        --decision approved --accept deploy --accept drill.revoke \\
        --comments "Clear diagnoses. Say the daily number out loud sooner." \\
        --out signoff.json

Scores run 0 to 3 and approval needs 2 or more on every line (docs/reviewing.md). --accept lists the evidence
Field Academy could not read from Hermes that you judged believable; leave an item out and it stays unpassed.

Honest limit: this is a plain implementation of Ed25519 (ed25519.py), written for clarity and checked against the
RFC 8032 test vectors. It is fine for signing a review on your own computer. It is not a hardened signer.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import pathlib
import sys
import types
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load():
    """The plugin's walkthrough module, without starting the plugin: a bare package pointing at the folder."""
    package = types.ModuleType("fa_sign")
    package.__path__ = [str(ROOT)]
    sys.modules["fa_sign"] = package
    return importlib.import_module("fa_sign.walkthrough"), importlib.import_module("fa_sign.ed25519")


def fileaccess():
    load()
    return importlib.import_module("fa_sign.fileaccess")


def read_key(path):
    path = pathlib.Path(path).expanduser()
    others = fileaccess().others(path)
    if others:
        # The same warning OpenSSH gives for a private key others can read. Signing still works.
        print(f"Warning: {path} can be read by others ({', '.join(others)}). Only you should be able to read your secret key.", file=sys.stderr)
    text = path.read_text().strip()
    secret = bytes.fromhex(text)
    if len(secret) != 32:
        raise SystemExit("The key file must hold 64 hexadecimal characters.")
    return secret


def keygen(args):
    wt, ed = load()
    target = pathlib.Path(args.out).expanduser()
    if target.exists():
        raise SystemExit(f"{target} already exists. Nothing was changed.")
    secret = os.urandom(32)
    # Private from the moment it exists: mode 600 on Linux and macOS, an access list naming only you on Windows.
    try:
        descriptor = fileaccess().create_private(target)
    except FileExistsError:
        raise SystemExit(f"{target} already exists. Nothing was changed.")
    with os.fdopen(descriptor, "w") as handle:
        handle.write(secret.hex() + "\n")
    public = ed.public_key(secret).hex()
    print(f"Secret key written to {target} (readable only by you). Keep it private and back it up.")
    print(f"Public key:  {public}")
    print(f"Fingerprint: {wt.key_fingerprint(public)}")
    print('To be listed as a Field Academy reviewer, send the public key and your name to the maintainer, who adds')
    print('{"name": "...", "public_key": "..."} to reviewers/trusted-reviewers.json.')


def sign(args):
    wt, ed = load()
    packet = json.loads(pathlib.Path(args.packet).expanduser().read_text(encoding="utf-8"))
    if wt.packet_fingerprint(packet) != packet.get("fingerprint"):
        raise SystemExit("The packet does not match its own fingerprint. It was edited after it was made. Nothing was signed.")
    scores = {}
    for item in args.score or []:
        name, _, value = item.partition("=")
        if name not in wt.RUBRIC_IDS or not value.isdigit() or not wt.SCALE[0] <= int(value) <= wt.SCALE[1]:
            raise SystemExit(f"--score {item!r}: use one of {', '.join(wt.RUBRIC_IDS)}, then = and a whole number from 0 to 3.")
        scores[name] = int(value)
    missing = [rid for rid in wt.RUBRIC_IDS if rid not in scores]
    if missing:
        raise SystemExit(f"Score every line. Missing: {', '.join(missing)}.")
    needs = [item["item"] for item in packet.get("fallback_evidence") or []]
    unknown = [a for a in args.accept or [] if a not in needs]
    if unknown:
        raise SystemExit(f"--accept names evidence that is not in the packet's list ({', '.join(needs) or 'none'}): {', '.join(unknown)}.")
    body = {
        "signoff": "Field Academy Deployer review",
        "version": 1,
        "packet_fingerprint": packet["fingerprint"],
        "reviewer": {"name": args.name, "role": args.role or ""},
        "decision": args.decision,
        "scores": scores,
        "accepted_evidence": list(args.accept or []),
        "comments": args.comments or "",
        "signed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    secret = read_key(args.key)
    signed = wt.sign(body, secret)
    print(f"Learner: {packet.get('learner')}   Packet: {packet['fingerprint'][:16]}   Decision: {args.decision}")
    print("Scores: " + ", ".join(f"{k} {v}" for k, v in scores.items()))
    print(f"Signing with key {wt.key_fingerprint(signed['reviewer']['public_key'])}.")
    pathlib.Path(args.out).expanduser().write_text(json.dumps(signed, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {args.out}. Send it to the learner, who pastes its contents into Field Academy.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    k = sub.add_parser("keygen", help="make a signing key")
    k.add_argument("--out", required=True)
    k.set_defaults(run=keygen)
    s = sub.add_parser("sign", help="sign a review packet")
    s.add_argument("--packet", required=True)
    s.add_argument("--key", required=True)
    s.add_argument("--name", required=True)
    s.add_argument("--role", default="")
    s.add_argument("--score", action="append")
    s.add_argument("--decision", choices=("approved", "changes_requested"), required=True)
    s.add_argument("--accept", action="append")
    s.add_argument("--comments", default="")
    s.add_argument("--out", required=True)
    s.set_defaults(run=sign)
    args = parser.parse_args(argv)
    args.run(args)


if __name__ == "__main__":
    main()
