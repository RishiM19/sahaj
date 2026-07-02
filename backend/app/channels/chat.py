"""Tier 2 (WhatsApp-style) / Tier 4 (PWA) delivery channel.

Both tiers hit the same backend turn - see docs/PROBLEM.md, "same
intelligence, different interface." This router is what the frontend's chat
screen talks to; a real WhatsApp Cloud API webhook (Phase 2, see
docs/ROADMAP.md) would call the same `orchestrator.handle_turn` this does.
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.trust.upgrade import TrustUpgradeError

router = APIRouter(prefix="/api/chat", tags=["chat"])


class MessageIn(BaseModel):
    phone: str
    name: str | None = None
    message: str


class TrustIn(BaseModel):
    phone: str
    level: int


@router.post("/message")
async def send_message(body: MessageIn, request: Request):
    orchestrator = request.app.state.orchestrator
    if body.name:
        await orchestrator.bft.get_or_create_user(body.phone, name=body.name)

    result = await orchestrator.handle_turn(phone=body.phone, channel="chat", message=body.message)

    return {
        "reply": result["response"],
        "suggested_actions": result["suggested_actions"],
        "observations": [asdict(o) for o in result["observations"]],
        "bft": {
            "behavioral_state": result["bft"].behavioral_state.name,
            "state_score": result["bft"].state_score,
            "trust_level": result["bft"].trust_level,
        },
    }


@router.post("/trust")
async def raise_trust_level(body: TrustIn, request: Request):
    orchestrator = request.app.state.orchestrator
    try:
        result = await orchestrator.trust_upgrade.raise_level(body.phone, body.level)
    except TrustUpgradeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"phone": body.phone, "trust_level": result.level, "detail": result.detail}


@router.get("/bft/{phone}")
async def get_bft(phone: str, request: Request):
    orchestrator = request.app.state.orchestrator
    snapshot = await orchestrator.bft.get_or_create_user(phone)
    return {
        "phone": snapshot.phone,
        "name": snapshot.name,
        "behavioral_state": snapshot.behavioral_state.name,
        "state_score": snapshot.state_score,
        "trust_level": snapshot.trust_level,
        "income_trend_pct": snapshot.income_trend_pct,
        "current_balance": snapshot.current_balance,
        "income_verified": snapshot.income_verified,
        "digilocker_linked": snapshot.digilocker_linked,
    }
