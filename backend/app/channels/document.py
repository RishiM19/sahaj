"""Document Assist - scan a physical form, get back field values instead of
a wall of raw OCR text. Kisan's Kisan Credit Card application and Divya's
Section 80DD claim (docs/PROBLEM.md) are the two schemas shipped so far -
see app/ocr/forms.py. Gated at PTP Level 4 (DigiLocker) per docs/PTP.md -
document-verified form-filling is exactly what that level is for.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from app.ocr.forms import FORM_SCHEMAS, FormFieldExtractor
from app.ocr.service import get_ocr

router = APIRouter(prefix="/api/document", tags=["document"])

_REQUIRED_TRUST_LEVEL = 4


@router.get("/forms")
async def list_forms():
    return {"forms": FORM_SCHEMAS}


@router.post("/scan")
async def scan_document(
    request: Request,
    phone: str = Form(...),
    form_type: str = Form(...),
    language: str = Form("en"),
    image: UploadFile = File(...),
):
    if form_type not in FORM_SCHEMAS:
        raise HTTPException(
            status_code=400, detail=f"unknown form_type {form_type!r} - known: {list(FORM_SCHEMAS)}"
        )

    orchestrator = request.app.state.orchestrator
    snapshot = await orchestrator.bft.get_or_create_user(phone)
    if snapshot.trust_level < _REQUIRED_TRUST_LEVEL:
        raise HTTPException(
            status_code=403,
            detail=f"Document Assist needs trust level {_REQUIRED_TRUST_LEVEL} (DigiLocker linked), "
            f"this user is at level {snapshot.trust_level}",
        )

    suffix = Path(image.filename or "scan.png").suffix or ".png"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
        tmp.write(await image.read())
        tmp.flush()
        try:
            ocr_text = await get_ocr().extract_text(tmp.name, language=language)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"OCR failed: {exc}") from exc

    extractor = FormFieldExtractor(orchestrator.llm)
    fields = await extractor.extract(form_type, ocr_text)

    return {
        "form_type": form_type,
        "raw_text": ocr_text,
        "fields": fields,
        "fields_found": sum(1 for v in fields.values() if v),
        "fields_total": len(fields),
    }
