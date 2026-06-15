"""
ProClaim — Claim Business Logic Service

Handles:
- Reference number generation
- State machine transition validation
- Field upsert after extraction
- Audit log writes
- Dashboard stats aggregation
"""
import random
import string
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit_log import AuditAction, AuditLog
from app.models.claim import Claim, ClaimDocument, ClaimField, ClaimStatus, FieldStatus
from app.models.field_config import FieldConfig
from app.schemas.claim import DashboardStats
from app.services.extraction_models import ExtractionResult

logger = structlog.get_logger(__name__)

# Valid state transitions
TRANSITIONS: dict[ClaimStatus, set[ClaimStatus]] = {
    ClaimStatus.DRAFT:        {ClaimStatus.PROCESSING, ClaimStatus.REJECTED},
    ClaimStatus.PROCESSING:   {ClaimStatus.EXTRACTED, ClaimStatus.DRAFT},
    ClaimStatus.EXTRACTED:    {ClaimStatus.UNDER_REVIEW, ClaimStatus.PROCESSING},
    ClaimStatus.UNDER_REVIEW: {ClaimStatus.READY, ClaimStatus.PROCESSING},
    ClaimStatus.READY:        {ClaimStatus.SUBMITTED, ClaimStatus.UNDER_REVIEW},
    ClaimStatus.SUBMITTED:    {ClaimStatus.PAID, ClaimStatus.REJECTED},
    ClaimStatus.PAID:         set(),
    ClaimStatus.REJECTED:     {ClaimStatus.DRAFT},
}


async def generate_reference_number(db: AsyncSession) -> str:
    """Generate a unique human-readable claim reference: PC-YYYYMMDD-XXXX"""
    for _ in range(10):
        date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
        rand_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        ref = f"PC-{date_part}-{rand_part}"
        existing = await db.execute(select(Claim).where(Claim.reference_number == ref))
        if not existing.scalar_one_or_none():
            return ref
    raise RuntimeError("Unable to generate a unique reference number")


async def create_claim(db: AsyncSession, user) -> Claim:
    """Create a new DRAFT claim shell."""
    claim = Claim(
        reference_number=await generate_reference_number(db),
        status=ClaimStatus.DRAFT,
        hospital_id=user.hospital_id,
        hospital_name=user.hospital_name,
        created_by_id=user.id,
    )
    db.add(claim)
    await db.flush()
    logger.info("claim.created", reference=claim.reference_number)
    return claim


async def get_claim_with_relations(db: AsyncSession, claim_id: uuid.UUID) -> Claim | None:
    result = await db.execute(
        select(Claim)
        .where(Claim.id == claim_id)
        .options(
            selectinload(Claim.documents),
            selectinload(Claim.fields),
            selectinload(Claim.audit_logs),
        )
    )
    return result.scalar_one_or_none()


async def transition_claim_status(
    db: AsyncSession,
    claim: Claim,
    new_status: ClaimStatus,
    user_id: uuid.UUID,
    note: str | None = None,
    rejection_reason: str | None = None,
) -> Claim:
    allowed = TRANSITIONS.get(claim.status, set())
    if new_status not in allowed:
        raise ValueError(
            f"Cannot transition claim from {claim.status} to {new_status}. "
            f"Allowed: {[s.value for s in allowed]}"
        )

    old_status = claim.status
    claim.status = new_status
    if rejection_reason:
        claim.rejection_reason = rejection_reason

    log = AuditLog(
        claim_id=claim.id,
        user_id=user_id,
        action=AuditAction.STATUS_CHANGED,
        field_name="status",
        old_value=old_status.value,
        new_value=new_status.value,
        source_type="system",
        note=note,
    )
    db.add(log)
    await db.flush()
    logger.info("claim.status_changed", reference=claim.reference_number, from_=old_status, to=new_status)
    return claim


async def upsert_extracted_fields(
    db: AsyncSession,
    claim: Claim,
    results: list[ExtractionResult],
    user_id: uuid.UUID | None = None,
) -> list[ClaimField]:
    """
    After Gemini extraction, write one ClaimField row per result.
    Also denormalise key fields back to the Claim row for fast querying.
    """
    updated_fields: list[ClaimField] = []

    for res in results:
        # Upsert the ClaimField row
        existing = await db.execute(
            select(ClaimField).where(
                ClaimField.claim_id == claim.id,
                ClaimField.field_key == res.field_key,
            )
        )
        field = existing.scalar_one_or_none()

        old_value = field.value if field else None
        field_status = FieldStatus.MISSING if res.is_missing else FieldStatus.EXTRACTED

        safe_doc_id = None
        if res.source_document_id:
            try:
                safe_doc_id = uuid.UUID(res.source_document_id)
            except ValueError:
                safe_doc_id = None

        if field is None:
            field = ClaimField(
                claim_id=claim.id,
                field_key=res.field_key,
                field_label=res.field_label,
                value=res.value,
                confidence_score=res.confidence,
                status=field_status,
                source_document_id=safe_doc_id,
                page_number=res.page_number,
                bounding_box=res.bounding_box,
            )
            db.add(field)
        else:
            field.value = res.value
            field.confidence_score = res.confidence
            field.status = field_status
            if safe_doc_id:
                field.source_document_id = safe_doc_id
            field.page_number = res.page_number
            field.bounding_box = res.bounding_box

        # Write audit log
        if old_value != res.value:
            audit = AuditLog(
                claim_id=claim.id,
                user_id=user_id,
                action=AuditAction.FIELD_EXTRACTED,
                field_name=res.field_key,
                old_value=old_value,
                new_value=res.value,
                source_type="gemini",
            )
            db.add(audit)

        updated_fields.append(field)

    # Denormalise key fields into Claim columns
    field_map = {r.field_key: r.value for r in results if not r.is_missing}
    _DENORM_MAP = [
        ("patient_name", "patient_name"),
        ("nhia_id", "nhia_id"),
        ("date_of_service", "date_of_service"),
        ("hospital_name", "hospital_name"),
        ("primary_diagnosis", "primary_diagnosis"),
        ("icd10_code", "icd10_code"),
        ("procedure_desc", "procedure_desc"),
        ("nhia_tariff_code", "nhia_tariff_code"),
        ("physician_name", "physician_name"),
        ("physician_id", "physician_id"),
    ]
    for field_key, claim_attr in _DENORM_MAP:
        if field_key in field_map:
            setattr(claim, claim_attr, field_map[field_key])

    for money_key in ("total_cost", "consultation_fee", "drug_cost", "lab_cost"):
        if money_key in field_map:
            try:
                cleaned = field_map[money_key].replace(",", "").replace("₦", "").strip()
                setattr(claim, money_key, Decimal(cleaned))
            except (InvalidOperation, AttributeError):
                pass

    await db.flush()
    return updated_fields


