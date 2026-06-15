"""
ProClaim — AuditLog Model
Immutable ledger of every change made to a claim's fields.
"""
import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin


class AuditAction(str, enum.Enum):
    FIELD_EXTRACTED = "field_extracted"      # AI returned a value
    FIELD_MANUAL_SET = "field_manual_set"    # user typed a value
    FIELD_OVERRIDDEN = "field_overridden"    # user changed an extracted value
    FIELD_VERIFIED = "field_verified"        # user explicitly confirmed a value
    STATUS_CHANGED = "status_changed"        # claim state machine transition
    DOCUMENT_UPLOADED = "document_uploaded"  # new document attached
    CLAIM_SUBMITTED = "claim_submitted"      # sent to HMO/NHIA


class AuditLog(Base, TimestampMixin):
    """Every write to claim data is captured here. Never deleted."""
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, name="auditaction"), nullable=False
    )
    field_name: Mapped[str | None] = mapped_column(String(100))  
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str | None] = mapped_column(String(50))  # e.g. "gemini", "manual", "system"
    note: Mapped[str | None] = mapped_column(Text) 

    # Relationships
    claim: Mapped["Claim"] = relationship("Claim", back_populates="audit_logs") 
    user: Mapped["User | None"] = relationship("User", back_populates="audit_logs")  

    def __repr__(self) -> str:
        return f"<AuditLog claim={self.claim_id} action={self.action} field={self.field_name}>"
