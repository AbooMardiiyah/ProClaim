"""
ProClaim — Application Configuration
All settings are sourced from environment variables with sane defaults.
"""
from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        case_sensitive=False,
    )

    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "ProClaim"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # ── Security ─────────────────────────────────────────────────────────────
    SECRET_KEY: str  # required – set in .env
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3001", "http://localhost:5173"]

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: PostgresDsn  # required – e.g. postgresql+asyncpg://user:pass@localhost:5432/proclaim

    # ── Redis / Celery ───────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── File Storage ─────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "/tmp/proclaim/uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_MIME_TYPES: list[str] = ["application/pdf", "image/jpeg", "image/png", "image/tiff"]

    # ── Gemini (primary extractor) ────────────────────────────────────────────
    GEMINI_API_KEY: str  # required – get from https://aistudio.google.com/app/apikey

    # ── HMO Submission ─────────────────────────────────────────────────────────
    HMO_SUBMISSION_URL: str = ""  # optional external endpoint to POST claim JSON

    # ── ICD-10 / NHIA ────────────────────────────────────────────────────────
    ICD10_DB_PATH: str = "app/data/icd10_ng_common.json"
    NHIA_TARIFF_DB_PATH: str = "app/data/nhia_tariff_codes.json"

    # ── Observability ────────────────────────────────────────────────────────
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"
    ENABLE_METRICS: bool = True

    # ── Seeding ──────────────────────────────────────────────────────────────
    FIRST_ADMIN_EMAIL: str = "admin@proclaim.ng"
    FIRST_ADMIN_PASSWORD: str = "changeme123!"

    @property
    def async_database_url(self) -> str:
        url = str(self.DATABASE_URL)
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
