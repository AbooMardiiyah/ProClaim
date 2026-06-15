import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from app.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.BILLING_OFFICER
    hospital_id: uuid.UUID
    hospital_name: str | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserSignup(BaseModel):
    """Public self-registration schema. Creates a new hospital workspace."""
    email: EmailStr
    full_name: str
    password: str
    hospital_name: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserUpdate(BaseModel):
    full_name: str | None = None
    hospital_name: str | None = None
    is_active: bool | None = None
    role: UserRole | None = None


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    hospital_id: uuid.UUID
    hospital_name: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
