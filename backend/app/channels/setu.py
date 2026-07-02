"""Real Setu Account Aggregator consent flow - additive to, not a
replacement for, the mocked instant-approve path in
POST /api/chat/trust (app/channels/chat.py). Real consent is asynchronous:
the user approves it in their AA app, so this is two calls (start, then
finalize once approved) rather than one - see app/integrations/setu.py for
what's verified against Setu's docs versus best-effort.
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.integrations.setu import SetuAAClient, SetuNotConfigured

router = APIRouter(prefix="/api/chat/trust/consent", tags=["trust"])


class ConsentStartIn(BaseModel):
    phone: str


class ConsentFinalizeIn(BaseModel):
    phone: str
    consent_id: str


async def _call_setu(coro):
    """Every Setu call fails one of two ways from here out: not configured
    (ours to fix, 503) or the sandbox itself rejected the request (theirs,
    surfaced as a 502 with their actual error body rather than an opaque 500 -
    that's what told us during development that a fake token gets a real,
    correctly-shaped 401 back)."""
    try:
        return await coro
    except SetuNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502, detail=f"Setu sandbox returned {exc.response.status_code}: {exc.response.text}"
        ) from exc


@router.post("/start")
async def start_consent(body: ConsentStartIn):
    client = SetuAAClient()
    consent = await _call_setu(
        client.create_consent(vua=body.phone, purpose="SAHAJ cash-flow verification")
    )
    return {
        "consent_id": consent.id,
        "status": consent.status,
        "approval_url": consent.approval_url,
        "next_step": "Have the user approve this in their Account Aggregator app, "
        "then call /finalize with the same consent_id.",
    }


@router.post("/finalize")
async def finalize_consent(body: ConsentFinalizeIn, request: Request):
    client = SetuAAClient()
    status = await _call_setu(client.get_consent_status(body.consent_id))

    if status != "ACTIVE":
        return {"status": status, "trust_level_granted": False}

    orchestrator = request.app.state.orchestrator
    snapshot = await orchestrator.bft.get_or_create_user(body.phone)
    if snapshot.trust_level < 2:
        raise HTTPException(
            status_code=400,
            detail=f"Level 3 needs Level 2 (income range) first, currently at {snapshot.trust_level}",
        )

    await orchestrator.bft.set_income_verified(body.phone, True)
    if snapshot.trust_level < 3:
        await orchestrator.bft.set_trust_level(body.phone, 3)
    return {"status": status, "trust_level_granted": True, "trust_level": 3}
