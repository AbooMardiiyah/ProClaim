"""
ProClaim — Document Upload & Extraction Trigger Endpoints

POST /claims/{claim_id}/documents          → upload one or more files
POST /claims/{claim_id}/extract            → trigger Gemini extraction (Celery task)
GET  /claims/{claim_id}/documents          → list documents for a claim
GET  /claims/{claim_id}/documents/{doc_id}/download → download a file
DELETE /claims/{claim_id}/documents/{doc_id}
"""
import os
import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.api.deps import CurrentUser, DB
from app.config import settings
from app.models.audit_log import AuditAction, AuditLog
from app.models.claim import Claim, ClaimDocument, ClaimStatus
from app.models.user import UserRole
from app.schemas.claim import ClaimDocumentRead
from app.workers.tasks import extract_documents

router = APIRouter(tags=["Documents"])

ALLOWED_MIME_TYPES = set(settings.ALLOWED_MIME_TYPES)


async def _save_file(upload: UploadFile, dest_dir: Path) -> tuple[Path, int]:
    """Stream upload to disk; return (path, size_bytes)."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    safe_basename = Path(upload.filename or "unnamed").name
    safe_name = f"{uuid.uuid4()}_{safe_basename}"
    dest_path = dest_dir / safe_name
    total = 0
    async with aiofiles.open(dest_path, "wb") as f:
        while chunk := await upload.read(1024 * 64):
            await f.write(chunk)
            total += len(chunk)
    return dest_path, total


@router.post(
    "/claims/{claim_id}/documents",
    response_model=list[ClaimDocumentRead],
    status_code=status.HTTP_201_CREATED,
)
async def upload_documents(
    claim_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
    files: list[UploadFile] = File(...),
) -> list[ClaimDocumentRead]:
    """Upload one or more documents to a claim (PDF, JPEG, PNG, TIFF)."""
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if current_user.role != UserRole.ADMIN and claim.hospital_id != current_user.hospital_id:
        raise HTTPException(status_code=403, detail="You do not have access to this claim.")

    saved: list[ClaimDocumentRead] = []
    upload_dir = Path(settings.UPLOAD_DIR) / str(claim_id)

    for upload in files:
        # Validate mime type
        content_type = upload.content_type or ""
        if content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {content_type}. Allowed: {list(ALLOWED_MIME_TYPES)}",
            )

        file_path, file_size = await _save_file(upload, upload_dir)

        if file_size > settings.max_upload_bytes:
            file_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=413,
                detail=f"File {upload.filename} exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit",
            )

        doc = ClaimDocument(
            claim_id=claim_id,
            file_name=upload.filename or file_path.name,
            file_path=str(file_path),
            file_size_bytes=file_size,
            mime_type=content_type,
        )
        db.add(doc)
        await db.flush()

        # Audit log
        db.add(AuditLog(
            claim_id=claim_id,
            user_id=current_user.id,
            action=AuditAction.DOCUMENT_UPLOADED,
            new_value=upload.filename,
            source_type="upload",
        ))

        saved.append(ClaimDocumentRead.model_validate(doc))

    return saved


@router.post("/claims/{claim_id}/extract", status_code=status.HTTP_202_ACCEPTED)
async def trigger_extraction(
    claim_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> dict:
    """
    Dispatch the Celery extraction task for all documents attached to this claim.
    Returns immediately with the task ID.
    """
    result = await db.execute(
        select(Claim).where(Claim.id == claim_id)
    )
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if current_user.role != UserRole.ADMIN and claim.hospital_id != current_user.hospital_id:
        raise HTTPException(status_code=403, detail="You do not have access to this claim.")

    if claim.status == ClaimStatus.PROCESSING:
        raise HTTPException(status_code=409, detail="Extraction already in progress")

    docs_result = await db.execute(
        select(ClaimDocument).where(ClaimDocument.claim_id == claim_id)
    )
    documents = docs_result.scalars().all()
    if not documents:
        raise HTTPException(status_code=400, detail="No documents attached to this claim")

    # Read file contents here in the API process and pass as base64 to the worker
    # This avoids shared filesystem dependency between API and worker containers
    import base64
    doc_payloads = []
    for d in documents:
        try:
            async with aiofiles.open(d.file_path, "rb") as f:
                content = await f.read()
            doc_payloads.append({
                "id": str(d.id),
                "file_name": d.file_name,
                "mime_type": d.mime_type,
                "content_b64": base64.b64encode(content).decode(),
            })
        except Exception:
            doc_payloads.append({
                "id": str(d.id),
                "file_name": d.file_name,
                "mime_type": d.mime_type,
                "content_b64": None,
            })

    task = extract_documents.delay(
        str(claim_id), doc_payloads, str(current_user.id)
    )

    return {
        "task_id": task.id,
        "claim_id": str(claim_id),
        "documents": len(doc_payloads),
        "message": "Extraction started. Poll /claims/{id} for status updates.",
    }


@router.get("/claims/{claim_id}/documents", response_model=list[ClaimDocumentRead])
async def list_documents(
    claim_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> list[ClaimDocumentRead]:
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if current_user.role != UserRole.ADMIN and claim.hospital_id != current_user.hospital_id:
        raise HTTPException(status_code=403, detail="You do not have access to this claim.")

    docs_result = await db.execute(
        select(ClaimDocument).where(ClaimDocument.claim_id == claim_id)
    )
    return [ClaimDocumentRead.model_validate(d) for d in docs_result.scalars().all()]


@router.get("/claims/{claim_id}/documents/{doc_id}/download")
async def download_document(
    claim_id: uuid.UUID,
    doc_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> FileResponse:
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if current_user.role != UserRole.ADMIN and claim.hospital_id != current_user.hospital_id:
        raise HTTPException(status_code=403, detail="You do not have access to this claim.")

    doc_result = await db.execute(
        select(ClaimDocument).where(
            ClaimDocument.id == doc_id, ClaimDocument.claim_id == claim_id
        )
    )
    doc = doc_result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not Path(doc.file_path).exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(doc.file_path, filename=doc.file_name, media_type=doc.mime_type)


@router.delete(
    "/claims/{claim_id}/documents/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    claim_id: uuid.UUID,
    doc_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> None:
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if current_user.role != UserRole.ADMIN and claim.hospital_id != current_user.hospital_id:
        raise HTTPException(status_code=403, detail="You do not have access to this claim.")

    doc_result = await db.execute(
        select(ClaimDocument).where(
            ClaimDocument.id == doc_id, ClaimDocument.claim_id == claim_id
        )
    )
    doc = doc_result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    Path(doc.file_path).unlink(missing_ok=True)
    await db.delete(doc)
