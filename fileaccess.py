"""Who can read a file, asked the way each platform keeps the answer.

Linux and macOS keep it in a file's mode bits: ``chmod 600`` leaves only the owner able to read and
write it. Windows keeps it in the file's access list (its ACL): a list of accounts and what each may
do. A file is private on Windows when nothing on that list lets in anyone but you, Windows itself
(SYSTEM) and the computer's administrators, the three accounts Windows gives every file in your own
folders. Hermes on Windows keeps its keys in ``%LOCALAPPDATA%\\hermes\\.env``, which is private that
way by default. A file in a folder that lets every account read (a shared folder, or one made at the
top of a drive) is not, and the learner locks it the way Windows administrators do:

    icacls .env /inheritance:r /grant:r "${env:USERDOMAIN}\\${env:USERNAME}:F"

On Windows this module reads and writes access lists through the Windows security API (advapi32)
with ctypes, from the standard library. It runs no program and reaches no network. It reads a
file's access list to grade a lab, and writes one in two places only: when the lab builder makes a
lab folder, and when the reviewer's script makes its secret key file.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

ON_WINDOWS = os.name == "nt"

# The accounts every file in your own Windows folders already lists: you, Windows itself and the administrators.
SYSTEM_SID = "S-1-5-18"
ADMINISTRATORS_SID = "S-1-5-32-544"
USERS_SID = "S-1-5-32-545"
OWNER_RIGHTS_SID = "S-1-3-4"
# Names for the accounts a learner is likely to meet on a list. Anything else is shown as its SID.
WELL_KNOWN = {
    "S-1-1-0": "Everyone",
    "S-1-5-11": "Authenticated Users",
    USERS_SID: "Users",
    "S-1-5-32-546": "Guests",
    "S-1-5-32-547": "Power Users",
    "S-1-5-7": "Anonymous",
    "S-1-5-4": "Interactive",
    "S-1-5-2": "Network",
    "S-1-3-4": "Owner Rights",
    "S-1-15-2-1": "All Application Packages",
}

# The PowerShell line a learner types in the lab folder to lock one file, with the file's path in place of {path}.
WINDOWS_LOCK_COMMAND = 'icacls {path} /inheritance:r /grant:r "${{env:USERDOMAIN}}\\${{env:USERNAME}}:F"'


def is_private(path) -> bool:
    """True when only the file's owner can read or change it (Linux, macOS) or only you, SYSTEM and the administrators can (Windows)."""
    return not others(path)


def others(path) -> list:
    """Who else can get at the file's contents, as short readable names. Empty when the file is private."""
    path = Path(path)
    if not ON_WINDOWS:
        mode = stat.S_IMODE(path.stat().st_mode)
        return [f"mode {mode:o}"] if mode & 0o077 else []
    return [WELL_KNOWN.get(sid, sid) for sid in _win_others(str(path))]


def make_private(path) -> None:
    """Leave only the owner on the file: chmod 600, or on Windows an access list naming only you (not inherited from the folder)."""
    if not ON_WINDOWS:
        os.chmod(path, 0o600)
        return
    _win_set_private(str(path))


def make_shared_folder(folder) -> None:
    """Create a new folder (it must not exist). On Windows it is created with its access list already in place, in one
    call: you, SYSTEM and the administrators with full control, and every account on this computer (Users) allowed to
    read and run it and whatever is made in it later, the way a folder at the top of a drive allows. Nothing is
    inherited from the folder above. The lab builder uses it so a lab's files start the way a careless install leaves
    them. Refuses when either folder above it is a junction or a link."""
    folder = Path(folder)
    for above in (folder.parent, folder.parent.parent):
        if is_link_or_junction(above):
            raise OSError(f"{above} is a link or a junction, so no lab folder is made through it")
    if not ON_WINDOWS:
        folder.mkdir()
        return
    _win_create_shared_folder(str(folder))


def is_link_or_junction(path) -> bool:
    """True for a symbolic link, and on Windows for any reparse point (a junction, a mount point)."""
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return False
    if stat.S_ISLNK(info.st_mode):
        return True
    return bool(getattr(info, "st_file_attributes", 0) & 0x400)  # FILE_ATTRIBUTE_REPARSE_POINT


def create_private(path) -> int:
    """Create a new file that only you can read and return an open, writable file descriptor. Fails if the file exists.
    The file is private from the moment it exists, so its contents are never readable by anyone else, even briefly."""
    if not ON_WINDOWS:
        return os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    return _win_create_private(str(path))


def keeps_access_lists(path) -> bool:
    """False on a Windows drive that keeps no access lists (FAT32, exFAT, many USB sticks), where no file can be private."""
    if not ON_WINDOWS:
        return True
    return _win_keeps_acls(str(path))


