"""
ProClaim — Database Seeder
Creates the first admin user and default FieldConfig rows on first run.
"""
import logging

from passlib.context import CryptContext
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.field_config import DEFAULT_FIELD_CONFIGS, FieldConfig
from app.models.hospital import Hospital
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_defaults() -> None:
    async with AsyncSessionLocal() as db:
        # ── Seed default hospital ──────────────────────────────────────────
        hospital_result = await db.execute(
            select(Hospital).where(Hospital.name == "ProClaim HQ")
        )
        hospital = hospital_result.scalar_one_or_none()
        if not hospital:
            hospital = Hospital(name="ProClaim HQ")
            db.add(hospital)
            await db.flush()
            logger.info("Seeded default hospital: %s", hospital.name)

        # ── Seed admin user ────────────────────────────────────────────────
        existing_admin = await db.execute(
            select(User).where(User.email == settings.FIRST_ADMIN_EMAIL)
        )
        if not existing_admin.scalar_one_or_none():
            admin = User(
                email=settings.FIRST_ADMIN_EMAIL,
                full_name="ProClaim Admin",
                password_hash=pwd_context.hash(settings.FIRST_ADMIN_PASSWORD),
                role=UserRole.ADMIN,
                hospital_id=hospital.id,
                hospital_name=hospital.name,
            )
            db.add(admin)
            logger.info("Seeded admin user: %s", settings.FIRST_ADMIN_EMAIL)

        # ── Seed field configs ─────────────────────────────────────────────
        existing_count = await db.execute(select(FieldConfig))
        if not existing_count.scalars().all():
            for fc_data in DEFAULT_FIELD_CONFIGS:
                fc = FieldConfig(**fc_data)
                db.add(fc)
            logger.info("Seeded %d default field configs", len(DEFAULT_FIELD_CONFIGS))

        await db.commit()
