"""Auth service routes — login / refresh / logout / me / change-password.

These five endpoints match the frontend `authClient` contract documented in
`docs/contracts/frontend-backend-api.md` §2. The auth domain prefix has NO
`/v1`; the FastAPI app mounts this router under both `/` and `/api/auth` so
the same handlers serve direct (8081) and proxied requests.
"""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from auth_service.config import get_settings
from auth_service.passwords import verify_password
from auth_service.tokens import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from auth_service.users import User, UserStore, build_default_store

router = APIRouter()

_store: UserStore = build_default_store()


class LoginRequest(BaseModel):
    email: str
    password: str
    captcha: str | None = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)
    confirm_password: str


class AuthSession(BaseModel):
    access_token: str
    expires_at: str


class UserProfile(BaseModel):
    user_id: str
    public_id: str
    email: str
    display_name: str
    role: str
    status: str
    created_at: str
    updated_at: str


def _profile(user: User) -> UserProfile:
    return UserProfile(
        user_id=user.user_id,
        public_id=user.public_id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        status=user.status,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _set_refresh_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        secure=False,  # dev over http; flip in production behind TLS
        samesite="lax",
        path="/api/auth",
        domain=settings.cookie_domain or None,
        max_age=settings.refresh_token_ttl_days * 24 * 60 * 60,
    )


def _clear_refresh_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=settings.cookie_name,
        path="/api/auth",
        domain=settings.cookie_domain or None,
    )


def _require_user_from_access(authorization: str | None) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "AUTH_REQUIRED", "message": "请先登录"},
        )
    token = authorization.split(" ", 1)[1].strip()
    try:
        public_id = decode_token(token, expected_type="access")
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "AUTH_EXPIRED", "message": "登录已过期，请重新登录"},
        ) from exc
    user = _store.find_by_public_id(public_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "AUTH_EXPIRED", "message": "用户不存在，请重新登录"},
        )
    return user


@router.post("/login", response_model=AuthSession)
def login(payload: LoginRequest, response: Response) -> AuthSession:
    user = _store.find_by_email(payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "AUTH_INVALID_CREDENTIALS", "message": "账号或密码不正确"},
        )
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "AUTH_FORBIDDEN", "message": "账号已禁用"},
        )
    access_token, expires_at = create_access_token(user.public_id, user.role)
    _set_refresh_cookie(response, create_refresh_token(user.public_id))
    return AuthSession(
        access_token=access_token,
        expires_at=expires_at.astimezone().isoformat(),
    )


@router.post("/refresh", response_model=AuthSession)
def refresh(request: Request, response: Response) -> AuthSession:
    settings = get_settings()
    token = request.cookies.get(settings.cookie_name)
    if not token:
        return _unauthenticated()
    try:
        public_id = decode_token(token, expected_type="refresh")
    except TokenError:
        return _unauthenticated()
    user = _store.find_by_public_id(public_id)
    if user is None:
        _clear_refresh_cookie(response)
        return _unauthenticated()
    access_token, expires_at = create_access_token(user.public_id, user.role)
    _set_refresh_cookie(response, create_refresh_token(user.public_id))
    return AuthSession(
        access_token=access_token,
        expires_at=expires_at.astimezone().isoformat(),
    )


def _unauthenticated() -> AuthSession:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error_code": "AUTH_EXPIRED", "message": "登录已过期，请重新登录"},
    )


@router.post("/logout")
def logout(response: Response) -> dict[str, bool]:
    _clear_refresh_cookie(response)
    return {"ok": True}


@router.get("/me", response_model=UserProfile)
def me(authorization: str | None = Header(default=None)) -> UserProfile:
    user = _require_user_from_access(authorization)
    return _profile(user)


@router.post("/change-password")
def change_password(
    payload: PasswordChangeRequest,
    response: Response,
    authorization: str | None = Header(default=None),
) -> dict[str, bool]:
    user = _require_user_from_access(authorization)
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "AUTH_INVALID_CREDENTIALS", "message": "当前密码不正确"},
        )
    if payload.new_password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "VALIDATION_ERROR", "message": "两次新密码不一致"},
        )
    if payload.new_password == payload.current_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "VALIDATION_ERROR", "message": "新密码不能与当前密码相同"},
        )
    _store.update_password(user.public_id, payload.new_password)
    _clear_refresh_cookie(response)
    return {"ok": True}
