"""
ProClaim — Celery Tasks

extract_documents(claim_id, document_ids, user_id)
  - Transitions claim to PROCESSING
  - Calls Google Gemini for each document
  - Writes ClaimField rows
  - Transitions to EXTRACTED (or back to DRAFT on failure)
"""
import asyncio
import logging
import time
import uuid

from celery import Task
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models.claim import Claim, ClaimDocument, ClaimStatus
from app.models.field_config import FieldConfig
from app.services.extraction_service import DocumentExtractionService
from app.services.claim_service import (
    transition_claim_status,
    upsert_extracted_fields,
)
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run(coro):
    """Run a coroutine from a sync Celery task."""
    return asyncio.run(coro)


class ExtractionTask(Task):
    """Celery task base that initialises the extraction service once per worker."""
    _extraction_service: DocumentExtractionService | None = None

    @property
    def extraction_service(self) -> DocumentExtractionService:
        if self._extraction_service is None:
            self._extraction_service = DocumentExtractionService()
        return self._extraction_service


@celery_app.task(
    bind=True,
    base=ExtractionTask,
    name="app.workers.tasks.extract_documents",
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def extract_documents(
    self: ExtractionTask,
    claim_id: str,
    document_ids: list[str],
    user_id: str,
) -> dict:
    """
    Main extraction task.
    Args:
        claim_id: UUID string of the claim to process
        document_ids: list of ClaimDocument UUID strings to analyse
        user_id: UUID string of the user who triggered extraction
    Returns:
        dict with fields_extracted, fields_missing, duration_seconds
    """
    try:
        return _run(_extract_async(self, claim_id, document_ids, user_id))
    except Exception as exc:
        logger.error("extraction.failed claim_id=%s: %s", claim_id, exc, exc_info=True)
        _run(_mark_failed(claim_id, user_id, str(exc)))
        raise self.retry(exc=exc, countdown=30)


async def _extract_async(
    task: ExtractionTask,
    claim_id: str,
    document_ids: list[str],
    user_id: str,
) -> dict:
    start = time.monotonic()

    async with AsyncSessionLocal() as db:
        # Load claim
        claim_result = await db.execute(
            select(Claim).where(Claim.id == uuid.UUID(claim_id)).options(
                selectinload(Claim.documents),
                selectinload(Claim.fields),
            )
        )
        claim = claim_result.scalar_one_or_none()
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")

        # Transition to PROCESSING
        await transition_claim_status(
            db, claim, ClaimStatus.PROCESSING,
            user_id=uuid.UUID(user_id),
            note="Extraction started",
        )
        await db.commit()

        # Load active field configs
        fc_result = await db.execute(
            select(FieldConfig).where(FieldConfig.is_active == True).order_by(FieldConfig.order)
        )
        field_configs = fc_result.scalars().all()
        fc_dicts = [
            {
                "api_key": fc.api_key,
                "name": fc.name,
                "field_type": fc.field_type.value,
                "extraction_hint": fc.extraction_hint,
            }
            for fc in field_configs
        ]

        # Load target documents
        docs_result = await db.execute(
            select(ClaimDocument).where(
                ClaimDocument.id.in_([uuid.UUID(d) for d in document_ids])
            )
        )
        documents = docs_result.scalars().all()

        # Run extraction on all documents in parallel
        async def _extract_one(doc):
            logger.info("Extracting %s (doc=%s)", claim_id, doc.id)
            try:
                return await task.extraction_service.analyze_document(
                    file_path=doc.file_path,
                    field_configs=fc_dicts,
                    document_id=str(doc.id),
                )
            except Exception as exc:
                logger.warning("extraction.error doc=%s: %s", doc.id, exc)
                return []

        doc_results_list = await asyncio.gather(*[_extract_one(doc) for doc in documents])

        # Merge: keep highest-confidence value per field across all documents
        all_results: dict[str, object] = {}
        for doc_results in doc_results_list:
            for res in doc_results:
                existing = all_results.get(res.field_key)
                if existing is None or (not res.is_missing and res.confidence > existing.confidence):
                    all_results[res.field_key] = res

        merged_results = list(all_results.values())

        if not merged_results:
            logger.warning("extraction.no_results claim=%s — all documents failed", claim_id)
            await transition_claim_status(
                db, claim, ClaimStatus.DRAFT,
                user_id=uuid.UUID(user_id),
                note="Extraction failed: no results from any document",
            )
            await db.commit()
            return {
                "claim_id": claim_id,
                "fields_extracted": 0,
                "fields_missing": 0,
                "duration_seconds": round(time.monotonic() - start, 2),
                "error": "All extraction backends failed",
            }

        # Write fields to DB
        await upsert_extracted_fields(db, claim, merged_results, uuid.UUID(user_id))

        # Transition to EXTRACTED
        await transition_claim_status(
            db, claim, ClaimStatus.EXTRACTED,
            user_id=uuid.UUID(user_id),
            note="Document extraction complete",
        )
        await db.commit()

    elapsed = time.monotonic() - start
    extracted = sum(1 for r in merged_results if not r.is_missing)
    missing = sum(1 for r in merged_results if r.is_missing)
    logger.info(
        "extraction.complete claim=%s extracted=%d missing=%d duration=%.1fs",
        claim_id, extracted, missing, elapsed,
    )
    return {
        "claim_id": claim_id,
        "fields_extracted": extracted,
        "fields_missing": missing,
        "duration_seconds": round(elapsed, 2),
    }


async def _mark_failed(claim_id: str, user_id: str, error: str) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Claim).where(Claim.id == uuid.UUID(claim_id)))
        claim = result.scalar_one_or_none()
        if claim and claim.status == ClaimStatus.PROCESSING:
            await transition_claim_status(
                db, claim, ClaimStatus.DRAFT,
                user_id=uuid.UUID(user_id),
                note=f"Extraction failed: {error}",
            )
            await db.commit()