# ------------------------------------------------------------------------------------------------- Windows --
#
# Everything below runs on Windows only. Each Windows call's result is checked and a failure raises OSError, so a
# file whose access list cannot be read is never reported private.

_api = None


def _windows():
    """Load the Windows security calls once, with their argument and result types declared."""
    global _api
    if _api is not None:
        return _api
    import ctypes
    from ctypes import wintypes

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    PSID = ctypes.c_void_p
    PACL = ctypes.c_void_p
    PSD = ctypes.c_void_p

    def fn(dll, name, restype, *argtypes):
        f = getattr(dll, name)
        f.restype = restype
        f.argtypes = list(argtypes)
        return f

    api = {
        "ctypes": ctypes,
        "wintypes": wintypes,
        "GetNamedSecurityInfoW": fn(advapi32, "GetNamedSecurityInfoW", wintypes.DWORD, wintypes.LPCWSTR, ctypes.c_int, wintypes.DWORD,
                                    ctypes.POINTER(PSID), ctypes.POINTER(PSID), ctypes.POINTER(PACL), ctypes.POINTER(PACL), ctypes.POINTER(PSD)),
        "SetNamedSecurityInfoW": fn(advapi32, "SetNamedSecurityInfoW", wintypes.DWORD, wintypes.LPWSTR, ctypes.c_int, wintypes.DWORD,
                                    PSID, PSID, PACL, PACL),
        "GetAce": fn(advapi32, "GetAce", wintypes.BOOL, PACL, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p)),
        "IsValidSid": fn(advapi32, "IsValidSid", wintypes.BOOL, PSID),
        "IsValidAcl": fn(advapi32, "IsValidAcl", wintypes.BOOL, PACL),
        "GetLengthSid": fn(advapi32, "GetLengthSid", wintypes.DWORD, PSID),
        "ConvertSidToStringSidW": fn(advapi32, "ConvertSidToStringSidW", wintypes.BOOL, PSID, ctypes.POINTER(wintypes.LPWSTR)),
        "ConvertStringSidToSidW": fn(advapi32, "ConvertStringSidToSidW", wintypes.BOOL, wintypes.LPCWSTR, ctypes.POINTER(PSID)),
        "InitializeAcl": fn(advapi32, "InitializeAcl", wintypes.BOOL, PACL, wintypes.DWORD, wintypes.DWORD),
        "AddAccessAllowedAceEx": fn(advapi32, "AddAccessAllowedAceEx", wintypes.BOOL, PACL, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, PSID),
        "InitializeSecurityDescriptor": fn(advapi32, "InitializeSecurityDescriptor", wintypes.BOOL, PSD, wintypes.DWORD),
        "SetSecurityDescriptorDacl": fn(advapi32, "SetSecurityDescriptorDacl", wintypes.BOOL, PSD, wintypes.BOOL, PACL, wintypes.BOOL),
        "SetSecurityDescriptorControl": fn(advapi32, "SetSecurityDescriptorControl", wintypes.BOOL, PSD, wintypes.WORD, wintypes.WORD),
        "OpenProcessToken": fn(advapi32, "OpenProcessToken", wintypes.BOOL, wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)),
        "GetTokenInformation": fn(advapi32, "GetTokenInformation", wintypes.BOOL, wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                  wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)),
        "GetCurrentProcess": fn(kernel32, "GetCurrentProcess", wintypes.HANDLE),
        "CloseHandle": fn(kernel32, "CloseHandle", wintypes.BOOL, wintypes.HANDLE),
        "LocalFree": fn(kernel32, "LocalFree", ctypes.c_void_p, ctypes.c_void_p),
        "SetSecurityInfo": fn(advapi32, "SetSecurityInfo", wintypes.DWORD, wintypes.HANDLE, ctypes.c_int, wintypes.DWORD, PSID, PSID, PACL, PACL),
        "GetFileInformationByHandle": fn(kernel32, "GetFileInformationByHandle", wintypes.BOOL, wintypes.HANDLE, ctypes.c_void_p),
        "CreateDirectoryW": fn(kernel32, "CreateDirectoryW", wintypes.BOOL, wintypes.LPCWSTR, ctypes.c_void_p),
        "CreateFileW": fn(kernel32, "CreateFileW", wintypes.HANDLE, wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                          wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE),
        "GetVolumePathNameW": fn(kernel32, "GetVolumePathNameW", wintypes.BOOL, wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD),
        "GetVolumeInformationW": fn(kernel32, "GetVolumeInformationW", wintypes.BOOL, wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD,
                                    ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD),
                                    wintypes.LPWSTR, wintypes.DWORD),
    }
    _api = api
    return api


