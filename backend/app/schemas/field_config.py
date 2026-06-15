import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.field_config import FieldType


class FieldConfigCreate(BaseModel):
    name: str
    api_key: str
    field_type: FieldType = FieldType.STRING
    required: bool = False
    order: int = 0
    extraction_hint: str | None = None
    validation_rules: dict | None = None


class FieldConfigUpdate(BaseModel):
    name: str | None = None
    field_type: FieldType | None = None
    required: bool | None = None
    is_active: bool | None = None
    order: int | None = None
    extraction_hint: str | None = None
    validation_rules: dict | None = None


class FieldConfigRead(BaseModel):
    id: uuid.UUID
    name: str
    api_key: str
    field_type: FieldType
    required: bool
    is_active: bool
    order: int
    extraction_hint: str | None
    validation_rules: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}
