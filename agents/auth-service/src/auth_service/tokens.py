"""JWT issuance and verification for access and refresh tokens."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from auth_service.config import get_settings

ALGORITHM = "HS256"


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def create_access_token(public_id: str, role: str) -> tuple[str, datetime]:
    settings = get_settings()
    expires_at = _now() + timedelta(minutes=settings.access_token_ttl_minutes)
    payload = {
        "sub": public_id,
        "role": role,
        "type": "access",
        "iat": int(_now().timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)
    return token, expires_at


def create_refresh_token(public_id: str) -> str:
    settings = get_settings()
    expires_at = _now() + timedelta(days=settings.refresh_token_ttl_days)
    payload = {
        "sub": public_id,
        "type": "refresh",
        "iat": int(_now().timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


class TokenError(Exception):
    """Raised when a token is missing, malformed, expired, or wrong type."""


def decode_token(token: str, expected_type: str) -> str:
    """Validate `token` and return the subject (`public_id`)."""
    settings = get_settings()
    try:
        claims = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise TokenError("invalid token") from exc

    if claims.get("type") != expected_type:
        raise TokenError("wrong token type")

    sub = claims.get("sub")
    if not isinstance(sub, str):
        raise TokenError("missing subject")
    return sub
