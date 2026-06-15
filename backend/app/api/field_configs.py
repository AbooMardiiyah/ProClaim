"""
ProClaim — Field Config Endpoints

GET    /field-configs         → list all active extraction field templates
POST   /field-configs         → create a new custom field (admin)
PATCH  /field-configs/{id}    → update a field template (admin)
DELETE /field-configs/{id}    → soft-delete (set is_active=False) (admin)
POST   /field-configs/reorder → bulk reorder (admin)
"""
import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import AdminOnly, CurrentUser, DB
from app.models.field_config import FieldConfig
from app.schemas.field_config import FieldConfigCreate, FieldConfigRead, FieldConfigUpdate

router = APIRouter(prefix="/field-configs", tags=["Field Configs"])


@router.get("", response_model=list[FieldConfigRead])
async def list_field_configs(current_user: CurrentUser, db: DB) -> list[FieldConfigRead]:
    result = await db.execute(
        select(FieldConfig).where(FieldConfig.is_active == True).order_by(FieldConfig.order)
    )
    return [FieldConfigRead.model_validate(fc) for fc in result.scalars().all()]


@router.post("", response_model=FieldConfigRead, status_code=status.HTTP_201_CREATED)
async def create_field_config(
    payload: FieldConfigCreate, admin: AdminOnly, db: DB
) -> FieldConfigRead:
    existing = await db.execute(
        select(FieldConfig).where(FieldConfig.api_key == payload.api_key)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Field key '{payload.api_key}' already exists")

    fc = FieldConfig(**payload.model_dump())
    db.add(fc)
    await db.flush()
    return FieldConfigRead.model_validate(fc)


@router.patch("/{config_id}", response_model=FieldConfigRead)
async def update_field_config(
    config_id: uuid.UUID, payload: FieldConfigUpdate, admin: AdminOnly, db: DB
) -> FieldConfigRead:
    result = await db.execute(select(FieldConfig).where(FieldConfig.id == config_id))
    fc = result.scalar_one_or_none()
    if not fc:
        raise HTTPException(status_code=404, detail="Field config not found")

    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(fc, k, v)

    await db.flush()
    return FieldConfigRead.model_validate(fc)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_field_config(
    config_id: uuid.UUID, admin: AdminOnly, db: DB
) -> None:
    result = await db.execute(select(FieldConfig).where(FieldConfig.id == config_id))
    fc = result.scalar_one_or_none()
    if not fc:
        raise HTTPException(status_code=404, detail="Field config not found")
    fc.is_active = False


@router.post("/reorder", response_model=list[FieldConfigRead])
async def reorder_field_configs(
    ordered_ids: list[uuid.UUID], admin: AdminOnly, db: DB
) -> list[FieldConfigRead]:
    """Accepts an ordered list of field-config IDs and updates their order index."""
    result = await db.execute(select(FieldConfig))
    all_fcs = {fc.id: fc for fc in result.scalars().all()}

    for index, fid in enumerate(ordered_ids):
        if fid in all_fcs:
            all_fcs[fid].order = index

    await db.flush()
    updated = await db.execute(
        select(FieldConfig).where(FieldConfig.is_active == True).order_by(FieldConfig.order)
    )
    return [FieldConfigRead.model_validate(fc) for fc in updated.scalars().all()]
