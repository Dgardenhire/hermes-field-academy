"""The public package: .public-exclude lists every private path (the pitch brief for Nous, its images and
generator, the CI setup, the draft catalog entry and PR, the demo notes, the status page), every listed path is real,
and nothing that ships links to a path that doesn't."""

import pathlib
import re
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MUST_DROP = (".github", "docs/brief-img", "docs/concept-brief-nous.html", "docs/make_brief.py", "docs/catalog",
             "docs/DEMO-NOTES.md", "docs/STATUS.md")


def excluded():
    out = []
    for line in (ROOT / ".public-exclude").read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.append(line)
    return out


def tracked():
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True)
    names = out.stdout.split() if out.returncode == 0 else []
    return names or [str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts]


def dropped(name, rules):
    return name == ".public-exclude" or any(name == r or name.startswith(r.rstrip("/") + "/") for r in rules)


@unittest.skipUnless((ROOT / ".public-exclude").exists(), "this is the public package: the exclude list was applied and removed")
class PublicPackage(unittest.TestCase):
    def test_every_private_path_is_listed(self):
        rules = excluded()
        for path in MUST_DROP:
            self.assertIn(path, rules)

    def test_every_listed_path_is_relative_and_real(self):
        for rule in excluded():
            self.assertFalse(rule.startswith("/") or ".." in rule, rule)
            self.assertTrue((ROOT / rule).exists(), f"{rule} is listed but not in the repo")

    def test_the_brief_never_ships(self):
        shipped = [n for n in tracked() if not dropped(n, excluded())]
        for name in shipped:
            self.assertNotRegex(name, r"concept-brief|make_brief|brief-img/|^\.github/|^docs/catalog/|DEMO-NOTES|STATUS\.md")

    def test_nothing_that_ships_links_to_a_dropped_path(self):
        rules = excluded()
        shipped = [n for n in tracked() if not dropped(n, rules) and n.endswith((".md", ".txt", ".html"))]
        for name in shipped:
            text = (ROOT / name).read_text(encoding="utf-8", errors="ignore")
            for rule in rules:
                if rule == ".github":
                    continue  # named in prose (a test's docstring), never linked
                self.assertNotIn(f"]({rule}", text, f"{name} links to {rule}")
                self.assertNotIn(f"]({rule.removeprefix('docs/')}", text if name.startswith("docs/") else "", f"{name} links to {rule}")


if __name__ == "__main__":
    unittest.main()
