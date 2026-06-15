"""
ProClaim — Auth Endpoints
POST /auth/login      → access + refresh tokens
POST /auth/refresh    → new access token
POST /auth/register   → create user (admin only in production)
GET  /auth/me         → current user profile
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminOnly, CurrentUser, DB
from app.models.hospital import Hospital
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenPair, TokenRefreshRequest
from app.schemas.user import UserCreate, UserRead, UserSignup
from app.utils.jwt import create_access_token, create_refresh_token, decode_refresh_token, decode_token

router = APIRouter(prefix="/auth", tags=["Auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, db: DB) -> TokenPair:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    return TokenPair(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id, user.role),
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: TokenRefreshRequest, db: DB) -> TokenPair:
    try:
        token_data = decode_refresh_token(payload.refresh_token)
        user_id = uuid.UUID(token_data.sub)
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return TokenPair(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id, user.role),
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: DB, _admin: AdminOnly) -> UserRead:
    """Admin-only endpoint to create new users."""
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
        hospital_id=payload.hospital_id,
        hospital_name=payload.hospital_name,
    )
    db.add(user)
    await db.flush()
    return UserRead.model_validate(user)


@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def signup(payload: UserSignup, db: DB) -> UserRead:
    """Public self-registration. Creates a hospital workspace and a billing officer account."""
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    hospital = Hospital(name=payload.hospital_name)
    db.add(hospital)
    await db.flush()

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role="billing_officer",
        hospital_id=hospital.id,
        hospital_name=payload.hospital_name,
    )
    db.add(user)
    await db.flush()
    return UserRead.model_validate(user)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    payload: dict,
    db: DB,
    _admin: AdminOnly,
) -> None:
    """Admin-only: reset any user's password by email."""
    email = payload.get("email")
    new_password = payload.get("new_password")
    if not email or not new_password:
        raise HTTPException(status_code=400, detail="email and new_password are required")
    if len(new_password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.password_hash = hash_password(new_password)
    await db.flush()


@router.get("/me", response_model=UserRead)
async def me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)
