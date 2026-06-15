"""
ProClaim — Document Extraction Service

Primary extractor powered by Google Gemini 3.5 Flash.
"""
import logging

from app.config import settings
from app.services.extraction_models import ExtractionResult
from app.services.gemini_extraction import GeminiExtractionService
from app.services.icd10_lookup import ICD10Lookup
from app.services.nhia_tariff import NHIATariffLookup

logger = logging.getLogger(__name__)


class DocumentExtractionService:
    """
    Primary extractor powered by Google Gemini 3.5 Flash.
    """

    def __init__(self) -> None:
        self._gemini: GeminiExtractionService | None = None

    async def analyze_document(
        self,
        file_path: str,
        field_configs: list[dict],
        document_id: str | None = None,
    ) -> list[ExtractionResult]:
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not configured")

        if self._gemini is None:
            self._gemini = GeminiExtractionService()

        results = await self._gemini.analyze_document(
            file_path, field_configs, document_id
        )
        return self._post_process(results)

    def _post_process(self, results: list[ExtractionResult]) -> list[ExtractionResult]:
        """
        Enrich results:
        - ICD-10 lookup: if primary_diagnosis extracted but no icd10_code, auto-derive
        - NHIA tariff lookup: if procedure_desc but no nhia_tariff_code, auto-derive
        - Clamp confidence to [0, 100]
        """
        icd10 = ICD10Lookup()
        nhia = NHIATariffLookup()
        field_map = {r.field_key: r for r in results}

        # Auto ICD-10
        diagnosis_result = field_map.get("primary_diagnosis")
        icd10_result = field_map.get("icd10_code")
        if (
            diagnosis_result
            and not diagnosis_result.is_missing
            and icd10_result
            and icd10_result.is_missing
        ):
            code = icd10.lookup(diagnosis_result.value or "")
            if code:
                icd10_result.value = code
                icd10_result.confidence = 75
                logger.debug("Auto-assigned ICD-10 %s for %s", code, diagnosis_result.value)

        # Auto NHIA tariff
        proc_result = field_map.get("procedure_desc")
        tariff_result = field_map.get("nhia_tariff_code")
        if (
            proc_result
            and not proc_result.is_missing
            and tariff_result
            and tariff_result.is_missing
        ):
            code = nhia.lookup(proc_result.value or "")
            if code:
                tariff_result.value = code
                tariff_result.confidence = 72
                logger.debug("Auto-assigned NHIA tariff %s for %s", code, proc_result.value)

        # Clamp confidence
        for r in results:
            r.confidence = max(0, min(100, r.confidence))

        return results
