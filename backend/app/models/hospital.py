"""
ProClaim — Hospital Model
Simple multi-tenant discriminator. Every user and claim belongs to one hospital.
"""
import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin


class Hospital(Base, TimestampMixin):
    __tablename__ = "hospitals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    def __repr__(self) -> str:
        return f"<Hospital {self.name}>"
