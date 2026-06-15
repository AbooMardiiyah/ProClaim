"""
ProClaim — Claims CRUD & Field Management Endpoints

GET    /claims                          → paginated list
POST   /claims                          → create draft claim (auto-reference)
GET    /claims/{id}                     → full claim with fields & documents
PATCH  /claims/{id}/status              → state machine transition
PATCH  /claims/{id}/fields/{field_key}  → manual field override
GET    /claims/{id}/audit               → audit trail for a claim
GET    /dashboard/stats                 → KPI aggregates
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DB
from app.models.audit_log import AuditLog
from app.models.claim import Claim, ClaimDocument, ClaimField, ClaimStatus
from app.models.user import UserRole
from app.schemas.claim import (
    AuditLogRead,
    ClaimFieldUpdate,
    ClaimListItem,
    ClaimRead,
    ClaimStatusTransition,
    DashboardStats,
)
from app.services.claim_service import (
    create_claim,
    get_claim_with_relations,
    get_dashboard_stats,
    manually_set_field,
    transition_claim_status,
)
from app.utils.pagination import Page, PaginationParams

router = APIRouter(tags=["Claims"])


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_claim_or_404(db, claim_id: uuid.UUID) -> Claim:
    claim = await get_claim_with_relations(db, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


def _ensure_claim_access(current_user, claim: Claim):
    if current_user.role != UserRole.ADMIN and claim.hospital_id != current_user.hospital_id:
        raise HTTPException(status_code=403, detail="You do not have access to this claim.")


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/claims", response_model=Page[ClaimListItem])
async def list_claims(
    current_user: CurrentUser,
    db: DB,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: ClaimStatus | None = Query(None, alias="status"),
    search: str | None = Query(None, description="Search patient name or NHIA ID"),
) -> Page[ClaimListItem]:
    params = PaginationParams(page=page, page_size=page_size)

    filters = []
    if current_user.role != UserRole.ADMIN:
        filters.append(Claim.hospital_id == current_user.hospital_id)
    if status_filter:
        filters.append(Claim.status == status_filter)
    if search:
        like = f"%{search}%"
        from sqlalchemy import or_
        filters.append(or_(Claim.patient_name.ilike(like), Claim.nhia_id.ilike(like)))

    count_q = await db.execute(select(func.count(Claim.id)).where(*filters))
    total = count_q.scalar() or 0

    claims_q = await db.execute(
        select(Claim)
        .where(*filters)
        .order_by(Claim.created_at.desc())
        .offset(params.offset)
        .limit(params.page_size)
    )
    claims = claims_q.scalars().all()

    # Batch load document counts
    claim_ids = [c.id for c in claims]
    doc_counts: dict[uuid.UUID, int] = {}
    if claim_ids:
        dc_result = await db.execute(
            select(ClaimDocument.claim_id, func.count(ClaimDocument.id))
            .where(ClaimDocument.claim_id.in_(claim_ids))
            .group_by(ClaimDocument.claim_id)
        )
        doc_counts = {row[0]: row[1] for row in dc_result.all()}

    items = []
    for c in claims:
        item = ClaimListItem.model_validate(c)
        item.document_count = doc_counts.get(c.id, 0)
        items.append(item)

    return Page.create(items=items, total=total, params=params)


@router.post("/claims", response_model=ClaimRead, status_code=status.HTTP_201_CREATED)
async def create_new_claim(current_user: CurrentUser, db: DB) -> ClaimRead:
    """Create an empty draft claim. Documents are uploaded separately."""
    claim = await create_claim(db, current_user)
    # Eagerly load relationships so ClaimRead serialisation doesn't trigger lazy loads
    refreshed = await get_claim_with_relations(db, claim.id)
    return ClaimRead.model_validate(refreshed)


@router.get("/claims/{claim_id}", response_model=ClaimRead)
async def get_claim(claim_id: uuid.UUID, current_user: CurrentUser, db: DB) -> ClaimRead:
    claim = await _get_claim_or_404(db, claim_id)
    _ensure_claim_access(current_user, claim)
    return ClaimRead.model_validate(claim)


@router.delete("/claims/{claim_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_claim(claim_id: uuid.UUID, current_user: CurrentUser, db: DB) -> None:
    """Permanently delete a claim and all its documents/fields. Admin only."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can delete claims.")
    claim = await _get_claim_or_404(db, claim_id)

    # Delete files from disk
    from pathlib import Path
    for doc in claim.documents:
        try:
            Path(doc.file_path).unlink(missing_ok=True)
        except Exception:
            pass

    # Cascade delete: audit logs first (no ORM cascade), then claim (cascades to docs/fields)
    await db.execute(delete(AuditLog).where(AuditLog.claim_id == claim_id))
    await db.delete(claim)


