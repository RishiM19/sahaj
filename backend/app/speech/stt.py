"""Speech-to-text via faster-whisper - the "whisper-small, 244M" model from
the exec summary, run entirely on-device/self-hosted (CPU, int8 quantized).
This is what Voice & Accessibility uses for the Divya persona's voice-only
path (docs/AGENTS.md).
"""

from __future__ import annotations

import asyncio

from faster_whisper import WhisperModel

_MODEL_SIZE = "small"


class STTService:
    def __init__(self) -> None:
        self._model: WhisperModel | None = None

    def _get_model(self) -> WhisperModel:
        if self._model is None:
            self._model = WhisperModel(_MODEL_SIZE, device="cpu", compute_type="int8")
        return self._model

    async def transcribe(self, audio_path: str, language: str | None = None) -> str:
        model = self._get_model()

        def _run() -> str:
            segments, _info = model.transcribe(audio_path, language=language)
            return " ".join(segment.text.strip() for segment in segments).strip()

        return await asyncio.to_thread(_run)


_shared: STTService | None = None


def get_stt() -> STTService:
    global _shared
    if _shared is None:
        _shared = STTService()
    return _shared
