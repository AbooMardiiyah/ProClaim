"""
ProClaim — ICD-10 Lookup Service
Loads the local JSON database and provides fuzzy diagnosis-to-code matching.
"""
import json
import logging
import re
from difflib import SequenceMatcher
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


class ICD10Lookup:
    """Fast in-memory ICD-10 code lookup with fuzzy string matching."""

    def __init__(self) -> None:
        self._db: dict[str, str] = {}  # description → code
        self._load()

    def _load(self) -> None:
        path = Path(settings.ICD10_DB_PATH)
        if path.exists():
            with open(path) as f:
                data = json.load(f)
            for entry in data:
                desc = entry.get("description", "").lower().strip()
                code = entry.get("code", "").strip()
                if desc and code:
                    self._db[desc] = code
            logger.info("Loaded %d ICD-10 codes from %s", len(self._db), path)
        else:
            logger.warning("ICD-10 database not found at %s", path)

    def lookup(self, diagnosis_text: str) -> str | None:
        if not diagnosis_text:
            return None
        query = diagnosis_text.lower().strip()

        # Exact match
        if query in self._db:
            return self._db[query]

        # Keyword match — any entry whose description contains all major words
        query_words = set(re.findall(r"\w{4,}", query))
        for desc, code in self._db.items():
            desc_words = set(re.findall(r"\w{4,}", desc))
            if query_words and query_words.issubset(desc_words):
                return code

        # Fuzzy match (SequenceMatcher)
        best_ratio = 0.0
        best_code: str | None = None
        for desc, code in self._db.items():
            ratio = SequenceMatcher(None, query, desc).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_code = code

        if best_ratio >= 0.65:
            return best_code
        return None

    def describe(self, code: str) -> str | None:
        """Reverse lookup: code → description."""
        for desc, c in self._db.items():
            if c == code:
                return desc.title()
        return None
