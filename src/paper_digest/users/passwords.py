import hashlib
import hmac
import secrets

# scrypt parameters (OWASP minimum: n=2**17, r=8, p=1).
_N, _R, _P = 2**17, 8, 1
_MAXMEM = 256 * 1024 * 1024


def _derive(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        password.encode(), salt=salt, n=_N, r=_R, p=_P, maxmem=_MAXMEM, dklen=32
    )


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    return f"scrypt${salt.hex()}${_derive(password, salt).hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt, digest = stored.split("$")
    except ValueError:
        return False
    if scheme != "scrypt":
        return False
    return hmac.compare_digest(_derive(password, bytes.fromhex(salt)).hex(), digest)
