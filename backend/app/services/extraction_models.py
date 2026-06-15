"""
ProClaim — Shared extraction data models.
"""


class ExtractionResult:
    """Container for a single extracted field."""

    def __init__(
        self,
        field_key: str,
        field_label: str,
        value: str | None,
        confidence: int,
        page_number: int | None = None,
        bounding_box: dict | None = None,
        source_document_id: str | None = None,
    ) -> None:
        self.field_key = field_key
        self.field_label = field_label
        self.value = value
        self.confidence = confidence  # 0–100
        self.page_number = page_number
        self.bounding_box = bounding_box
        self.source_document_id = source_document_id

    @property
    def is_missing(self) -> bool:
        return self.value is None or str(self.value).strip() == ""

    @property
    def status(self) -> str:
        if self.is_missing:
            return "missing"
        return "extracted"
