"""Where a connector may not reach in a practice profile. Read-only: it names paths only to refuse them.

Hermes's profiles.create mirrors the learner's sign-in into a new profile, and Hermes's own file tools refuse to read
those files and the other credential stores (agent/file_safety.py: _CREDENTIAL_FILE_NAMES and _READ_DENIED_DIRS). A
filesystem connector is a separate program with none of those guards, so practice_write.check_connector_reach refuses
any connector folder that is the profile's own folder, a folder above it, or one that holds or sits inside a path here.
Nothing in this module opens, lists or reads any of them.
"""

from __future__ import annotations

from pathlib import Path

SIGN_IN_PATHS = (".env", "auth.json", "auth.lock", ".anthropic_oauth.json", "webhook_subscriptions.json", "auth",
                 "mcp-tokens", "pairing", "platforms", "browser-profile", "vault", "webapp")


def _overlaps(a: Path, b: Path) -> bool:
    return a == b or a in b.parents or b in a.parents


def reaches_sign_in(home, raw) -> bool:
    """Would a connector folder argument ``raw`` reach the profile's own folder (or above) or any sign-in path?"""
    text = str(raw or "")
    if not text or text.startswith("-"):
        return False
    try:
        path = Path(text).expanduser()
        if not path.is_absolute():
            # A relative folder depends on where Hermes starts the connector, which could be the profile itself.
            return text in (".", "..") or text.startswith(("./", "../", ".\\", "..\\"))
        path = path.resolve(strict=False)
        root = Path(home).resolve(strict=False)
    except (OSError, ValueError, RuntimeError):
        return True
    if path == root or path in root.parents:
        return True
    return any(_overlaps(path, (root / name).resolve(strict=False)) for name in SIGN_IN_PATHS)
