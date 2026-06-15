import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.claim import ClaimStatus, FieldStatus
from app.models.audit_log import AuditAction


# ── ClaimDocument ─────────────────────────────────────────────────────────────
class ClaimDocumentRead(BaseModel):
    id: uuid.UUID
    file_name: str
    file_size_bytes: int
    mime_type: str
    document_type: str | None
    page_count: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── ClaimField ────────────────────────────────────────────────────────────────
class ClaimFieldRead(BaseModel):
    id: uuid.UUID
    field_key: str
    field_label: str
    value: str | None
    confidence_score: int | None
    status: FieldStatus
    source_document_id: uuid.UUID | None
    page_number: int | None
    bounding_box: dict | None

    model_config = {"from_attributes": True}


class ClaimFieldUpdate(BaseModel):
    """Payload for manually setting / overriding a field value."""
    value: str
    source_type: str = "manual"  # "manual" | "re_extracted"
    note: str | None = None      # reason for the change


# ── Claim ─────────────────────────────────────────────────────────────────────
class ClaimCreate(BaseModel):
    """Initial claim creation — just a shell; extraction populates the rest."""
    pass  # claims are created implicitly on first document upload


class ClaimListItem(BaseModel):
    id: uuid.UUID
    reference_number: str
    patient_name: str | None
    nhia_id: str | None
    date_of_service: str | None
    status: ClaimStatus
    total_cost: Decimal | None
    hospital_id: uuid.UUID
    created_at: datetime
    document_count: int = 0

    model_config = {"from_attributes": True}


class ClaimRead(BaseModel):
    id: uuid.UUID
    reference_number: str
    patient_name: str | None
    nhia_id: str | None
    date_of_service: str | None
    hospital_id: uuid.UUID
    hospital_name: str | None
    primary_diagnosis: str | None
    icd10_code: str | None
    procedure_desc: str | None
    nhia_tariff_code: str | None
    physician_name: str | None
    physician_id: str | None
    total_cost: Decimal | None
    consultation_fee: Decimal | None
    drug_cost: Decimal | None
    lab_cost: Decimal | None
    status: ClaimStatus
    rejection_reason: str | None
    submission_reference: str | None
    created_at: datetime
    updated_at: datetime

    documents: list[ClaimDocumentRead] = []
    fields: list[ClaimFieldRead] = []

    model_config = {"from_attributes": True}


class ClaimStatusTransition(BaseModel):
    """Request to move a claim to a new state."""
    status: ClaimStatus
    note: str | None = None
    rejection_reason: str | None = None


# ── AuditLog ──────────────────────────────────────────────────────────────────
class AuditLogRead(BaseModel):
    id: uuid.UUID
    claim_id: uuid.UUID
    user_id: uuid.UUID | None
    action: AuditAction
    field_name: str | None
    old_value: str | None
    new_value: str | None
    source_type: str | None
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Dashboard ─────────────────────────────────────────────────────────────────
class DashboardStats(BaseModel):
    total_claims: int
    claims_this_month: int
    avg_processing_seconds: float
    acceptance_rate: float          # 0–1
    missing_field_rate: float       # avg fraction of fields that are MISSING
    pending_review_count: int
