"""The installed Hermes version, read from the checkout without running Hermes or git.

Hermes 0.22.4 installed from source carries an install stamp that says baseVersion 0.21.5 and displayVersion
0.21.5+15970.g4d04303, while the checkout is tagged v0.22.4. Field Academy must report 0.22.4 when a release tag
sits on the installed commit, and say plainly when all it has is the stamp's older base version.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import struct
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_scrub import load  # noqa: E402

COMMIT = "4d04303818b61bf3aa09278af48356315515965b"
OTHER = "1111111111111111111111111111111111111111"


def tag_object(target, name):
    return f"object {target}\ntype commit\ntag {name}\ntagger Hermes <h@example.invalid> 1792599405 +0000\n\nRelease {name}\n".encode()


def object_sha(kind, data):
    return hashlib.sha1(f"{kind} {len(data)}".encode() + b"\0" + data).hexdigest()


def pack_header(kind_number, size):
    first = (kind_number << 4) | (size & 0x0F)
    size >>= 4
    out = bytearray()
    while True:
        if size:
            out.append(first | 0x80)
            first = size & 0x7F
            size >>= 7
        else:
            out.append(first)
            return bytes(out)


def write_pack(git, sha, data):
    """A one-object pack and its version-2 index, as git lays them down."""
    folder = git / "objects" / "pack"
    folder.mkdir(parents=True, exist_ok=True)
    body = b"PACK" + struct.pack(">II", 2, 1)
    offset = len(body)
    body += pack_header(4, len(data)) + zlib.compress(data)
    pack_sha = hashlib.sha1(body).digest()
    body += pack_sha
    raw = bytes.fromhex(sha)
    fanout = [0] * 256
    for i in range(raw[0], 256):
        fanout[i] = 1
    idx = b"\xfftOc" + struct.pack(">I", 2) + b"".join(struct.pack(">I", n) for n in fanout)
    idx += raw + struct.pack(">I", zlib.crc32(data)) + struct.pack(">I", offset) + pack_sha
    idx += hashlib.sha1(idx).digest()
    (folder / "pack-test.pack").write_bytes(body)
    (folder / "pack-test.idx").write_bytes(idx)


class Checkout(unittest.TestCase):
    def setUp(self):
        self.ev = load("evidence")
        self.root = pathlib.Path(tempfile.mkdtemp())
        self.git = self.root / ".git"
        (self.git / "refs" / "tags").mkdir(parents=True)
        (self.git / "HEAD").write_text(COMMIT + "\n")
        self.stamp({"schemaVersion": 2, "commit": COMMIT, "baseVersion": "0.21.5", "displayVersion": "0.21.5+15970.g4d04303", "distance": 15970, "tag": None})
        (self.git / "refs" / "tags" / "v0.22.3").write_text(OTHER + "\n")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def stamp(self, body):
        (self.root / "install-stamp.json").write_text(json.dumps(body), encoding="utf-8")

    def loose_tag(self, name, target=COMMIT):
        data = tag_object(target, name)
        sha = object_sha("tag", data)
        path = self.git / "objects" / sha[:2] / sha[2:]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(zlib.compress(f"tag {len(data)}".encode() + b"\0" + data))
        (self.git / "refs" / "tags" / name).write_text(sha + "\n")
        return sha

    def found(self):
        return self.ev.version_from_checkout(self.root)

    def test_an_annotated_tag_on_the_installed_commit_wins_over_the_stamp(self):
        self.loose_tag("v0.22.4")
        found = self.found()
        self.assertEqual((found["value"], found["source"], found["exact"]), ("0.22.4", "git tag", True))

    def test_an_annotated_tag_kept_in_a_pack_is_read_too(self):
        data = tag_object(COMMIT, "v0.22.4")
        sha = object_sha("tag", data)
        write_pack(self.git, sha, data)
        (self.git / "refs" / "tags" / "v0.22.4").write_text(sha + "\n")
        self.assertEqual(self.found()["value"], "0.22.4")

    def test_a_peeled_line_in_packed_refs_is_enough(self):
        (self.git / "packed-refs").write_text(
            "# pack-refs with: peeled fully-peeled sorted\n"
            f"{'2' * 40} refs/tags/v0.22.4\n^{COMMIT}\n"
            f"{'3' * 40} refs/tags/v0.22.2\n^{OTHER}\n"
        )
        self.assertEqual(self.found()["value"], "0.22.4")

    def test_a_lightweight_tag_on_the_commit_counts(self):
        (self.git / "refs" / "tags" / "v0.22.4").write_text(COMMIT + "\n")
        self.assertEqual(self.found()["value"], "0.22.4")

    def test_canary_and_other_tags_never_count(self):
        (self.git / "refs" / "tags" / "v0.22.5+canary.20261021T070232Z").write_text(COMMIT + "\n")
        found = self.found()
        self.assertEqual(found["value"], "0.21.5")
        self.assertFalse(found["exact"])

    def test_without_a_tag_the_stamp_base_is_reported_as_inexact(self):
        found = self.found()
        self.assertEqual(found["value"], "0.21.5")
        self.assertFalse(found["exact"])
        self.assertIn("15970", found["source"])

    def test_a_stamp_that_names_its_tag_is_exact(self):
        shutil.rmtree(self.git)
        self.stamp({"commit": COMMIT, "baseVersion": "0.22.4", "displayVersion": "0.22.4", "distance": 0, "tag": "v0.22.4"})
        self.assertEqual((self.found()["value"], self.found()["exact"]), ("0.22.4", True))

    def test_a_worktree_style_git_file_is_followed(self):
        real = self.root / "real-git"
        shutil.move(str(self.git), str(real))
        (self.root / ".git").write_text(f"gitdir: {real}\n")
        (real / "refs" / "tags" / "v0.22.4").write_text(COMMIT + "\n")
        self.assertEqual(self.found()["value"], "0.22.4")

    def test_head_on_a_branch_is_resolved_when_the_stamp_has_no_commit(self):
        self.stamp({"baseVersion": "0.21.5", "displayVersion": "0.21.5+3.gabc", "distance": 3})
        (self.git / "HEAD").write_text("ref: refs/heads/main\n")
        (self.git / "refs" / "heads").mkdir()
        (self.git / "refs" / "heads" / "main").write_text(COMMIT + "\n")
        (self.git / "refs" / "tags" / "v0.22.4").write_text(COMMIT + "\n")
        self.assertEqual(self.found()["value"], "0.22.4")

    def test_nothing_readable_gives_nothing(self):
        empty = pathlib.Path(tempfile.mkdtemp())
        try:
            self.assertEqual(self.ev.version_from_checkout(empty)["value"], "")
        finally:
            shutil.rmtree(empty)

    def test_detect_version_keeps_its_two_value_shape(self):
        found = self.ev.detect_version()
        self.assertIsInstance(found, tuple)
        self.assertEqual(len(found), 2)


if __name__ == "__main__":
    unittest.main()
