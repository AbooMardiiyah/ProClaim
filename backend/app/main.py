"""
ProClaim — FastAPI Application Entry Point
"""
import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.auth import router as auth_router
from app.api.claims import router as claims_router
from app.api.documents import router as docs_router
from app.api.field_configs import router as field_configs_router
from app.api.hospitals import router as hospitals_router
from app.config import settings
from app.database import check_db_connection, init_db
from app.services.seeder import seed_defaults

# ── Logging ───────────────────────────────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)
logging.basicConfig(level=logging.DEBUG if settings.DEBUG else logging.INFO)
logger = structlog.get_logger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("proclaim.startup", version=settings.APP_VERSION, env=settings.ENVIRONMENT)

    if not await check_db_connection():
        raise RuntimeError("Cannot connect to database. Check DATABASE_URL.")

    if settings.ENVIRONMENT == "development":
        await init_db() 
        await seed_defaults()

    yield

    logger.info("proclaim.shutdown")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered claims processing for Nigerian healthcare",
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/api/openapi.json" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
PREFIX = settings.API_V1_PREFIX
app.include_router(auth_router, prefix=PREFIX)
app.include_router(claims_router, prefix=PREFIX)
app.include_router(docs_router, prefix=PREFIX)
app.include_router(field_configs_router, prefix=PREFIX)
app.include_router(hospitals_router, prefix=PREFIX)


# ── Health / Readiness ────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    db_ok = await check_db_connection()
    return {
        "status": "ok" if db_ok else "degraded",
        "version": settings.APP_VERSION,
        "database": "ok" if db_ok else "error",
    }


@app.get("/", include_in_schema=False)
async def root():
    return {"service": settings.APP_NAME, "version": settings.APP_VERSION}
