from __future__ import annotations

from app.agents.base import Observation, TurnContext
from app.llm.client import LLMClient

_SYSTEM = """You read one message from a financially stressed Indian user and judge their
emotional/behavioral state. Consider their recent income trend if given.
Reply with strict JSON only:
{
  "emotion": "<one or two words, e.g. anxious, resigned, hopeful>",
  "bias": "<a documented behavioral-finance bias this message shows, or null>",
  "urgency": <integer 0-100, how likely they are to act impulsively in the next hour>,
  "score_delta": <integer -20 to 30, how much this message should move their overall stress score>
}"""


class FinancialPsycheAgent:
    name = "financial_psyche"
    min_trust_level = 0

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    async def run(self, ctx: TurnContext) -> Observation | None:
        trend = ctx.bft.income_trend_pct
        trend_line = (
            f"Their income trend is {trend:+.0f}% vs. their recent average."
            if trend is not None
            else "No income history yet."
        )
        prompt = f"Message: {ctx.message!r}\n{trend_line}\nCurrent stress score: {ctx.bft.state_score}"

        try:
            result = await self._llm.complete_json(prompt, system=_SYSTEM)
        except Exception:
            return None

        new_score = max(0.0, min(100.0, ctx.bft.state_score + result.get("score_delta", 0)))
        urgency = result.get("urgency", 0)

        return Observation(
            agent=self.name,
            headline=f"Reads as {result.get('emotion', 'neutral')}"
            + (f", likely impulsive ({urgency}% urgency)" if urgency and urgency >= 60 else ""),
            details={
                "emotion": result.get("emotion"),
                "bias": result.get("bias"),
                "urgency": urgency,
                "proposed_score": new_score,
                "score_delta": result.get("score_delta", 0),
            },
            severity="warning" if urgency and urgency >= 60 else "info",
        )
