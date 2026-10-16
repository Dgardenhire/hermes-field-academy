"""Catch the failure that blanks a plugin page: a component used but never imported.

A plugin file loads uncompiled, so a missing identifier is a ReferenceError at
render time. The app catches it in an error boundary and the pane goes empty
with no visible explanation. This walks the file, collects every identifier that
looks like a component or a helper, and checks each one is imported or defined
in the file itself.

Run:  python3 scripts/check_identifiers.py desktop/plugin.js
"""

import re
import sys
from pathlib import Path

# Anything the app or React provides for free.
GLOBALS = {
    "Array", "Boolean", "Date", "Error", "Infinity", "JSON", "Map", "Math", "NaN", "Number",
    "Object", "Promise", "Set", "String", "Symbol", "URL", "URLSearchParams", "WeakMap",
    "console", "document", "globalThis", "isFinite", "isNaN", "parseFloat", "parseInt",
    "setTimeout", "clearTimeout", "setInterval", "clearInterval", "window", "fetch",
    "undefined", "null", "true", "false", "BigInt", "Intl", "RegExp",
}


def declared_imports(source):
    names = set()
    for block in re.findall(r"import\s*\{([^}]*)\}\s*from", source):
        for part in block.split(","):
            token = part.strip().split(" as ")[-1].strip()
            if token:
                names.add(token)
    # default imports and namespace imports
    for match in re.findall(r"import\s+(\w+)\s*(?:,|from)", source):
        names.add(match)
    return names


def declared_locally(source):
    names = set()
    for pattern in (
        r"function\s+(\w+)\s*\(",
        r"const\s+(\w+)\s*=",
        r"let\s+(\w+)\s*=",
        r"class\s+(\w+)",
    ):
        names.update(re.findall(pattern, source))
    return names


def used_components(source):
    """Identifiers passed to jsx/jsxs as a component, plus JSX-style <Name ...>."""
    names = set()
    # jsx(Component, ...) / jsxs(Component, ...)  — capitalised first argument
    for match in re.findall(r"\bjsxs?\s*\(\s*([A-Z][A-Za-z0-9_]*)\s*,", source):
        names.add(match)
    # direct component references in children arrays: [jsx(X)] is covered above;
    # also catch bare `Component)` inside a child list via `<Name`
    for match in re.findall(r"<([A-Z][A-Za-z0-9_]*)[\s/>]", source):
        names.add(match)
    return names


def main(path):
    source = Path(path).read_text()
    declared = declared_imports(source) | declared_locally(source) | GLOBALS
    missing = sorted(used_components(source) - declared)
    if missing:
        print(f"MISSING from {path}: {', '.join(missing)}")
        return 1
    print(f"OK: every component in {path} is imported or defined")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "desktop/plugin.js"))