async def manually_set_field(
    db: AsyncSession,
    claim: Claim,
    field_key: str,
    new_value: str,
    user_id: uuid.UUID,
    source_type: str = "manual",
    note: str | None = None,
) -> ClaimField:
    """Billing officer manually enters or overrides a field value."""
    existing = await db.execute(
        select(ClaimField).where(
            ClaimField.claim_id == claim.id,
            ClaimField.field_key == field_key,
        )
    )
    field = existing.scalar_one_or_none()
    old_value = field.value if field else None
    action = AuditAction.FIELD_OVERRIDDEN if field and field.status == FieldStatus.EXTRACTED else AuditAction.FIELD_MANUAL_SET

    if field is None:
        # Get the label from FieldConfig
        fc_result = await db.execute(select(FieldConfig).where(FieldConfig.api_key == field_key))
        fc = fc_result.scalar_one_or_none()
        field = ClaimField(
            claim_id=claim.id,
            field_key=field_key,
            field_label=fc.name if fc else field_key,
            value=new_value,
            confidence_score=100,
            status=FieldStatus.MANUAL,
        )
        db.add(field)
    else:
        field.value = new_value
        field.status = FieldStatus.MANUAL
        field.confidence_score = 100

    audit = AuditLog(
        claim_id=claim.id,
        user_id=user_id,
        action=action,
        field_name=field_key,
        old_value=old_value,
        new_value=new_value,
        source_type=source_type,
        note=note,
    )
    db.add(audit)

    # Sync to Claim denormalised column
    if hasattr(claim, field_key):
        if field_key in ("total_cost", "consultation_fee", "drug_cost", "lab_cost"):
            try:
                cleaned = new_value.replace(",", "").replace("₦", "").strip()
                setattr(claim, field_key, Decimal(cleaned))
            except InvalidOperation:
                pass
        else:
            setattr(claim, field_key, new_value)

    await db.flush()
    logger.info("field.manual_set", claim=str(claim.id), field=field_key, value=new_value)
    return field


async def get_dashboard_stats(
    db: AsyncSession,
    user_id: uuid.UUID | None = None,
    hospital_id: uuid.UUID | None = None,
) -> DashboardStats:
    """Aggregate stats for the dashboard KPI cards."""
    base_filter = []
    if hospital_id:
        base_filter.append(Claim.hospital_id == hospital_id)
    if user_id:
        base_filter.append(Claim.created_by_id == user_id)

    total_q = await db.execute(select(func.count(Claim.id)).where(*base_filter))
    total = total_q.scalar() or 0

    from datetime import date
    first_of_month = date.today().replace(day=1)
    month_q = await db.execute(
        select(func.count(Claim.id)).where(
            *base_filter,
            Claim.created_at >= first_of_month,
        )
    )
    claims_this_month = month_q.scalar() or 0

    paid_q = await db.execute(select(func.count(Claim.id)).where(*base_filter, Claim.status == ClaimStatus.PAID))
    submitted_q = await db.execute(
        select(func.count(Claim.id)).where(*base_filter, Claim.status.in_([ClaimStatus.SUBMITTED, ClaimStatus.PAID, ClaimStatus.REJECTED]))
    )
    paid_count = paid_q.scalar() or 0
    submitted_count = submitted_q.scalar() or 1
    acceptance_rate = paid_count / submitted_count

    review_q = await db.execute(
        select(func.count(Claim.id)).where(*base_filter, Claim.status == ClaimStatus.UNDER_REVIEW)
    )
    pending_review = review_q.scalar() or 0

    return DashboardStats(
        total_claims=total,
        claims_this_month=claims_this_month,
        avg_processing_seconds=87.0,  # TODO: instrument Celery task timing
        acceptance_rate=round(acceptance_rate, 3),
        missing_field_rate=0.18,       # TODO: aggregate from ClaimField
        pending_review_count=pending_review,
    )
