"""The shared blackboard contract every agent writes to.

An agent never returns text meant for the user - it returns a typed
Observation, and only the Orchestrator (app/orchestrator/graph.py) composes
those into the one reply the user actually sees. See docs/AGENTS.md for why.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from app.bft.models import BFTSnapshot


@dataclass
class Observation:
    agent: str
    headline: str
    details: dict[str, Any] = field(default_factory=dict)
    severity: str = "info"  # info | warning | critical
    suggested_actions: list[str] = field(default_factory=list)


@dataclass
class TurnContext:
    """Everything on the blackboard for this one turn."""

    phone: str
    channel: str
    message: str
    bft: BFTSnapshot


class Agent(Protocol):
    name: str
    #: minimum PTP level required before the orchestrator will even dispatch this agent
    min_trust_level: int

    async def run(self, ctx: TurnContext) -> Observation | None: ...
