"""Learning & Literacy - explains a financial term only at the moment it's
actually relevant, in the user's own terms, instead of a separate literacy
course nobody asked for. See docs/PROBLEM.md - "the real gap ... isn't a
missing literacy course."
"""

from __future__ import annotations

from app.agents.base import Observation, TurnContext
from app.llm.client import LLMClient

_SYSTEM = """A message from an Indian user may or may not contain a financial term or
product name (SIP, ULIP, EMI, KCC, NPS, 80C, etc.) that someone without a finance
background might not follow. If it does, explain that ONE term in plain language, in
one or two sentences, using an example with real rupee amounts if it helps. If the
message contains no such term, or the user clearly already understands it, say so.

Reply with strict JSON only: {"term": "<term or null>", "explanation": "<one or two
plain sentences, or null>"}"""


class LearningLiteracyAgent:
    name = "learning_literacy"
    min_trust_level = 1

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    async def run(self, ctx: TurnContext) -> Observation | None:
        try:
            result = await self._llm.complete_json(f"Message: {ctx.message!r}", system=_SYSTEM)
        except Exception:
            return None

        term, explanation = result.get("term"), result.get("explanation")
        if not term or not explanation:
            return None

        return Observation(
            agent=self.name,
            headline=f"{term}: {explanation}",
            details={"term": term, "explanation": explanation},
            severity="info",
        )
