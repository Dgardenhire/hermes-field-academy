"""Release checks for an outside reviewer: the manifest, the catalog entry and
register() agree; versions agree everywhere; the shipped tree carries no personal
paths or secrets; the reviewer documents exist and say the honest things; the home
banner is inline SVG drawn from theme variables with every camp on the mountain."""

import hashlib
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

from support import AcademyCase

ROOT = Path(__file__).resolve().parents[1]


def _block(path, key):
    """A `key:` list in a YAML file, with the indent of every item."""
    items, inside = [], False
    for line in (ROOT / path).read_text(encoding="utf-8").splitlines():
        if re.match(rf"^\s*{key}:\s*$", line):
            inside = True
            continue
        if inside:
            item = re.match(r"^(\s+)-\s+(\S+)\s*$", line)
            if item:
                items.append((len(item.group(1)), item.group(2)))
            elif line.strip():
                break
    return items


def _shipped_files():
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True)
    names = out.stdout.split() if out.returncode == 0 else []
    if not names:
        names = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts]
    extra = ["REVIEWER-GUIDE.md", "docs/paths.md", "desktop/src/banner.js", "tests/test_release.py"]
    return sorted(set(names) | {n for n in extra if (ROOT / n).exists()})


class ManifestTests(AcademyCase):
    def registered(self):
        tools, hooks = [], []

        class Ctx:
            def register_tool(self, name, **kwargs):
                tools.append(name)

            def register_hook(self, name, *args, **kwargs):
                hooks.append(name)

            def register_command(self, *args, **kwargs):
                pass

            def register_skill(self, *args, **kwargs):
                pass

        self.pkg.register(Ctx())
        return tools, hooks

    def test_plugin_yaml_declares_exactly_what_register_registers(self):
        tools, hooks = self.registered()
        self.assertEqual([n for _, n in _block("plugin.yaml", "provides_tools")], tools)
        self.assertEqual([n for _, n in _block("plugin.yaml", "provides_hooks")], hooks)

    def test_catalog_entry_lists_are_evenly_indented(self):
        """A misindented item reads as a list item to a loose parser and as a YAML error to the catalog CI."""
        for key in ("provides_tools", "provides_hooks"):
            indents = {indent for indent, _ in _block("catalog-entry.yaml", key)}
            self.assertEqual(len(indents), 1, f"catalog-entry.yaml {key} items are indented {sorted(indents)}")


class VersionTests(unittest.TestCase):
    def version(self):
        return re.search(r"^version:\s*(\S+)", (ROOT / "plugin.yaml").read_text(encoding="utf-8"), re.M).group(1)

    def test_versions_agree(self):
        version = self.version()
        self.assertEqual(version, "0.8.4")
        catalog = re.search(r'^version:\s*"?([^"\s]+)"?', (ROOT / "catalog-entry.yaml").read_text(encoding="utf-8"), re.M).group(1)
        self.assertEqual(catalog, version)
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        first = re.search(r"^## (\S+)", changelog, re.M).group(1)
        self.assertEqual(first.lstrip("v"), version)


class ShippedTreeTests(unittest.TestCase):
    PERSONAL = re.compile(r"/Users/(?!you\b|a b/|a%20b/)[A-Za-z]")
    # Private names that must never ship, stored only as truncated SHA-256 hashes of
    # lowercase word runs (1 to 5 words) so this guard does not itself name them.
    PRIVATE_HASHES = frozenset({
        "3ffdd6848d404beb", "92bf236c5aaaab8a", "bef8d4d6b3527300", "3c7444cc78eb62ac",
        "be83a596a691393c", "b85ee1167bf8f05f", "4d8a17dac9ef3596", "be03e7a0c479093f",
        "d322ab4916e6be6b", "480887c948adc6be", "8e3fd81f1c31fdab", "4a1e28f0d8cfae74",
        "886f6f8499f38f0e", "269053a3a2570733", "497e71c8f7558307", "b6f7e96bcce09432",
        "4cf66e281e9a6949", "ee40e240072a8250", "8a560a0476415da9", "7e17bc31796114a5",
        "c36ba8dff84f087f", "4858a5e7e179e714", "7a851bb57fc3b70b", "706120e0fc362daa",
    })
    SECRET = re.compile(r"sk-[A-Za-z0-9]{24,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|xox[bp]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----")

    def test_no_personal_paths_private_names_or_secrets_ship(self):
        problems = []
        for name in _shipped_files():
            path = ROOT / name
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".ico"} or not path.exists():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if name == "tests/test_release.py":
                continue
            for pattern in (self.PERSONAL, self.SECRET):
                hit = pattern.search(text)
                if hit:
                    problems.append(f"{name}: {hit.group(0)!r}")
            # A link to the public site (a .studio domain) is an address, not a name; the bare name stays barred.
            words = re.findall(r"[a-z0-9]+", re.sub(r"\b[\w-]+\.studio\b", " ", text.lower()))
            for size in range(1, 6):
                for i in range(len(words) - size + 1):
                    phrase = " ".join(words[i:i + size])
                    if hashlib.sha256(phrase.encode()).hexdigest()[:16] in self.PRIVATE_HASHES:
                        problems.append(f"{name}: a private name (word {i + 1})")
        self.assertEqual(problems, [])

    def test_the_reviewer_list_ships_empty_and_says_why(self):
        data = json.loads((ROOT / "reviewers" / "trusted-reviewers.json").read_text(encoding="utf-8"))
        self.assertEqual(data["reviewers"], [])
        self.assertIn("awaiting review", data["about"])


