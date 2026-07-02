"""Crisis Intercept - the one agent whose entire job is noticing the BFT has
already crossed into CRISIS and getting a human in the loop, rather than
proposing more automated advice. Runs at every trust level - a user in
crisis doesn't lose this safety net for having shared less data.
"""

from __future__ import annotations

from app.agents.base import Observation, TurnContext
from app.bft.models import BehavioralState


class CrisisInterceptAgent:
    name = "crisis_intercept"
    min_trust_level = 0

    async def run(self, ctx: TurnContext) -> Observation | None:
        if ctx.bft.behavioral_state != BehavioralState.CRISIS:
            return None

        return Observation(
            agent=self.name,
            headline="This has crossed into crisis territory - you shouldn't have to handle it alone.",
            details={"behavioral_state": ctx.bft.behavioral_state.name, "score": ctx.bft.state_score},
            severity="critical",
            suggested_actions=["Talk to a human advisor now", "Show me emergency schemes"],
        )
