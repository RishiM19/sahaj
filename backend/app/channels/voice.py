"""Tier 3 - the on-device/voice-first path (Divya persona: "entirely by
voice", see docs/PROBLEM.md). Wraps the same orchestrator turn every other
channel uses - STT in, orchestrator.handle_turn, TTS out - so voice is a
delivery-format difference, not a different reasoning path.
"""

from __future__ import annotations

import base64
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from app.speech.stt import get_stt
from app.speech.tts import get_tts

router = APIRouter(prefix="/api/voice", tags=["voice"])


class SpeakIn(BaseModel):
    text: str
    language: str = "en"


@router.post("/transcribe")
async def transcribe(audio: UploadFile = File(...), language: str | None = Form(None)):
    suffix = Path(audio.filename or "audio.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
        tmp.write(await audio.read())
        tmp.flush()
        try:
            text = await get_stt().transcribe(tmp.name, language=language)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"transcription failed: {exc}") from exc
    return {"text": text}


@router.post("/speak")
async def speak(body: SpeakIn):
    try:
        audio_bytes = await get_tts().synthesize(body.text, language=body.language)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(content=audio_bytes, media_type="audio/wav")


@router.post("/turn")
async def voice_turn(
    request: Request, phone: str = Form(...), audio: UploadFile = File(...)
):
    """The full round trip: audio in, orchestrator reasons, audio reply out."""
    orchestrator = request.app.state.orchestrator

    suffix = Path(audio.filename or "audio.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
        tmp.write(await audio.read())
        tmp.flush()
        try:
            transcript = await get_stt().transcribe(tmp.name)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"transcription failed: {exc}") from exc

    if not transcript:
        raise HTTPException(status_code=400, detail="couldn't hear anything in that clip")

    result = await orchestrator.handle_turn(phone=phone, channel="voice", message=transcript)
    language = result["bft"].language

    try:
        audio_bytes = await get_tts().synthesize(result["response"], language=language)
    except FileNotFoundError:
        audio_bytes = b""  # voice not available for this language yet - text reply still useful

    return {
        "transcript": transcript,
        "reply": result["response"],
        "suggested_actions": result["suggested_actions"],
        "audio_base64": base64.b64encode(audio_bytes).decode() if audio_bytes else None,
    }
