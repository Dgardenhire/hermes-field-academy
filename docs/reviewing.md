# Reviewing a Guide packet

This is for a reviewer a learner chose to read and sign their review packet. A learner who has finished every
other part of the Guide path (internal id `deployer`) builds a packet in Field Academy and sends you its folder.

Your signature goes on the learner's own Field Record, which they keep. The record is self-issued with Field
Academy, a community plugin for Hermes Agent, and not issued or endorsed by Nous Research. You sign as yourself:
nobody at Nous Research or on the Hermes team appoints or approves reviewers. Field Academy's published reviewer
list ships empty, so today the learner adds your public key to their own list.

## What you receive

A folder with:

- `packet.md`, the packet in readable form: each lab's changed files and the learner's diagnosis, the proposal, the
  nine answers, the deployment and drills with how each was evidenced, the walkthrough in the learner's words, and
  a note on what the plugin could and could not check.
- `packet.json`, the same thing as data, with a fingerprint. You sign the fingerprint.
- `rubric.md`, the six lines you score.
- `signoff-template.json`, the shape of what you send back.
- `labs/`, a copy of each repaired lab folder, so you can open the files.

Every secret in a lab is made up. The packet never holds a real key, and pasted log excerpts have key-shaped text
removed before they are kept.

## What you score

Six lines, 0 to 3 each (the words are in `rubric.md`): diagnostic reasoning, safety posture, scoping and price
honesty, plain words for the client, the order of audit, design, build and staged test, and whether the evidence is
plausibly the learner's own. Approval needs 2 or more on every line. Ask the learner for anything missing rather
than guessing. You can also ask for the recording of the walkthrough if they gave one: the packet carries its
fingerprint.

If the packet has a section for evidence Field Academy could not read from Hermes, those excerpts are the
learner's own account. Accept one only if it fits the rest of the packet (the labs' seeds, the dates, the
learner's explanation). List what you accept with `--accept`. Anything you leave out stays unpassed.

## Signing

```bash
python3 scripts/sign_review.py keygen --out ~/reviewer.key
python3 scripts/sign_review.py sign --packet <packet folder>/packet.json --key ~/reviewer.key \
    --name "Your Name" --role "Hermes consultant" \
    --score diagnosis=3 --score safety=2 --score scope_honesty=3 \
    --score client_communication=2 --score lifecycle=3 --score evidence_integrity=2 \
    --decision approved --accept deploy --comments "..." --out signoff.json
```

`keygen` writes your secret key to a file only you can read, and prints your public key. To be listed as a
reviewer on Field Academy's published list, send the public key and your name to the maintainer, who adds it to
`reviewers/trusted-reviewers.json` after checking who holds it. `sign` refuses to sign a packet that no longer
matches its own fingerprint.

Send `signoff.json` to the learner, who pastes it into Field Academy. If you decline, use
`--decision changes_requested` and say what to change in `--comments`; the learner then fixes it and builds a new
packet.

## What the plugin checks, and what that proves

The plugin verifies four things: the signature is valid; it names this exact packet's fingerprint, so any edit to
the packet after you read it breaks it; every rubric line is a whole number from 0 to 3 with the floor met and the
decision approved; and your public key is one it trusts.

A key on the published list (`reviewers/trusted-reviewers.json`, shipped with the plugin) counts as a reviewer
Field Academy lists. A key on the learner's own local list (`reviewers.local.json` in Field Academy's data folder)
also counts, and the Field Record says the reviewer is not on the published list. A valid signature from any other
key is shown and does not count.

What this proves: the sign-off was made with a key the plugin trusts, over this packet, with these scores. What it
does not prove: who holds the key, or that the review was done well. A learner who edits their own copy of the
plugin can put their own key on their own local list and sign their own packet, which is why the Field Record states
which list the key came from and why a third party should compare it with the published list in the Field Academy
repository. Anyone reading a Guide Field Record should check the reviewer's key against that list.

The signing code is a plain implementation of Ed25519 (RFC 8032), tested against that RFC's vectors. It is not
constant-time and not a hardened signer. It is meant for signing a review on your own computer.
