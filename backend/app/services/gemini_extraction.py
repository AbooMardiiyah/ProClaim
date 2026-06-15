"""
ProClaim — Gemini 3.5 Flash Document Extraction Service

Gemini accepts PDFs/images directly and returns structured JSON
matching our field schema in a single API call.

Uses the Gemini REST API (v1) via aiohttp.
"""
import base64
import logging
from pathlib import Path
from typing import Any

import aiofiles
import aiohttp

from app.config import settings
from app.services.extraction_models import ExtractionResult

logger = logging.getLogger(__name__)

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1"
GEMINI_MODEL = "gemini-3.5-flash"


class GeminiExtractionService:
    """Wraps the Gemini 3.5 Flash generateContent REST API."""

    def __init__(self) -> None:
        self._api_key = settings.GEMINI_API_KEY

    # ── Public API ────────────────────────────────────────────────────────────

    async def analyze_document(
        self,
        file_path: str,
        field_configs: list[dict],
        document_id: str | None = None,
    ) -> list[ExtractionResult]:
        """
        Main entry point. Reads a file from disk, sends to Gemini,
        and returns a list of ExtractionResult objects.
        """
        path = Path(file_path)
        mime_type = self._guess_mime_type(path)
        file_name = path.name

        async with aiofiles.open(file_path, "rb") as f:
            file_bytes = await f.read()

        prompt = self._build_prompt(field_configs, file_name)
        schema = self._build_json_schema(field_configs)

        raw = await self._call_gemini(file_bytes, mime_type, prompt, schema)
        return self._map_to_extraction_results(raw, field_configs, document_id)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _guess_mime_type(self, path: Path) -> str:
        ext = path.suffix.lower()
        mapping = {
            ".pdf": "application/pdf",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".tiff": "image/tiff",
            ".tif": "image/tiff",
        }
        return mapping.get(ext, "application/octet-stream")

    def _build_prompt(self, field_configs: list[dict], file_name: str) -> str:
        lines = [
            "You are an expert medical claims document processor for the Nigerian National Health Insurance Authority (NHIA).",
            f"Extract structured data from the attached document ({file_name}).",
            "",
            "Return ONLY a JSON object with exactly the following keys. "
            "If a field is not found in the document, return an empty string '' for that key.",
            "Do not include markdown code blocks or any explanatory text — only raw JSON.",
            "",
            "Fields to extract:",
        ]
        for fc in field_configs:
            hint = fc.get("extraction_hint") or fc["name"]
            lines.append(f'- {fc["api_key"]}: {hint}')
        return "\n".join(lines)

    def _build_json_schema(self, field_configs: list[dict]) -> dict[str, Any]:
        """Build an OpenAPI-style schema for Gemini JSON mode."""
        properties: dict[str, Any] = {}
        for fc in field_configs:
            properties[fc["api_key"]] = {"type": "string"}
        return {
            "type": "object",
            "properties": properties,
        }

    async def _call_gemini(
        self,
        file_bytes: bytes,
        mime_type: str,
        prompt: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        url = (
            f"{GEMINI_BASE_URL}/models/{GEMINI_MODEL}:generateContent"
            f"?key={self._api_key}"
        )

        # Note: generationConfig.responseMimeType/responseSchema are NOT
        # supported in API v1. We rely on prompt instructions + text parsing.
        body: dict[str, Any] = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": base64.b64encode(file_bytes).decode(),
                            }
                        },
                    ]
                }
            ],
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=body) as resp:
                data = await resp.json()
                if resp.status != 200:
                    raise RuntimeError(
                        f"Gemini API error [{resp.status}]: {data}"
                    )

        return self._parse_gemini_response(data)

    def _parse_gemini_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """Pull the JSON object out of Gemini's response envelope."""
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError(f"Gemini returned no candidates: {data}")

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            raise RuntimeError(f"Gemini returned empty content: {data}")

        text = parts[0].get("text", "")
        if not text:
            raise RuntimeError(f"Gemini returned empty text: {data}")

        import json
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Gemini returned invalid JSON: {text}") from exc

        if not isinstance(parsed, dict):
            raise RuntimeError(f"Gemini returned non-object JSON: {parsed}")

        return parsed

    def _map_to_extraction_results(
        self,
        raw: dict[str, Any],
        field_configs: list[dict],
        document_id: str | None,
    ) -> list[ExtractionResult]:
        """Convert Gemini's flat JSON into ExtractionResult objects."""
        results: list[ExtractionResult] = []
        for fc in field_configs:
            key = fc["api_key"]
            label = fc["name"]
            value = raw.get(key)

            # Normalize to string or None
            if value is None or (isinstance(value, str) and value.strip() == ""):
                str_value: str | None = None
                confidence = 0
            else:
                str_value = str(value).strip()
                confidence = 85  # Gemini is generally accurate; no per-field score available

            results.append(
                ExtractionResult(
                    field_key=key,
                    field_label=label,
                    value=str_value,
                    confidence=confidence,
                    source_document_id=document_id,
                )
            )
        return results
