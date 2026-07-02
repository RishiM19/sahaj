"""Cash Flow agent - SIII (Seasonal & Irregular Income Intelligence)
projection, backed by a real Monte Carlo simulation (this is also the
numeric engine the Life Simulator/FLSE agent narrates - see
life_simulator.py). The income model applies the structured seasonality in
app/agents/seasonal.py (crop calendar, gig demand cycle, MNREGA) on top of
each user's own recency-weighted mean/std, rather than treating every week
as an independent draw from a flat distribution.
"""

from __future__ import annotations

import re

import numpy as np

from app.agents.base import Observation, TurnContext
from app.agents.seasonal import IncomeSource, expected_mnrega_topup, month_for_week_offset, monthly_multiplier
from app.bft.models import BFTSnapshot

TRIALS = 10_000
HORIZON_DAYS = 30


class MonteCarloResult:
    def __init__(
        self,
        deficit_probability: float,
        median_shortfall: float,
        first_deficit_day: int | None,
        day_by_day_p70: list[dict],
    ) -> None:
        self.deficit_probability = deficit_probability
        self.median_shortfall = median_shortfall
        self.first_deficit_day = first_deficit_day
        self.day_by_day_p70 = day_by_day_p70


def extract_loan_amount(message: str) -> float | None:
    m = re.search(r"₹\s?([\d,]+)", message)
    if not m:
        return None
    return float(m.group(1).replace(",", ""))


def run_monte_carlo(bft: BFTSnapshot, extra_inflow: float = 0.0) -> MonteCarloResult:
    samples = [s.amount for s in bft.income_samples] or [8_000.0]
    # weight recent weeks more than old ones, so a declining trend actually
    # pulls the projection down instead of being smoothed away by a flat
    # historical average - a real SIII model would trend-extrapolate; this is
    # the Phase 1 approximation of that (see docs/ROADMAP.md).
    weights = np.linspace(1.0, 2.0, num=len(samples))
    weekly_mean = float(np.average(samples, weights=weights))
    weekly_std = float(np.std(samples)) if len(samples) > 1 else weekly_mean * 0.25
    weekly_std = max(weekly_std, weekly_mean * 0.15)

    start_balance = bft.current_balance if bft.current_balance is not None else weekly_mean * 1.8
    expenses = list(bft.fixed_expenses or [])
    if extra_inflow > 0:
        # the loan itself gets consumed by whatever emergency prompted asking
        # for it - it's not free cash sitting in the account. What it actually
        # costs going forward is the repayment, at a typical unregistered-
        # lender rate, which is what should show up as a risk to future cash
        # flow.
        expenses.append({"label": "EMI (new loan)", "amount": extra_inflow * 0.213, "due_day": 8})

    source = IncomeSource(bft.income_source)
    rng = np.random.default_rng()
    weeks = HORIZON_DAYS // 7 + 1
    # each week gets its own seasonal multiplier and MNREGA top-up based on
    # which calendar month it falls in - a farmer's week 4 (post-monsoon
    # sowing) looks nothing like a gig worker's week 4 (Diwali demand spike),
    # even off the same historical mean/std
    week_months = [month_for_week_offset(w) for w in range(weeks)]
    seasonal_mults = np.array([monthly_multiplier(source, m) for m in week_months])
    mnrega_topups = np.array([expected_mnrega_topup(source, m) for m in week_months])

    # trials x weeks matrix of simulated weekly income, floored at 0
    weekly_income = np.clip(
        rng.normal(weekly_mean, weekly_std, size=(TRIALS, weeks)) * seasonal_mults + mnrega_topups,
        0,
        None,
    )

    balances = np.full(TRIALS, start_balance, dtype=float)
    day_by_day: list[dict] = []
    first_deficit_day = np.full(TRIALS, -1, dtype=int)

    for day in range(1, HORIZON_DAYS + 1):
        if day % 7 == 1:
            week_idx = day // 7
            balances += weekly_income[:, week_idx]
        for exp in expenses:
            if exp["due_day"] == day:
                balances -= exp["amount"]

        newly_negative = (balances < 0) & (first_deficit_day == -1)
        first_deficit_day[newly_negative] = day

        if day in (7, 14, 21, 30):
            day_by_day.append(
                {"day": day, "balance_p70": float(np.percentile(balances, 30))}
            )  # 30th pct of balance = 70% of trials are at or above this (the "7 of 10" framing)

    deficit_mask = first_deficit_day != -1
    deficit_probability = float(deficit_mask.mean())
    shortfalls = -balances[balances < 0]
    median_shortfall = float(np.median(shortfalls)) if len(shortfalls) else 0.0
    median_first_day = (
        int(np.median(first_deficit_day[deficit_mask])) if deficit_mask.any() else None
    )

    return MonteCarloResult(
        deficit_probability=deficit_probability,
        median_shortfall=median_shortfall,
        first_deficit_day=median_first_day,
        day_by_day_p70=day_by_day,
    )


class CashFlowAgent:
    name = "cash_flow"
    min_trust_level = 2  # needs an income range - PTP Level 2

    async def run(self, ctx: TurnContext) -> Observation | None:
        loan_amount = extract_loan_amount(ctx.message)
        result = run_monte_carlo(ctx.bft, extra_inflow=loan_amount or 0.0)

        if loan_amount:
            headline = (
                f"Borrowing ₹{loan_amount:,.0f} today puts you in deficit "
                f"in {result.first_deficit_day} days."
                if result.first_deficit_day
                else f"Borrowing ₹{loan_amount:,.0f} today looks affordable over the next 30 days."
            )
        else:
            headline = (
                f"{result.deficit_probability * 100:.0f}% chance of a cash deficit in the next 30 days."
            )

        return Observation(
            agent=self.name,
            headline=headline,
            details={
                "loan_amount": loan_amount,
                "deficit_probability": round(result.deficit_probability, 2),
                "first_deficit_day": result.first_deficit_day,
                "median_shortfall": round(result.median_shortfall, 0),
                "trials": TRIALS,
                "income_verified": ctx.bft.income_verified,
                "income_source": ctx.bft.income_source,
            },
            severity="critical" if result.deficit_probability > 0.5 else "warning"
            if result.deficit_probability > 0.2
            else "info",
        )
