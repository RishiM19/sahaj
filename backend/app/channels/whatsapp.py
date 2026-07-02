"""Real Meta WhatsApp Cloud API webhook - replaces the /api/chat/message
simulator for Tier 2 once real credentials are configured (see
backend/.env.example). Same orchestrator turn as every other channel; this
file only speaks Meta's webhook verification handshake and message
send/receive JSON shape. Getting real credentials needs a Meta developer
account and phone number verification - manual steps this code can't do on
anyone's behalf, documented in docs/ROADMAP.md.
"""

from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, HTTPException, Request, Response

from app.config import get_settings

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])
_logger = logging.getLogger(__name__)


class WhatsAppClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._phone_number_id = settings.whatsapp_phone_number_id
        self._base_url = f"https://graph.facebook.com/{settings.whatsapp_api_version}"
        self._headers = {"Authorization": f"Bearer {settings.whatsapp_access_token}"}

    async def send_text(self, to: str, body: str) -> None:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._base_url}/{self._phone_number_id}/messages",
                headers=self._headers,
                json={
                    "messaging_product": "whatsapp",
                    "to": to,
                    "type": "text",
                    "text": {"body": body},
                },
            )
            resp.raise_for_status()


@router.get("/webhook")
async def verify_webhook(request: Request):
    """Meta's one-time handshake when you register a webhook URL: echo back
    hub.challenge if hub.verify_token matches what's configured."""
    settings = get_settings()
    params = request.query_params
    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == settings.whatsapp_verify_token
        and settings.whatsapp_verify_token  # never match on an unset (empty) token
    ):
        return Response(content=params.get("hub.challenge", ""), media_type="text/plain")
    raise HTTPException(status_code=403, detail="webhook verification failed")


@router.post("/webhook")
async def receive_message(request: Request):
    settings = get_settings()
    if not (settings.whatsapp_access_token and settings.whatsapp_phone_number_id):
        raise HTTPException(
            status_code=503,
            detail="WhatsApp Cloud API not configured - set WHATSAPP_* in .env (see docs/ROADMAP.md)",
        )

    payload = await request.json()
    message = _extract_message(payload)
    if message is None:
        return {"status": "ignored"}  # status update / delivery receipt / non-text, not a user message

    phone, text = message
    orchestrator = request.app.state.orchestrator
    result = await orchestrator.handle_turn(phone=phone, channel="whatsapp", message=text)

    try:
        await WhatsAppClient().send_text(phone, result["response"])
    except httpx.HTTPStatusError as exc:
        _logger.error("WhatsApp send failed: %s", exc.response.text)

    return {"status": "ok"}


def _extract_message(payload: dict) -> tuple[str, str] | None:
    try:
        value = payload["entry"][0]["changes"][0]["value"]
        messages = value.get("messages")
        if not messages:
            return None
        msg = messages[0]
        if msg.get("type") != "text":
            return None
        return msg["from"], msg["text"]["body"]
    except (KeyError, IndexError):
        return None
