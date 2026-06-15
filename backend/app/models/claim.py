"""
ProClaim — Claim, ClaimDocument, and ClaimField Models

State Machine (openIMIS-inspired, NHIA-adapted):
  DRAFT → PROCESSING → EXTRACTED → UNDER_REVIEW → READY → SUBMITTED → PAID | REJECTED
"""
import enum
import uuid
from decimal import Decimal

from sqlalchemy import (
    Date, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin


class ClaimStatus(str, enum.Enum):
    DRAFT = "draft"               # just uploaded, not yet processed
    PROCESSING = "processing"     # extraction task running
    EXTRACTED = "extracted"       # AI extraction complete
    UNDER_REVIEW = "under_review" # billing officer is reviewing
    READY = "ready"               # all fields validated, ready to submit
    SUBMITTED = "submitted"       # sent to HMO/NHIA portal
    PAID = "paid"                 # reimbursement received
    REJECTED = "rejected"         # HMO rejected the claim


class FieldStatus(str, enum.Enum):
    EXTRACTED = "extracted"   # returned by AI with confidence score
    MISSING = "missing"       # not found in documents
    MANUAL = "manual"         # user entered / overrode the value
    VERIFIED = "verified"     # billing officer explicitly confirmed the value


class Claim(Base, TimestampMixin):
    __tablename__ = "claims"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # ── Patient & Encounter ───────────────────────────────────────────────────
    patient_name: Mapped[str | None] = mapped_column(String(255))
    nhia_id: Mapped[str | None] = mapped_column(String(100), index=True)
    date_of_service: Mapped[str | None] = mapped_column(String(20))  # ISO date string
    hospital_name: Mapped[str | None] = mapped_column(String(255))

    # ── Clinical ──────────────────────────────────────────────────────────────
    primary_diagnosis: Mapped[str | None] = mapped_column(Text)
    icd10_code: Mapped[str | None] = mapped_column(String(20))
    procedure_desc: Mapped[str | None] = mapped_column(Text)
    nhia_tariff_code: Mapped[str | None] = mapped_column(String(20))
    physician_name: Mapped[str | None] = mapped_column(String(255))
    physician_id: Mapped[str | None] = mapped_column(String(100))

    # ── Financial ─────────────────────────────────────────────────────────────
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    consultation_fee: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    drug_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    lab_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))

    # ── State & Meta ──────────────────────────────────────────────────────────
    status: Mapped[ClaimStatus] = mapped_column(
        Enum(ClaimStatus, name="claimstatus"), default=ClaimStatus.DRAFT, nullable=False, index=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    submission_reference: Mapped[str | None] = mapped_column(String(100))  # HMO ref number

    # ── Raw Extraction Output ─────────────────────────────────────────────────
    extraction_raw: Mapped[dict | None] = mapped_column(JSONB)  # raw extraction response stored for debugging

    # ── Multi-tenant / Ownership ──────────────────────────────────────────────
    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=False, index=True
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    created_by_user: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", back_populates="claims", foreign_keys=[created_by_id]
    )
    documents: Mapped[list["ClaimDocument"]] = relationship(
        "ClaimDocument", back_populates="claim", cascade="all, delete-orphan"
    )
    fields: Mapped[list["ClaimField"]] = relationship(
        "ClaimField", back_populates="claim", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(  # type: ignore[name-defined]
        "AuditLog", back_populates="claim"
    )

    def __repr__(self) -> str:
        return f"<Claim {self.reference_number} [{self.status}]>"


class ClaimDocument(Base, TimestampMixin):
    """A single uploaded file attached to a claim (outpatient register, lab report, pharmacy log…)."""
    __tablename__ = "claim_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)  # server-side path
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    document_type: Mapped[str | None] = mapped_column(
        String(50)
    )  # e.g. outpatient_register | pharmacy_log | lab_report | billing_receipt | other
    page_count: Mapped[int | None] = mapped_column(Integer)

    # Relationships
    claim: Mapped[Claim] = relationship("Claim", back_populates="documents")
    source_fields: Mapped[list["ClaimField"]] = relationship(
        "ClaimField", back_populates="source_document"
    )

    def __repr__(self) -> str:
        return f"<ClaimDocument {self.file_name}>"


class ClaimField(Base, TimestampMixin):
    """
    A single extracted (or manually entered) field value on a claim.
    Every field from the active FieldConfig gets a row here after extraction.
    """
    __tablename__ = "claim_fields"
    __table_args__ = (UniqueConstraint("claim_id", "field_key", name="uq_claim_field"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True
    )
    field_key: Mapped[str] = mapped_column(String(100), nullable=False)
    field_label: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str | None] = mapped_column(Text)
    confidence_score: Mapped[int | None] = mapped_column(Integer)  # 0–100
    status: Mapped[FieldStatus] = mapped_column(
        Enum(FieldStatus, name="fieldstatus"), default=FieldStatus.MISSING, nullable=False
    )
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claim_documents.id", ondelete="SET NULL"), nullable=True
    )
    page_number: Mapped[int | None] = mapped_column(Integer)
    bounding_box: Mapped[dict | None] = mapped_column(JSONB)  # optional region coordinates

    # Relationships
    claim: Mapped[Claim] = relationship("Claim", back_populates="fields")
    source_document: Mapped[ClaimDocument | None] = relationship(
        "ClaimDocument", back_populates="source_fields"
    )

    def __repr__(self) -> str:
        return f"<ClaimField {self.field_key}={self.value!r} [{self.status}]>"
