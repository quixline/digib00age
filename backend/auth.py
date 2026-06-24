"""
ComicVault — Admin/Editor auth primitives.

Password protection is OFF by default (no admin_password_hash in config.json).
Stdlib only: hashlib for pbkdf2/hmac, secrets for tokens, no new dependency.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time

from fastapi import HTTPException, Request, Response

from backend.config import get_config

COOKIE_NAME = "cv_session"
SESSION_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days sliding expiry

PBKDF2_ITERATIONS = 200_000

MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 600  # 10 minutes

# In-memory brute-force tracker: ip -> (failed_count, locked_until_ts)
_failed_attempts: dict[str, tuple[int, float]] = {}


def hash_password(password: str) -> tuple[str, str]:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERATIONS
    )
    return digest.hex(), salt


def verify_password(password: str, hash_hex: str, salt_hex: str) -> bool:
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), PBKDF2_ITERATIONS
    )
    return hmac.compare_digest(digest.hex(), hash_hex)


def is_protection_enabled() -> bool:
    return bool(get_config().get("admin_password_hash"))


def is_remote_admin_enabled() -> bool:
    return bool(get_config().get("remote_admin_enabled", False))


def make_session_cookie(secret: str, ttl_seconds: int = SESSION_TTL_SECONDS) -> str:
    expiry = int(time.time()) + ttl_seconds
    sig = hmac.new(secret.encode("utf-8"), str(expiry).encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{expiry}.{sig}"


def verify_session_cookie(cookie_val: str, secret: str) -> bool:
    try:
        expiry_str, sig = cookie_val.split(".", 1)
        expiry = int(expiry_str)
    except (ValueError, AttributeError):
        return False
    expected_sig = hmac.new(secret.encode("utf-8"), expiry_str.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        return False
    return expiry > time.time()


def is_local_request(request: Request) -> bool:
    host = request.client.host if request.client else None
    return host in ("127.0.0.1", "::1")


def is_locked_out(ip: str) -> bool:
    entry = _failed_attempts.get(ip)
    if not entry:
        return False
    _count, locked_until = entry
    return time.time() < locked_until


def record_failed_attempt(ip: str) -> None:
    count, _locked_until = _failed_attempts.get(ip, (0, 0.0))
    count += 1
    locked_until = time.time() + LOCKOUT_SECONDS if count >= MAX_ATTEMPTS else 0.0
    _failed_attempts[ip] = (count, locked_until)


def clear_failed_attempts(ip: str) -> None:
    _failed_attempts.pop(ip, None)


def require_admin_auth(request: Request, response: Response) -> None:
    """FastAPI dependency gating /api/admin/* and /api/editor/* routes.

    No-op (V1 behaviour) when protection is disabled. Login/status/enable/disable
    endpoints live in admin_auth.py and are registered without this dependency.
    """
    if not is_protection_enabled():
        return

    if not is_local_request(request) and not is_remote_admin_enabled():
        raise HTTPException(status_code=403, detail={"error": "remote_admin_disabled"})

    cfg = get_config()
    secret = cfg.get("SESSION_SECRET")
    cookie_val = request.cookies.get(COOKIE_NAME)
    if not secret or not cookie_val or not verify_session_cookie(cookie_val, secret):
        raise HTTPException(status_code=401, detail={"error": "auth_required"})

    # Sliding expiry — reissue a refreshed cookie on every authenticated request.
    response.set_cookie(
        COOKIE_NAME,
        make_session_cookie(secret),
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
    )
