"""
ProClaim — FieldConfig Model
Defines which fields to extract from documents.
Billing officers can add, reorder, rename, or disable fields.
"""
import enum
import uuid

from sqlalchemy import Boolean, Enum, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin


class FieldType(str, enum.Enum):
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    DATE = "date"
    BOOLEAN = "boolean"


# Default NHIA claim fields (seeded at startup)
DEFAULT_FIELD_CONFIGS = [
    {"name": "Patient Name",      "api_key": "patient_name",      "field_type": "string",  "required": True,  "order": 1,  "extraction_hint": "full name of the patient"},
    {"name": "NHIA ID",           "api_key": "nhia_id",           "field_type": "string",  "required": True,  "order": 2,  "extraction_hint": "NHIA or insurance ID number"},
    {"name": "Date of Service",   "api_key": "date_of_service",   "field_type": "date",    "required": True,  "order": 3,  "extraction_hint": "date the patient was seen"},
    {"name": "Hospital Name",     "api_key": "hospital_name",     "field_type": "string",  "required": False, "order": 4,  "extraction_hint": "name of the hospital or clinic"},
    {"name": "Primary Diagnosis", "api_key": "primary_diagnosis", "field_type": "string",  "required": True,  "order": 5,  "extraction_hint": "clinical diagnosis or presenting complaint"},
    {"name": "ICD-10 Code",       "api_key": "icd10_code",        "field_type": "string",  "required": True,  "order": 6,  "extraction_hint": "ICD-10 diagnostic code"},
    {"name": "Procedure",         "api_key": "procedure_desc",    "field_type": "string",  "required": False, "order": 7,  "extraction_hint": "medical procedure or treatment performed"},
    {"name": "NHIA Tariff Code",  "api_key": "nhia_tariff_code",  "field_type": "string",  "required": True,  "order": 8,  "extraction_hint": "NHIA or NHIS procedure tariff code"},
    {"name": "Physician Name",    "api_key": "physician_name",    "field_type": "string",  "required": True,  "order": 9,  "extraction_hint": "name of the attending physician"},
    {"name": "Physician ID",      "api_key": "physician_id",      "field_type": "string",  "required": False, "order": 10, "extraction_hint": "physician registration or ID number"},
    {"name": "Consultation Fee",  "api_key": "consultation_fee",  "field_type": "decimal", "required": False, "order": 11, "extraction_hint": "consultation charge in Naira"},
    {"name": "Drug Cost",         "api_key": "drug_cost",         "field_type": "decimal", "required": False, "order": 12, "extraction_hint": "total drug/pharmacy cost in Naira"},
    {"name": "Lab Cost",          "api_key": "lab_cost",          "field_type": "decimal", "required": False, "order": 13, "extraction_hint": "total laboratory investigation cost in Naira"},
    {"name": "Total Cost",        "api_key": "total_cost",        "field_type": "decimal", "required": True,  "order": 14, "extraction_hint": "total claim amount in Naira"},
]


class FieldConfig(Base, TimestampMixin):
    """Template definition for a claim extraction field."""
    __tablename__ = "field_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)           
    api_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)  
    field_type: Mapped[FieldType] = mapped_column(
        Enum(FieldType, name="fieldtype"), nullable=False, default=FieldType.STRING
    )
    required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    extraction_hint: Mapped[str | None] = mapped_column(String(500))  
    validation_rules: Mapped[dict | None] = mapped_column(JSONB)  

    def __repr__(self) -> str:
        return f"<FieldConfig {self.api_key} [{self.field_type}]>"
