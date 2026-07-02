"""Life Simulator - narrates the Cash Flow agent's Monte Carlo run as a short
"what happens next" story (FLSE). Reuses cash_flow.run_monte_carlo rather
than re-simulating, so the numbers Cash Flow warns about and the story Life
Simulator tells always agree.
"""

from __future__ import annotations

from app.agents.base import Observation, TurnContext
from app.agents.cash_flow import extract_loan_amount, run_monte_carlo
from app.llm.client import LLMClient

_SYSTEM = """You narrate a personal-finance Monte Carlo simulation as a short, plain-spoken
story a worried person could listen to, in the style of: "It's December, your income is
down 40%, EMI in eight days - here's what the month after looks like." Two to four
sentences. Use the numbers given, don't invent new ones. No disclaimers, no bullet points,
just the story."""


class LifeSimulatorAgent:
    name = "life_simulator"
    min_trust_level = 2

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    async def run(self, ctx: TurnContext) -> Observation | None:
        loan_amount = extract_loan_amount(ctx.message)
        if loan_amount is None:
            return None  # nothing hypothetical to simulate this turn

        result = run_monte_carlo(ctx.bft, extra_inflow=loan_amount)
        emi = round(loan_amount * 0.213)

        facts = (
            f"Borrowing ₹{loan_amount:,.0f} today means an EMI of ₹{emi:,.0f} due in 8 days. "
            f"{result.deficit_probability * 100:.0f}% of {10_000} simulated futures run into a "
            f"cash deficit within 30 days"
            + (
                f", typically around day {result.first_deficit_day}, average shortfall "
                f"₹{result.median_shortfall:,.0f}."
                if result.first_deficit_day
                else "."
            )
            + " Use only the ₹ figures given above - do not invent any other amounts."
        )

        try:
            narrative = await self._llm.complete(facts, system=_SYSTEM, temperature=0.6)
        except Exception:
            narrative = facts

        return Observation(
            agent=self.name,
            headline=narrative.strip(),
            details={
                "loan_amount": loan_amount,
                "deficit_probability": round(result.deficit_probability, 2),
                "day_by_day": result.day_by_day_p70,
            },
            severity="warning" if result.deficit_probability > 0.3 else "info",
        )