@router.patch("/claims/{claim_id}/status", response_model=ClaimRead)
async def update_claim_status(
    claim_id: uuid.UUID,
    payload: ClaimStatusTransition,
    current_user: CurrentUser,
    db: DB,
) -> ClaimRead:
    """Advance or revert the claim state machine."""
    claim = await _get_claim_or_404(db, claim_id)
    _ensure_claim_access(current_user, claim)
    try:
        await transition_claim_status(
            db, claim,
            new_status=payload.status,
            user_id=current_user.id,
            note=payload.note,
            rejection_reason=payload.rejection_reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return ClaimRead.model_validate(claim)


@router.patch("/claims/{claim_id}/fields/{field_key}", response_model=ClaimRead)
async def update_field(
    claim_id: uuid.UUID,
    field_key: str,
    payload: ClaimFieldUpdate,
    current_user: CurrentUser,
    db: DB,
) -> ClaimRead:
    """Manually set or override a specific field on a claim."""
    claim = await _get_claim_or_404(db, claim_id)
    _ensure_claim_access(current_user, claim)
    await manually_set_field(
        db, claim, field_key,
        new_value=payload.value,
        user_id=current_user.id,
        source_type=payload.source_type,
        note=payload.note,
    )
    refreshed = await get_claim_with_relations(db, claim_id)
    return ClaimRead.model_validate(refreshed)


@router.get("/claims/{claim_id}/audit", response_model=list[AuditLogRead])
async def get_audit_log(
    claim_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
    limit: int = Query(50, ge=1, le=200),
) -> list[AuditLogRead]:
    claim = await _get_claim_or_404(db, claim_id)
    _ensure_claim_access(current_user, claim)
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.claim_id == claim_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    return [AuditLogRead.model_validate(log) for log in result.scalars().all()]


@router.get("/dashboard/stats", response_model=DashboardStats)
async def dashboard_stats(current_user: CurrentUser, db: DB) -> DashboardStats:
    user_id = current_user.id if current_user.role != UserRole.ADMIN else None
    hospital_id = current_user.hospital_id if current_user.role != UserRole.ADMIN else None
    return await get_dashboard_stats(db, user_id=user_id, hospital_id=hospital_id)


@router.get("/claims/{claim_id}/export")
async def export_claim(
    claim_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
    format: str = Query("csv", pattern="^(csv|excel)$"),
):
    """Export a claim as CSV or Excel for the billing officer."""
    from fastapi.responses import Response
    claim = await _get_claim_or_404(db, claim_id)
    _ensure_claim_access(current_user, claim)

    export_data = {
        "reference_number": claim.reference_number,
        "patient_name": claim.patient_name,
        "nhia_id": claim.nhia_id,
        "date_of_service": claim.date_of_service,
        "hospital_name": claim.hospital_name,
        "primary_diagnosis": claim.primary_diagnosis,
        "icd10_code": claim.icd10_code,
        "procedure": claim.procedure_desc,
        "nhia_tariff_code": claim.nhia_tariff_code,
        "physician_name": claim.physician_name,
        "physician_id": claim.physician_id,
        "consultation_fee": str(claim.consultation_fee or ""),
        "drug_cost": str(claim.drug_cost or ""),
        "lab_cost": str(claim.lab_cost or ""),
        "total_cost": str(claim.total_cost or ""),
        "status": claim.status.value,
    }

    if format == "csv":
        import csv, io
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=list(export_data.keys()))
        writer.writeheader()
        writer.writerow(export_data)
        return Response(
            content=buf.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{claim.reference_number}.csv"'},
        )

    # Excel export
    import io
    from openpyxl import Workbook
    buf = io.BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = "Claim"
    ws.append(list(export_data.keys()))
    ws.append(list(export_data.values()))
    wb.save(buf)
    buf.seek(0)
    return Response(
        content=buf.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{claim.reference_number}.xlsx"'},
    )


@router.post("/claims/{claim_id}/submit-hmo")
async def submit_claim_to_hmo(
    claim_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
):
    """HMO submission placeholder. External HMO/NHIA portal integration is planned for a future release."""
    # This endpoint is intentionally disabled while the integration is being scoped.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="HMO submission is coming soon.",
    )