SE_FILE_OBJECT = 1
OWNER_SECURITY_INFORMATION = 0x1
DACL_SECURITY_INFORMATION = 0x4
PROTECTED_DACL_SECURITY_INFORMATION = 0x80000000
ACL_REVISION = 2
SECURITY_DESCRIPTOR_REVISION = 1
SE_DACL_PROTECTED = 0x1000
READ_CONTROL = 0x00020000
WRITE_DAC = 0x00040000
FILE_SHARE_ALL = 0x7
OPEN_EXISTING = 3
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
FILE_ATTRIBUTE_DIRECTORY = 0x10
FILE_ATTRIBUTE_REPARSE_POINT = 0x400
TOKEN_QUERY = 0x0008
TOKEN_USER_CLASS = 1
INHERIT_ONLY_ACE = 0x08
OBJECT_INHERIT_ACE = 0x01
CONTAINER_INHERIT_ACE = 0x02
ACCESS_ALLOWED_ACE_TYPE = 0x0
ACCESS_DENIED_TYPES = {0x1, 0x6, 0xA, 0xC}
# Rights that let an account read or change what the file holds, or take the file over and then do so.
DATA_RIGHTS = (0x0001 | 0x0002 | 0x0004   # read data, write data, append data
               | 0x0020                   # execute (counted: a reader of keys has no business running them either)
               | 0x20000000               # generic execute
               | 0x00040000 | 0x00080000  # change the access list, take ownership
               | 0x02000000               # maximum allowed
               | 0x10000000 | 0x40000000 | 0x80000000)  # generic all, generic write, generic read
FILE_ALL_ACCESS = 0x001F01FF
READ_AND_EXECUTE = 0x001200A9  # what icacls calls (RX)
GENERIC_WRITE = 0x40000000
CREATE_NEW = 1
FILE_ATTRIBUTE_NORMAL = 0x80
ERROR_FILE_EXISTS = 80
FILE_PERSISTENT_ACLS = 0x00000008


def _check(ok, what):
    if not ok:
        api = _windows()
        code = api["ctypes"].get_last_error()
        raise OSError(code, f"{what} failed (Windows error {code})")


def _sid_string(psid) -> str:
    api = _windows()
    ctypes, wintypes = api["ctypes"], api["wintypes"]
    _check(api["IsValidSid"](psid), "IsValidSid")
    text = wintypes.LPWSTR()
    _check(api["ConvertSidToStringSidW"](psid, ctypes.byref(text)), "ConvertSidToStringSidW")
    try:
        return text.value
    finally:
        api["LocalFree"](ctypes.cast(text, ctypes.c_void_p))


class _Sid:
    """A SID made from its string form, freed when the block ends."""

    def __init__(self, text):
        api = _windows()
        self.api = api
        self.ptr = api["ctypes"].c_void_p()
        _check(api["ConvertStringSidToSidW"](text, api["ctypes"].byref(self.ptr)), "ConvertStringSidToSidW")

    def __enter__(self):
        return self.ptr

    def __exit__(self, *exc):
        self.api["LocalFree"](self.ptr)


