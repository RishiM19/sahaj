"""Scheme Navigator - matches a user to real government schemes via the
Qdrant RAG index in app/rag/schemes.py. Runs on every turn at PTP Level 1+
so it can surface a relevant scheme even when nothing else fired (e.g. a
scam alert always offers "find a scheme that fits" as a next step)."""

from __future__ import annotations

from app.agents.base import Observation, TurnContext
from app.rag.schemes import SchemeIndex

_MIN_RELEVANCE = 0.35  # cosine similarity floor - below this, nothing's a real match


class SchemeNavigatorAgent:
    name = "scheme_navigator"
    min_trust_level = 1  # needs at least a name on file - PTP Level 1

    def __init__(self, index: SchemeIndex) -> None:
        self._index = index

    async def run(self, ctx: TurnContext) -> Observation | None:
        try:
            hits = await self._index.search(ctx.message, top_k=3)
        except Exception:
            return None

        relevant = [h for h in hits if h["score"] >= _MIN_RELEVANCE]
        if not relevant:
            return None

        top = relevant[0]
        headline = f"{top['name']} looks relevant - {top['benefit']}"

        return Observation(
            agent=self.name,
            headline=headline,
            details={
                "matches": [
                    {"name": h["name"], "score": h["score"], "benefit": h["benefit"], "apply_via": h["apply_via"]}
                    for h in relevant
                ]
            },
            severity="info",
            suggested_actions=[f"Tell me more about {top['name']}"],
        )