class ReviewerDocsTests(unittest.TestCase):
    def test_readme_covers_what_an_outside_reviewer_needs(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for needle in ("## Install", "## What is verified", "## Privacy", "## License", "CREDITS.md", "REVIEWER-GUIDE.md", "docs/shots/"):
            self.assertIn(needle, text, needle)

    def test_readme_screenshots_exist(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        shots = re.findall(r"\]\((docs/shots/[^)]+)\)", text)
        self.assertGreaterEqual(len(shots), 4)
        for shot in shots:
            self.assertTrue((ROOT / shot).exists(), shot)

    def test_reviewer_guide_names_the_open_questions(self):
        text = (ROOT / "REVIEWER-GUIDE.md").read_text(encoding="utf-8")
        for needle in ("10 minutes", "reviewer list", "chooses their reviewer", "Not issued or endorsed by Nous Research", "harness/shoot.py"):
            self.assertIn(needle, text, needle)
        self.assertNotIn("proposal for Nous", text)

    def test_paths_doc_gives_each_path_a_use_case_pain_and_rationale(self):
        text = (ROOT / "docs" / "paths.md").read_text(encoding="utf-8")
        for path in ("Messenger", "Traveler", "Crossroads", "Boundary Keeper", "Guide"):
            self.assertIn(f"## {path}", text)
        self.assertGreaterEqual(text.count("**Use case.**"), 5)
        self.assertGreaterEqual(text.count("**Pain it solves.**"), 5)
        self.assertGreaterEqual(text.count("**Why this shape.**"), 5)

    def test_credits_name_everyone_the_content_draws_on(self):
        text = (ROOT / "CREDITS.md").read_text(encoding="utf-8")
        for name in ("Learning Path", "Tonbi", "Kevin Simback", "Hermes Bible", "Tony Simons", "Orgo"):
            self.assertIn(name, text, name)

    def test_license_is_mit(self):
        self.assertTrue((ROOT / "LICENSE").read_text(encoding="utf-8").startswith("MIT License"))


class BannerTests(unittest.TestCase):
    SRC = (ROOT / "desktop" / "src" / "banner.js").read_text(encoding="utf-8")

    def ridge(self, name):
        d = re.search(rf"{name}: '([^']+)'", self.SRC).group(1)
        return [(float(x), float(y)) for x, y in re.findall(r"L?(\d+(?:\.\d+)?) (\d+(?:\.\d+)?)", d.split(" L1200 320")[0].lstrip("M"))]

    @staticmethod
    def height_at(points, x):
        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            if x0 <= x <= x1:
                return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
        raise AssertionError(f"x={x} is off the ridge")

    def camps(self):
        block = re.search(r"BANNER_CAMPS = \[(.*?)\]", self.SRC, re.S).group(1)
        return [(float(x), float(y)) for x, y in re.findall(r"x: (\d+), y: (\d+)", block)]

    def test_every_camp_stands_on_the_mountain_face_in_view(self):
        main, near = self.ridge("main"), self.ridge("near")
        camps = self.camps()
        self.assertEqual(len(camps), 5)
        for x, y in camps:
            self.assertGreater(y, self.height_at(main, x), f"camp at {x} floats above the crest")
            self.assertLess(y, self.height_at(near, x), f"camp at {x} is hidden behind the near ridge")
        summit = re.search(r"BANNER_SUMMIT = \{ x: (\d+), y: (\d+) \}", self.SRC)
        sx, sy = float(summit.group(1)), float(summit.group(2))
        self.assertAlmostEqual(self.height_at(main, sx), sy, delta=0.5)

    def test_the_banner_is_inline_and_themed(self):
        self.assertNotRegex(self.SRC, r"<img|jsx\('img'|https?://|\.png|\.jpg")
        css = re.search(r"BANNER_CSS = `(.*?)`", self.SRC, re.S).group(1)
        self.assertNotRegex(css, r"#[0-9a-fA-F]{3,8}\b|rgb\(|hsl\(", "colours must come from theme variables")
        self.assertIn("@container (max-width:640px)", css)
        self.assertIn("prefers-reduced-motion", css)

    def test_the_home_page_draws_the_banner_and_the_build_carries_it(self):
        page = (ROOT / "desktop" / "src" / "plugin.js").read_text(encoding="utf-8")
        self.assertIn("jsx(Banner,", page)
        self.assertIn("BANNER_CSS", page)
        built = (ROOT / "desktop" / "plugin.js").read_text(encoding="utf-8")
        self.assertIn("fa-bn-art", built)
        self.assertIn("Learn Hermes by doing real work", built)


if __name__ == "__main__":
    unittest.main()
