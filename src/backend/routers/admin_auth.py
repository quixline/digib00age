"""
digib00age — Admin auth router (ADMIN_SPEC.md §7.1)
POST /api/admin/login                 Password login, sets session cookie
POST /api/admin/logout                Clears session cookie
GET  /api/admin/auth/status           Auth/protection state for page bootstraps
POST /api/admin/auth/enable           Turn protection on + set password
POST /api/admin/auth/disable          Turn protection off, clears hash (requires current password)
POST /api/admin/auth/change-password  Change password while protected (requires current password)

This router is registered WITHOUT the require_admin_auth gating dependency —
it is the chicken-and-egg surface that the gate itself depends on. Password
state is the only boundary here; network origin is never checked.
"""

from __future__ import annotations

import secrets

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from backend.auth import (
    COOKIE_NAME,
    SESSION_TTL_SECONDS,
    clear_failed_attempts,
    hash_password,
    is_locked_out,
    is_protection_enabled,
    make_session_cookie,
    record_failed_attempt,
    verify_password,
    verify_session_cookie,
)
from backend.config import get_config, save_config

router = APIRouter(tags=["admin-auth"])


class LoginBody(BaseModel):
    password: str


class EnableBody(BaseModel):
    password: str


class ChangePasswordBody(BaseModel):
    current_password: str
    new_password: str


class DisableBody(BaseModel):
    current_password: str


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _is_authenticated(request: Request) -> bool:
    cfg = get_config()
    secret = cfg.get("SESSION_SECRET")
    if not secret:
        return False
    cookie_val = request.cookies.get(COOKIE_NAME)
    if not cookie_val:
        return False
    return verify_session_cookie(cookie_val, secret)


@router.post("/admin/login")
def login(body: LoginBody, request: Request, response: Response):
    ip = _client_ip(request)
    if is_locked_out(ip):
        raise HTTPException(status_code=423, detail={"error": "locked_out"})

    cfg = get_config()
    hash_hex = cfg.get("admin_password_hash")
    salt_hex = cfg.get("admin_password_salt")
    if not hash_hex or not salt_hex or not verify_password(body.password, hash_hex, salt_hex):
        record_failed_attempt(ip)
        raise HTTPException(status_code=401, detail={"error": "invalid_password"})

    clear_failed_attempts(ip)
    secret = cfg.get("SESSION_SECRET")
    cookie_val = make_session_cookie(secret)
    response.set_cookie(
        COOKIE_NAME, cookie_val, max_age=SESSION_TTL_SECONDS, httponly=True, samesite="lax"
    )
    return {"ok": True}


@router.post("/admin/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.get("/admin/auth/status")
def auth_status(request: Request):
    return {
        "protection_enabled": is_protection_enabled(),
        "authenticated": _is_authenticated(request),
    }


@router.post("/admin/auth/enable")
def enable_protection(body: EnableBody, request: Request):
    # Deliberately unrestricted, from anywhere — not an oversight. With no
    # password set, nothing is restricted at all (see ADMIN_SPEC.md §7.1.1);
    # whoever reaches the server first can claim the password. That risk is
    # explicitly accepted as the user's own responsibility.
    cfg = get_config()
    hash_hex, salt_hex = hash_password(body.password)
    update = {"admin_password_hash": hash_hex, "admin_password_salt": salt_hex}
    if not cfg.get("SESSION_SECRET"):
        update["SESSION_SECRET"] = secrets.token_hex(32)
    save_config(update)
    return {"ok": True}


@router.post("/admin/auth/disable")
def disable_protection(body: DisableBody, request: Request):
    cfg = get_config()
    hash_hex = cfg.get("admin_password_hash")
    salt_hex = cfg.get("admin_password_salt")
    if not hash_hex or not salt_hex or not verify_password(body.current_password, hash_hex, salt_hex):
        raise HTTPException(status_code=403, detail={"error": "invalid_password"})
    save_config({"admin_password_hash": None, "admin_password_salt": None})
    return {"ok": True}


@router.post("/admin/auth/change-password")
def change_password(body: ChangePasswordBody, request: Request):
    cfg = get_config()
    hash_hex = cfg.get("admin_password_hash")
    salt_hex = cfg.get("admin_password_salt")
    if not hash_hex or not salt_hex or not verify_password(body.current_password, hash_hex, salt_hex):
        raise HTTPException(status_code=401, detail={"error": "invalid_password"})
    new_hash, new_salt = hash_password(body.new_password)
    save_config({"admin_password_hash": new_hash, "admin_password_salt": new_salt})
    return {"ok": True}
