"""Text-to-speech via Piper-TTS - fully local/free, ONNX voices. The exec
summary called for 22 regional voices; this repo ships two (Hindi and
English) as a real, working starting point - see docs/ROADMAP.md for
growing that list, and `backend/app/data/voices/README.md` for how to add
more with the same `python -m piper.download_voices` command used here.
"""

from __future__ import annotations

import asyncio
import io
import wave
from pathlib import Path

from piper import PiperVoice

_VOICES_DIR = Path(__file__).resolve().parent.parent / "data" / "voices"

# language code (as stored on the BFT, see app/bft/models.py) -> Piper voice name
_VOICE_BY_LANGUAGE = {
    "hi": "hi_IN-pratham-medium",
    "en": "en_US-lessac-medium",
}
_DEFAULT_LANGUAGE = "en"


class TTSService:
    def __init__(self) -> None:
        self._voices: dict[str, PiperVoice] = {}

    def _get_voice(self, language: str) -> PiperVoice:
        voice_name = _VOICE_BY_LANGUAGE.get(language, _VOICE_BY_LANGUAGE[_DEFAULT_LANGUAGE])
        if voice_name not in self._voices:
            model_path = _VOICES_DIR / f"{voice_name}.onnx"
            if not model_path.exists():
                raise FileNotFoundError(
                    f"voice {voice_name!r} not downloaded - run: "
                    f"python -m piper.download_voices --download-dir {_VOICES_DIR} {voice_name}"
                )
            self._voices[voice_name] = PiperVoice.load(str(model_path))
        return self._voices[voice_name]

    async def synthesize(self, text: str, language: str = _DEFAULT_LANGUAGE) -> bytes:
        voice = self._get_voice(language)

        def _run() -> bytes:
            buf = io.BytesIO()
            with wave.open(buf, "wb") as wav_file:
                voice.synthesize_wav(text, wav_file)
            return buf.getvalue()

        return await asyncio.to_thread(_run)


_shared: TTSService | None = None


def get_tts() -> TTSService:
    global _shared
    if _shared is None:
        _shared = TTSService()
    return _shared
