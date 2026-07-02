from __future__ import annotations

from typing import Any, TypedDict

from app.agents.base import Observation
from app.bft.models import BFTSnapshot


class TurnState(TypedDict):
    phone: str
    channel: str  # "chat" | "ussd"
    message: str
    bft: BFTSnapshot
    observations: list[Observation]
    response: str
    suggested_actions: list[str]
    state_update: dict[str, Any] | None  # set by financial_psyche, applied by update_state node
