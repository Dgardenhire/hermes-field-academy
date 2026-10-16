"""Lock and open lab files the way a learner does on each platform, for the tests.

Linux and macOS: chmod. Windows: icacls, the program a Windows learner runs, so the tests prove the plugin's check
accepts what the learner's own command leaves behind (and rejects what a careless setup leaves).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

ON_WINDOWS = os.name == "nt"

# On Windows: who to let in, and with which icacls rights, for each way a file can be left open.
WINDOWS_OPENERS = (
    ("*S-1-5-32-545", "(R)"),    # Users: every account on this computer
    ("*S-1-1-0", "(R)"),         # Everyone
    ("*S-1-5-11", "(R)"),        # Authenticated Users
    ("*S-1-5-32-546", "(R)"),    # Guests
    ("*S-1-1-0", "(W)"),         # Everyone may write (and so replace the keys)
    ("*S-1-5-32-545", "(F)"),    # Users: full control
)
POSIX_OPENERS = (0o644, 0o640, 0o604, 0o660, 0o777, 0o666)
OPENERS = WINDOWS_OPENERS if ON_WINDOWS else POSIX_OPENERS


def icacls(*args):
    out = subprocess.run(["icacls", *[str(a) for a in args]], capture_output=True, text=True)
    if out.returncode != 0:
        raise AssertionError(f"icacls {' '.join(map(str, args))} failed: {out.stdout} {out.stderr}")
    return out.stdout


def lock(path):
    """What the coaching tells a learner to do: chmod 600, or icacls /inheritance:r /grant:r "<you>:F"."""
    if ON_WINDOWS:
        icacls(path, "/inheritance:r", "/grant:r", f"{os.environ['USERDOMAIN']}\\{os.environ['USERNAME']}:F")
    else:
        os.chmod(path, 0o600)


def lock_in_powershell(path):
    """Windows only: the exact line the coaching shows, typed into PowerShell in the file's folder."""
    path = Path(path)
    command = 'icacls {name} /inheritance:r /grant:r "${{env:USERDOMAIN}}\\${{env:USERNAME}}:F"'.format(name=path.name)
    out = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", command], cwd=str(path.parent), capture_output=True, text=True)
    if out.returncode != 0:
        raise AssertionError(f"PowerShell: {command} failed: {out.stdout} {out.stderr}")
    return command


def open_up(path, opener=None):
    """Leave the file readable by others: a group or world mode, or an access-list entry for a group of accounts."""
    if ON_WINDOWS:
        who, rights = opener or WINDOWS_OPENERS[0]
        icacls(path, "/grant", f"{who}:{rights}")
    else:
        os.chmod(path, opener if opener is not None else 0o644)


def undo_open(path, opener=None):
    """Take back what open_up gave."""
    if ON_WINDOWS:
        who, _ = opener or WINDOWS_OPENERS[0]
        icacls(path, "/remove:g", who)
    else:
        os.chmod(path, 0o600)
