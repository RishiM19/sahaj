"""Tier 1 - USSD `*99#` simulator.

A real deployment needs a telecom/NPCI aggregator agreement to receive
actual `*99#` sessions (see docs/ARCHITECTURE.md) - out of reach for an
individual project. This router speaks the same request/response shape a
real Go USSD handler would sit in front of, so swapping the simulator for a
real gateway integration later is a transport change, not a logic change.
Same orchestrator turn as the chat channel; the only difference is the
reply gets flattened into a short numbered menu instead of a rich chat
bubble, because that's all a feature-phone screen can show.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api/ussd", tags=["ussd"])

_USSD_CHAR_LIMIT = 182  # matches the real *99# session response limit


class UssdIn(BaseModel):
    phone: str
    message: str


def _render_menu(reply: str, suggested_actions: list[str]) -> str:
    text = reply.strip()
    if len(text) > _USSD_CHAR_LIMIT:
        text = text[: _USSD_CHAR_LIMIT - 1].rstrip() + "…"
    if suggested_actions:
        options = "\n".join(f"{i}. {a}" for i, a in enumerate(suggested_actions, start=1))
        text = f"{text}\n\n{options}\n\nReply 1-{len(suggested_actions)} and press Send"
    return text


@router.post("/message")
async def send_ussd_message(body: UssdIn, request: Request):
    orchestrator = request.app.state.orchestrator
    result = await orchestrator.handle_turn(phone=body.phone, channel="ussd", message=body.message)

    return {
        "screen": _render_menu(result["response"], result["suggested_actions"]),
        "suggested_actions": result["suggested_actions"],
    }