def _current_user():
    """(the running account's SID as text, a buffer holding its binary SID, a pointer into that buffer)."""
    api = _windows()
    ctypes, wintypes = api["ctypes"], api["wintypes"]
    token = wintypes.HANDLE()
    _check(api["OpenProcessToken"](api["GetCurrentProcess"](), TOKEN_QUERY, ctypes.byref(token)), "OpenProcessToken")
    try:
        need = wintypes.DWORD(0)
        api["GetTokenInformation"](token, TOKEN_USER_CLASS, None, 0, ctypes.byref(need))
        if not need.value:
            _check(False, "GetTokenInformation (size)")
        buffer = (ctypes.c_ulonglong * ((need.value + 7) // 8))()
        _check(api["GetTokenInformation"](token, TOKEN_USER_CLASS, buffer, need, ctypes.byref(need)), "GetTokenInformation")
    finally:
        api["CloseHandle"](token)
    # TOKEN_USER starts with SID_AND_ATTRIBUTES, whose first field is the pointer to the SID (inside the same buffer).
    psid = ctypes.c_void_p.from_buffer(buffer).value
    return _sid_string(psid), buffer, psid


def _allowed_sids():
    return {_current_user()[0], SYSTEM_SID, ADMINISTRATORS_SID}


def _win_others(path: str) -> list:
    """The SIDs, other than you, SYSTEM and the administrators, that can read or change the file: its owner (who can
    always rewrite the access list) when that is anyone else, and every entry on the list that lets someone in."""
    api = _windows()
    ctypes = api["ctypes"]
    owner = ctypes.c_void_p()
    dacl = ctypes.c_void_p()
    descriptor = ctypes.c_void_p()
    err = api["GetNamedSecurityInfoW"](path, SE_FILE_OBJECT, OWNER_SECURITY_INFORMATION | DACL_SECURITY_INFORMATION,
                                       ctypes.byref(owner), None, ctypes.byref(dacl), None, ctypes.byref(descriptor))
    if err:
        raise OSError(err, f"could not read the access list of {path} (Windows error {err})")
    try:
        allowed = _allowed_sids()
        found = []
        if not owner.value:
            found.append("an owner this check cannot read")
        else:
            owner_sid = _sid_string(owner)
            if owner_sid not in allowed:
                found.append(owner_sid)  # the owner can change the list at any time, even an empty one
            else:
                allowed.add(OWNER_RIGHTS_SID)  # an Owner Rights entry speaks for the owner, who is you or Windows here
        if not dacl.value:
            return found + ["S-1-1-0"]  # no access list at all: Windows lets everyone in
        _check(api["IsValidAcl"](dacl), "IsValidAcl")
        count = ctypes.c_ushort.from_address(dacl.value + 4).value  # ACL: revision, sbz1, size (2 bytes), count (2 bytes), sbz2
        for index in range(count):
            ace = ctypes.c_void_p()
            _check(api["GetAce"](dacl, index, ctypes.byref(ace)), "GetAce")
            ace_type = ctypes.c_ubyte.from_address(ace.value).value
            ace_flags = ctypes.c_ubyte.from_address(ace.value + 1).value
            if ace_flags & INHERIT_ONLY_ACE or ace_type in ACCESS_DENIED_TYPES:
                continue  # an entry for files made later, or one that takes access away
            if ace_type not in (ACCESS_ALLOWED_ACE_TYPE, 0x9):  # allowed, allowed-callback: header, mask, then the SID
                found.append(f"an entry this check cannot read (type {ace_type})")
                continue
            mask = ctypes.c_uint32.from_address(ace.value + 4).value
            if not mask & DATA_RIGHTS:
                continue
            sid = _sid_string(ctypes.c_void_p(ace.value + 8))
            if sid not in allowed and sid not in found:
                found.append(sid)
        return found
    finally:
        api["LocalFree"](descriptor)


def _acl_with(entries):
    """A new access list holding (SID pointer, rights, inheritance flags) entries. Returns the buffer that holds it."""
    api = _windows()
    ctypes = api["ctypes"]
    size = 8 + sum(8 + api["GetLengthSid"](sid) for sid, _, _ in entries)
    size = (size + 3) & ~3
    buffer = (ctypes.c_uint32 * (size // 4))()
    _check(api["InitializeAcl"](buffer, size, ACL_REVISION), "InitializeAcl")
    for sid, rights, flags in entries:
        _check(api["AddAccessAllowedAceEx"](buffer, ACL_REVISION, flags, rights, sid), "AddAccessAllowedAceEx")
    return buffer


def _win_set_private(path: str) -> None:
    """The access list icacls /inheritance:r /grant:r "<you>:F" leaves: you, with full control, and nothing inherited."""
    api = _windows()
    _, keep_alive, me = _current_user()
    acl = _acl_with([(me, FILE_ALL_ACCESS, 0)])
    err = api["SetNamedSecurityInfoW"](path, SE_FILE_OBJECT, DACL_SECURITY_INFORMATION | PROTECTED_DACL_SECURITY_INFORMATION, None, None, acl, None)
    del keep_alive
    if err:
        raise OSError(err, f"could not lock {path} (Windows error {err})")


def _security_attributes(acl, protected):
    """(SECURITY_ATTRIBUTES, the buffers it points into) for a new file or folder with this access list."""
    api = _windows()
    ctypes = api["ctypes"]
    descriptor = (ctypes.c_ulonglong * 8)()  # SECURITY_DESCRIPTOR is 40 bytes on 64-bit Windows, 20 on 32-bit
    _check(api["InitializeSecurityDescriptor"](descriptor, SECURITY_DESCRIPTOR_REVISION), "InitializeSecurityDescriptor")
    _check(api["SetSecurityDescriptorDacl"](descriptor, True, acl, False), "SetSecurityDescriptorDacl")
    if protected:
        _check(api["SetSecurityDescriptorControl"](descriptor, SE_DACL_PROTECTED, SE_DACL_PROTECTED), "SetSecurityDescriptorControl")

    class SECURITY_ATTRIBUTES(ctypes.Structure):
        _fields_ = [("nLength", ctypes.c_uint32), ("lpSecurityDescriptor", ctypes.c_void_p), ("bInheritHandle", ctypes.c_int)]

    return SECURITY_ATTRIBUTES(ctypes.sizeof(SECURITY_ATTRIBUTES), ctypes.addressof(descriptor), 0), (descriptor, acl)


def _win_create_shared_folder(path: str) -> None:
    """CreateDirectoryW with a protected access list, so the folder never has any other list. Then the same list is
    written once more through a handle to that very folder (opened without following a junction, and checked not to
    be one), because only the security API's own write marks the list auto-inherited. Without that mark, files made
    in the folder get plain copies of its entries instead of inherited ones, and icacls /inheritance:r would leave
    Users on them. No path-based write, so nothing can redirect it."""
    api = _windows()
    ctypes = api["ctypes"]
    inherit = OBJECT_INHERIT_ACE | CONTAINER_INHERIT_ACE
    _, keep_alive, me = _current_user()
    with _Sid(USERS_SID) as users, _Sid(SYSTEM_SID) as system, _Sid(ADMINISTRATORS_SID) as admins:
        acl = _acl_with([(me, FILE_ALL_ACCESS, inherit), (system, FILE_ALL_ACCESS, inherit), (admins, FILE_ALL_ACCESS, inherit),
                         (users, READ_AND_EXECUTE, inherit)])
        attributes, buffers = _security_attributes(acl, protected=True)
        ok = api["CreateDirectoryW"](path, ctypes.byref(attributes))
        code = ctypes.get_last_error()
        if not ok:
            if code == 183:  # ERROR_ALREADY_EXISTS
                raise FileExistsError(code, "The folder already exists", path)
            raise OSError(code, f"could not create {path} (Windows error {code})")
        handle = api["CreateFileW"](path, READ_CONTROL | WRITE_DAC, FILE_SHARE_ALL, None, OPEN_EXISTING,
                                    FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT, None)
        if handle is None or handle == ctypes.c_void_p(-1).value:
            code = ctypes.get_last_error()
            raise OSError(code, f"could not open {path} (Windows error {code})")
        try:
            info = (ctypes.c_uint32 * 13)()  # BY_HANDLE_FILE_INFORMATION; its first field is the attributes
            _check(api["GetFileInformationByHandle"](handle, info), "GetFileInformationByHandle")
            if info[0] & FILE_ATTRIBUTE_REPARSE_POINT or not info[0] & FILE_ATTRIBUTE_DIRECTORY:
                raise OSError(f"{path} is not the plain folder just made, so its access list was not written")
            err = api["SetSecurityInfo"](handle, SE_FILE_OBJECT, DACL_SECURITY_INFORMATION | PROTECTED_DACL_SECURITY_INFORMATION, None, None, acl, None)
            if err:
                raise OSError(err, f"could not set the access list of {path} (Windows error {err})")
        finally:
            api["CloseHandle"](handle)
    del keep_alive, buffers


def _win_create_private(path: str) -> int:
    api = _windows()
    ctypes = api["ctypes"]
    import msvcrt

    _, keep_alive, me = _current_user()
    acl = _acl_with([(me, FILE_ALL_ACCESS, 0)])
    attributes, buffers = _security_attributes(acl, protected=True)
    handle = api["CreateFileW"](path, GENERIC_WRITE, 0, ctypes.byref(attributes), CREATE_NEW, FILE_ATTRIBUTE_NORMAL, None)
    del keep_alive, buffers
    if handle is None or handle == ctypes.c_void_p(-1).value:
        code = ctypes.get_last_error()
        if code == ERROR_FILE_EXISTS:
            raise FileExistsError(code, "The file already exists", path)
        raise OSError(code, f"could not create {path} (Windows error {code})")
    try:
        return msvcrt.open_osfhandle(handle, os.O_WRONLY | os.O_BINARY | os.O_NOINHERIT)
    except BaseException:
        api["CloseHandle"](handle)
        raise


def _win_keeps_acls(path: str) -> bool:
    api = _windows()
    ctypes, wintypes = api["ctypes"], api["wintypes"]
    root = ctypes.create_unicode_buffer(1024)
    if not api["GetVolumePathNameW"](str(Path(path).resolve()), root, 1024):
        return False
    flags = wintypes.DWORD(0)
    if not api["GetVolumeInformationW"](root.value, None, 0, None, None, ctypes.byref(flags), None, 0):
        return False
    return bool(flags.value & FILE_PERSISTENT_ACLS)
