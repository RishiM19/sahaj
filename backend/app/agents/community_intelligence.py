"""Community Intelligence - reads the CFTI signal pool for anything nearby,
independent of what this specific user asked about. Phase 1/2 implementation
is a single-node Postgres read (see app/db/cfti.py); Phase 3 replaces the
underlying store with genuine federated learning across devices without
changing this agent's contract. Runs at PTP Level 0 - this is exactly the
"zero personal data, full CFTI benefit" case from docs/PTP.md.
"""

from __future__ import annotations

from app.agents.base import Observation, TurnContext
from app.db import cfti


class CommunityIntelligenceAgent:
    name = "community_intelligence"
    min_trust_level = 0

    def __init__(self, pg_pool) -> None:
        self._pool = pg_pool

    async def run(self, ctx: TurnContext) -> Observation | None:
        summary = await cfti.recent_area_summary(self._pool, area=None, days=7)
        if summary["total_reports"] == 0:
            return None

        return Observation(
            agent=self.name,
            headline=(
                f"{summary['distinct_entities']} scam pattern(s) reported nearby "
                f"in the last {summary['days']} days."
            ),
            details=summary,
            severity="info",
        )
