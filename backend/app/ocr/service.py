"""Document OCR - the engine behind Document Assist (docs/AGENTS.md).

The exec summary specified PaddleOCR. PaddlePaddle - PaddleOCR's underlying
deep-learning framework - does not currently publish any wheel for
Python 3.14 on any platform; `pip install paddlepaddle` fails outright in
this repo's dev environment before PaddleOCR itself is even involved. This
is a verifiable upstream gap, not something this codebase can route around.
Tesseract (via pytesseract) is the pragmatic, genuinely free/open-source
substitute behind the same OCRService interface below - swapping back to
PaddleOCR once it ships 3.14 wheels (or by running it as a separate service
pinned to an older Python) only touches this file.
"""

from __future__ import annotations

import asyncio

import pytesseract
from PIL import Image

# Tesseract language codes, not the BFT's ISO codes - see app/speech/tts.py
# for the equivalent mapping on the TTS side.
_LANG_BY_BFT_LANGUAGE = {
    "hi": "hin",
    "kn": "kan",
    "en": "eng",
}
_DEFAULT_LANG = "eng"


class OCRService:
    async def extract_text(self, image_path: str, language: str = "en") -> str:
        tess_lang = _LANG_BY_BFT_LANGUAGE.get(language, _DEFAULT_LANG)

        def _run() -> str:
            return pytesseract.image_to_string(Image.open(image_path), lang=tess_lang).strip()

        return await asyncio.to_thread(_run)


_shared: OCRService | None = None


def get_ocr() -> OCRService:
    global _shared
    if _shared is None:
        _shared = OCRService()
    return _shared
