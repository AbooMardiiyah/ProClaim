"""
ProClaim — NHIA Tariff Code Lookup Service
Maps procedure/service descriptions to NHIA/NHIS tariff codes.
"""
import json
import logging
import re
from difflib import SequenceMatcher
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


class NHIATariffLookup:
    def __init__(self) -> None:
        self._db: dict[str, str] = {}  # description → code
        self._load()

    def _load(self) -> None:
        path = Path(settings.NHIA_TARIFF_DB_PATH)
        if path.exists():
            with open(path) as f:
                data = json.load(f)
            for entry in data:
                desc = entry.get("description", "").lower().strip()
                code = entry.get("code", "").strip()
                if desc and code:
                    self._db[desc] = code
            logger.info("Loaded %d NHIA tariff codes from %s", len(self._db), path)
        else:
            logger.warning("NHIA tariff DB not found at %s", path)

    def lookup(self, procedure_text: str) -> str | None:
        if not procedure_text:
            return None
        query = procedure_text.lower().strip()

        if query in self._db:
            return self._db[query]

        query_words = set(re.findall(r"\w{4,}", query))
        for desc, code in self._db.items():
            desc_words = set(re.findall(r"\w{4,}", desc))
            if query_words and query_words.issubset(desc_words):
                return code

        best_ratio = 0.0
        best_code: str | None = None
        for desc, code in self._db.items():
            ratio = SequenceMatcher(None, query, desc).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_code = code

        return best_code if best_ratio >= 0.65 else None

    def describe(self, code: str) -> str | None:
        for desc, c in self._db.items():
            if c == code:
                return desc.title()
        return None
