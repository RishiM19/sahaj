"""Seasonal & Irregular Income Intelligence (SIII) - the structured-seasonality
layer that upgrades cash_flow.py's Monte Carlo from a flat recency-weighted
mean/std to something that actually knows gig income dips in the monsoon and
spikes around festivals, and that a farmer's income isn't irregular noise but
a predictable sowing-to-harvest cycle.

This is NOT a model trained on real gig-platform/crop-yield/MNREGA datasets -
nobody building this outside an institution has access to that data. What's
here is hand-encoded domain knowledge (India's two main cropping seasons,
known festival/monsoon demand swings for gig platforms, MNREGA as a
predictable income floor) rather than a black box - see docs/ROADMAP.md for
why a real trained model is future work, not something to fake with
synthetic training data that would just encode these same assumptions
anyway.
"""

from __future__ import annotations

from datetime import date, timedelta
from enum import StrEnum


class IncomeSource(StrEnum):
    GIG = "gig"  # platform work - Swiggy/Ola/Zomato-style, demand-driven
    FARMER = "farmer"  # seasonal crop income, kharif/rabi cycle
    SALARIED = "salaried"  # stable monthly salary, minimal seasonality


# Kharif (monsoon-sown, autumn-harvested) and Rabi (winter-sown,
# spring-harvested) are India's two dominant cropping seasons. Sowing months
# carry negative/near-zero income (money going out on inputs, KCC issue);
# harvest months carry a multi-week income spike.
_FARMER_MONTHLY_MULTIPLIER = {
    1: 0.3, 2: 0.3, 3: 1.6, 4: 2.2, 5: 0.6,  # rabi sowing -> rabi harvest (Mar-Apr) -> lean
    6: 0.3, 7: 0.4, 8: 0.5, 9: 0.6, 10: 1.8,  # kharif sowing (Jun) -> kharif harvest (Oct)
    11: 2.0, 12: 0.8,
}

# Gig demand: festival season (Oct-Nov, Diwali) spikes order/ride volume;
# monsoon (Jun-Sep) suppresses it (fewer people out, delivery slowdowns).
_GIG_MONTHLY_MULTIPLIER = {
    1: 1.0, 2: 1.0, 3: 1.0, 4: 0.95, 5: 0.95,
    6: 0.8, 7: 0.75, 8: 0.8, 9: 0.85,
    10: 1.3, 11: 1.35, 12: 1.15,
}

_SALARIED_MONTHLY_MULTIPLIER: dict[int, float] = {m: 1.0 for m in range(1, 13)}

_TABLES = {
    IncomeSource.FARMER: _FARMER_MONTHLY_MULTIPLIER,
    IncomeSource.GIG: _GIG_MONTHLY_MULTIPLIER,
    IncomeSource.SALARIED: _SALARIED_MONTHLY_MULTIPLIER,
}

# MNREGA guarantees up to 100 days/year of rural wage work on demand - modelled
# as a per-week probability of picking up a work day during a farmer's lean
# months, at a typical notified wage rate. This is what keeps a seasonal dip
# from being pure downside in the simulation, same as it is in practice.
_MNREGA_DAILY_WAGE = 300.0
_MNREGA_LEAN_MONTH_PICKUP_PROB = 0.4


def monthly_multiplier(source: IncomeSource, month: int) -> float:
    return _TABLES[source][month]


def month_for_week_offset(weeks_from_now: int, today: date | None = None) -> int:
    """Which calendar month a simulated week (0-indexed, weeks from today) falls in."""
    base = today or date.today()
    day = base + timedelta(weeks=weeks_from_now)
    return day.month


def expected_mnrega_topup(source: IncomeSource, month: int) -> float:
    if source != IncomeSource.FARMER:
        return 0.0
    if monthly_multiplier(source, month) >= 1.0:
        return 0.0  # harvest/mid-season - not the point of the safety net
    return _MNREGA_DAILY_WAGE * _MNREGA_LEAN_MONTH_PICKUP_PROB
