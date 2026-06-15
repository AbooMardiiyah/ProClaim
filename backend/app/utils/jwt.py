"""
ProClaim — JWT Utilities
Issues and verifies access tokens (15 min) + refresh tokens (7 days).
"""
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from app.config import settings
from app.schemas.auth import TokenPayload


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user_id: uuid.UUID, role: str) -> str:
    expire = _now_utc() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: uuid.UUID, role: str) -> str:
    expire = _now_utc() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "refresh",
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> TokenPayload:
    """
    Raises JWTError on invalid token or ExpiredSignatureError when expired.
    """
    data = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    return TokenPayload(**data)


def decode_refresh_token(token: str) -> TokenPayload:
    payload = decode_token(token)
    if payload.type != "refresh":
        raise JWTError("Not a refresh token")
    return payload
