"""Fail when a plugin uses a Tailwind class the app never compiled.

The desktop stylesheet is compiled at BUILD time from app sources. A plugin
file is loaded at runtime and is never scanned, so an arbitrary-value utility
invented while writing the pane (``text-[10.5px]``, ``grid-cols-[30px_1fr]``)
may be absent from the shipped CSS. The pane then renders unstyled or collapsed
with no error anywhere — no toast, no log line, nothing.

This checks every arbitrary-value class in the plugin against the real
compiled stylesheet, so the failure is loud and happens before the user sees it.

Classes the plugin ships itself (prefixed, defined in its own ``<style>`` block)
are exempt: those are guaranteed present because the plugin carries them.

Usage:
    python3 scripts/check_plugin_css.py desktop/plugin.js
    python3 scripts/check_plugin_css.py desktop/plugin.js --css path/to/index.css

Exit 1 on any uncompiled class, or on a failed self-test of the checker.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Values that are fine to hand-write because the app already compiles them for
# its own use. Kept explicit: an allow-list that grows silently is not a guard.
ALLOWLIST: set[str] = set()

# Proves the checker works before it accuses anyone. If this class is not found
# in the stylesheet, the escaping or the CSS path is wrong and every result
# would be a false positive.
SELF_TEST_CLASS = "tracking-[0.12em]"

ESCAPES = {
    "[": r"\[", "]": r"\]", ".": r"\.", "(": r"\(", ")": r"\)", "%": r"\%",
    "#": r"\#", "/": r"\/", ",": r"\,", ":": r"\:", "!": r"\!", "+": r"\+",
    "'": r"\'", '"': r"\"", "&": r"\&", "*": r"\*", ">": r"\>", "~": r"\~",
    "=": r"\=", "@": r"\@", " ": r"\_", "^": r"\^", "$": r"\$", "|": r"\|",
    "{": r"\{", "}": r"\}", ";": r"\;",
}


def tailwind_escape(cls: str) -> str:
    return "".join(ESCAPES.get(ch, ch) for ch in cls)


def class_names(source: str) -> set[str]:
    """Every class token that carries an arbitrary value (contains [ ])."""
    found: set[str] = set()
    for literal in re.findall(r"className:\s*'([^']*)'", source):
        for token in literal.split():
            if "[" in token and "]" in token:
                found.add(token)
    for literal in re.findall(r"className:\s*`([^`]*)`", source):
        for token in literal.split():
            if "[" in token and "]" in token:
                found.add(token)
    return found


def own_classes(source: str) -> set[str]:
    """Classes the plugin defines in its own <style> block."""
    own: set[str] = set()
    for block in re.findall(r"const CSS = `(.*?)`", source, re.S):
        own.update(re.findall(r"\.([A-Za-z][\w-]*)", block))
    return own


def find_stylesheets(explicit: str | None) -> list[Path]:
    """Every compiled stylesheet in the app bundle.

    Not just the first: the assets directory holds several (glyph-spinner-*.css
    sorts before index-*.css), and reading only one makes every check a false
    positive. Concatenate them all.
    """
    if explicit:
        p = Path(explicit)
        return [p] if p.is_file() else []
    for root in (Path.home() / ".hermes" / "hermes-agent", Path.cwd()):
        assets = root / "apps" / "desktop" / "dist" / "assets"
        if assets.is_dir():
            found = sorted(assets.glob("*.css"))
            if found:
                return found
    return []


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Fail when a plugin uses a Tailwind class the app never compiled.")
    ap.add_argument("plugin", nargs="?", default="desktop/plugin.js")
    ap.add_argument("--css", default=None, help="path to the app's compiled stylesheet")
    opts = ap.parse_args(argv)

    src_path = Path(opts.plugin)
    if not src_path.is_file():
        print(f"ERROR: no plugin file at {src_path}", file=sys.stderr)
        return 2
    source = src_path.read_text(encoding="utf-8")

    sheets = find_stylesheets(opts.css)
    if not sheets:
        print(
            "SKIP: no compiled stylesheet found (looked for "
            "apps/desktop/dist/assets/*.css). Pass --css to check anyway.",
            file=sys.stderr,
        )
        return 0
    css = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in sheets)

    # Self-test: the checker must find a class the app definitely compiles.
    if tailwind_escape(SELF_TEST_CLASS) not in css:
        print(
            f"ERROR: self-test failed — {SELF_TEST_CLASS} (escaped "
            f"{tailwind_escape(SELF_TEST_CLASS)}) is not in any of "
            f"{len(sheets)} stylesheet(s). The checker cannot be trusted; fix it "
            "before believing any result.",
            file=sys.stderr,
        )
        return 2

    used = class_names(source)
    own = own_classes(source)
    uncompiled = sorted(
        cls for cls in used
        if cls not in ALLOWLIST
        and cls not in own
        and tailwind_escape(cls) not in css
    )

    print(f"checked {len(used)} arbitrary-value class(es) in {src_path.name}")
    print(f"  stylesheets: {len(sheets)} file(s), {len(css):,} bytes")
    print(f"  shipped by the plugin: {', '.join(sorted(own)) or 'none'}")
    if uncompiled:
        print(f"\nUNCOMPILED ({len(uncompiled)}): the app's build never emits these rules")
        for cls in uncompiled:
            print(f"  - {cls}")
        print(
            "\nFix: use a compiled utility, or ship the rule yourself in the plugin's "
            "own <style> block under a prefixed class."
        )
        return 1
    print("OK: every arbitrary-value class resolves in the shipped stylesheet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
