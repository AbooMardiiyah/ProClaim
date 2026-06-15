"""
ProClaim — Hospital Management Endpoints
Admin-only endpoints to create and list hospitals (tenants).
"""
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import AdminOnly, DB
from app.models.hospital import Hospital
from app.schemas.hospital import HospitalCreate, HospitalRead

router = APIRouter(prefix="/hospitals", tags=["Hospitals"])


@router.get("", response_model=list[HospitalRead])
async def list_hospitals(admin: AdminOnly, db: DB) -> list[HospitalRead]:
    result = await db.execute(select(Hospital).order_by(Hospital.name))
    return [HospitalRead.model_validate(h) for h in result.scalars().all()]


@router.post("", response_model=HospitalRead, status_code=status.HTTP_201_CREATED)
async def create_hospital(payload: HospitalCreate, admin: AdminOnly, db: DB) -> HospitalRead:
    existing = await db.execute(select(Hospital).where(Hospital.name == payload.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Hospital with this name already exists")

    hospital = Hospital(name=payload.name)
    db.add(hospital)
    await db.flush()
    return HospitalRead.model_validate(hospital)
