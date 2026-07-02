"""Thin wrapper around a self-hosted Ollama instance.

This is the shared model backbone every agent reasons through - see
docs/ARCHITECTURE.md for why Ollama serving `phi3:mini` replaced the
event-only KakushIN LLM API. Swapping to a different local model, or to a
hosted API, only touches this file.
"""

from __future__ import annotations

import json

import httpx

from app.config import get_settings


class LLMClient:
    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self._base_url = base_url or settings.ollama_url
        self._model = model or settings.ollama_model
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=120.0)

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.3,
        json_mode: bool = False,
    ) -> str:
        payload: dict = {
            "model": self._model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if json_mode:
            payload["format"] = "json"

        resp = await self._client.post("/api/generate", json=payload)
        resp.raise_for_status()
        return resp.json()["response"]

    async def complete_json(
        self, prompt: str, system: str | None = None, temperature: float = 0.2
    ) -> dict:
        raw = await self.complete(prompt, system=system, temperature=temperature, json_mode=True)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # small local models occasionally wrap JSON in prose despite format="json" -
            # fall back to pulling out the first {...} block rather than crashing the turn.
            start, end = raw.find("{"), raw.rfind("}")
            if start != -1 and end != -1:
                return json.loads(raw[start : end + 1])
            raise

    async def aclose(self) -> None:
        await self._client.aclose()


_shared_client: LLMClient | None = None


def get_llm() -> LLMClient:
    global _shared_client
    if _shared_client is None:
        _shared_client = LLMClient()
    return _shared_client
