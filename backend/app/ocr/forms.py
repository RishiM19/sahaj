"""Turns raw OCR text into the specific fields a known form needs - the
"fills forms field by field" half of Document Assist, not just a text dump.
Two schemas to start, matching what Kisan and Divya actually need to file
(docs/PROBLEM.md); growing this list is the same shape of work as growing
the scheme RAG seed set.
"""

from __future__ import annotations

from app.llm.client import LLMClient

FORM_SCHEMAS: dict[str, list[str]] = {
    "kisan_credit_card": [
        "applicant_name",
        "father_or_husband_name",
        "aadhaar_number",
        "land_holding_acres",
        "bank_account_number",
        "crop_type",
    ],
    "section_80dd": [
        "dependent_name",
        "relationship_to_applicant",
        "disability_type",
        "disability_percentage",
        "certificate_number",
        "certificate_date",
        "claim_amount",
    ],
}


def _extraction_system(fields: list[str]) -> str:
    field_list = ", ".join(fields)
    return (
        "You extract structured field values from OCR'd text of an Indian government "
        f"form. Extract exactly these fields: {field_list}. "
        "Reply with strict JSON only: an object with exactly those keys. "
        "If a field isn't present in the text, its value must be null. "
        "Do not invent values - only use what's actually in the text."
    )


class FormFieldExtractor:
    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    async def extract(self, form_type: str, ocr_text: str) -> dict[str, str | None]:
        fields = FORM_SCHEMAS.get(form_type)
        if fields is None:
            raise ValueError(f"unknown form_type {form_type!r} - known: {list(FORM_SCHEMAS)}")

        if not ocr_text.strip():
            return dict.fromkeys(fields)

        result = await self._llm.complete_json(
            f"OCR text:\n{ocr_text}", system=_extraction_system(fields)
        )
        return {field: result.get(field) for field in fields}
