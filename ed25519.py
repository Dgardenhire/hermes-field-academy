"""Ed25519 signatures, from the reference algorithm in RFC 8032, section 6.

Why this file exists: the Deployer certificate needs an expert reviewer's
sign-off that a learner cannot write for themselves. Python's standard library
has no public-key signatures, and Field Academy takes no outside packages, so
this is the short reference implementation. The reviewer keeps a secret key and
signs a review packet; the plugin only ever holds the reviewer's public key.

What it is for: verifying a reviewer's signature inside the plugin, and signing
on the reviewer's own computer with scripts/sign_review.py.
What it is not for: anything that needs a hardened signer. It is not constant
time. The test suite runs it against the RFC 8032 test vectors.
"""

from __future__ import annotations

import hashlib

P = 2**255 - 19
Q = 2**252 + 27742317777372353535851937790883648493


def _sha512(data: bytes) -> bytes:
    return hashlib.sha512(data).digest()


def _inv(x: int) -> int:
    return pow(x, P - 2, P)


D = -121665 * _inv(121666) % P


def _recover_x(y: int, sign: int):
    if y >= P:
        return None
    x2 = (y * y - 1) * _inv(D * y * y + 1) % P
    if x2 == 0:
        return None if sign else 0
    x = pow(x2, (P + 3) // 8, P)
    if (x * x - x2) % P != 0:
        x = x * pow(2, (P - 1) // 4, P) % P
    if (x * x - x2) % P != 0:
        return None
    if (x & 1) != sign:
        x = P - x
    return x


_GY = 4 * _inv(5) % P
_GX = _recover_x(_GY, 0)
G = (_GX, _GY, 1, _GX * _GY % P)


def _add(a, b):
    p1 = (a[1] - a[0]) * (b[1] - b[0]) % P
    p2 = (a[1] + a[0]) * (b[1] + b[0]) % P
    c = 2 * a[3] * b[3] * D % P
    d = 2 * a[2] * b[2] % P
    e, f, g, h = p2 - p1, d - c, d + c, p2 + p1
    return (e * f % P, g * h % P, f * g % P, e * h % P)


def _mul(s: int, point):
    result = (0, 1, 1, 0)
    while s > 0:
        if s & 1:
            result = _add(result, point)
        point = _add(point, point)
        s >>= 1
    return result


def _equal(a, b) -> bool:
    if (a[0] * b[2] - b[0] * a[2]) % P != 0:
        return False
    return (a[1] * b[2] - b[1] * a[2]) % P == 0


def _compress(point) -> bytes:
    zinv = _inv(point[2])
    x = point[0] * zinv % P
    y = point[1] * zinv % P
    return int.to_bytes(y | ((x & 1) << 255), 32, "little")


def _decompress(raw: bytes):
    if len(raw) != 32:
        return None
    y = int.from_bytes(raw, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    x = _recover_x(y, sign)
    if x is None:
        return None
    return (x, y, 1, x * y % P)


def _expand(secret: bytes):
    if len(secret) != 32:
        raise ValueError("An Ed25519 secret key is 32 bytes.")
    h = _sha512(secret)
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    return a, h[32:]


def _modq(data: bytes) -> int:
    return int.from_bytes(_sha512(data), "little") % Q


def public_key(secret: bytes) -> bytes:
    a, _ = _expand(secret)
    return _compress(_mul(a, G))


def sign(secret: bytes, message: bytes) -> bytes:
    a, prefix = _expand(secret)
    public = _compress(_mul(a, G))
    r = _modq(prefix + message)
    r_point = _compress(_mul(r, G))
    h = _modq(r_point + public + message)
    s = (r + h * a) % Q
    return r_point + int.to_bytes(s, 32, "little")


def verify(public: bytes, message: bytes, signature: bytes) -> bool:
    if len(public) != 32 or len(signature) != 64:
        return False
    a_point = _decompress(public)
    if a_point is None:
        return False
    r_raw = signature[:32]
    r_point = _decompress(r_raw)
    if r_point is None:
        return False
    s = int.from_bytes(signature[32:], "little")
    if s >= Q:
        return False
    h = _modq(r_raw + public + message)
    return _equal(_mul(s, G), _add(r_point, _mul(h, a_point)))
