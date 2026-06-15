"""
ProClaim — FastAPI Dependency Injection
Provides: DB session, current user, role guards.
"""
import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.utils.jwt import decode_token

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
        if payload.type != "access":
            raise credentials_exception
        user_id = uuid.UUID(payload.sub)
    except (JWTError, ValueError):
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


def require_role(*roles: UserRole):
    """Factory for role-based guards. Usage: Depends(require_role(UserRole.ADMIN))"""
    async def guard(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in roles]}",
            )
        return current_user
    return guard


# Typed dependency aliases
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminOnly = Annotated[User, Depends(require_role(UserRole.ADMIN))]
DB = Annotated[AsyncSession, Depends(get_db)]


def require_claim_access(claim):
    """Raise 403 if current user does not belong to the claim's hospital (and is not admin)."""
    def _checker(current_user: CurrentUser):
        if current_user.role != UserRole.ADMIN and claim.hospital_id != current_user.hospital_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this claim.",
            )
    return _checker
