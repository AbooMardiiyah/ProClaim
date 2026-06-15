"""
ProClaim — User Model
Supports ADMIN and BILLING_OFFICER roles.
"""
import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    BILLING_OFFICER = "billing_officer"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="userrole"), nullable=False, default=UserRole.BILLING_OFFICER
    )
    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=False
    )
    hospital_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    hospital: Mapped["Hospital"] = relationship("Hospital")  # type: ignore[name-defined]
    claims: Mapped[list["Claim"]] = relationship(  # type: ignore[name-defined]
        "Claim", back_populates="created_by_user", foreign_keys="Claim.created_by_id"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(  # type: ignore[name-defined]
        "AuditLog", back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<User {self.email} [{self.role}]>"
