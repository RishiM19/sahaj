from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum


class BehavioralState(IntEnum):
    """Ordered so `state >= BehavioralState.STRESSED` reads naturally."""

    STABLE = 0
    STRESSED = 1
    VULNERABLE = 2
    CRISIS = 3

    @classmethod
    def from_score(cls, score: float) -> "BehavioralState":
        if score >= 76:
            return cls.CRISIS
        if score >= 51:
            return cls.VULNERABLE
        if score >= 26:
            return cls.STRESSED
        return cls.STABLE


@dataclass
class IncomeSample:
    amount: float
    source: str
    timestamp: str


@dataclass
class BFTSnapshot:
    """Everything an agent needs to know about a user before it reasons."""

    phone: str
    name: str | None
    language: str
    trust_level: int
    behavioral_state: BehavioralState
    state_score: float
    income_samples: list[IncomeSample] = field(default_factory=list)
    fixed_expenses: list[dict] = field(default_factory=list)  # [{label, amount, due_day}]
    current_balance: float | None = None
    income_verified: bool = False  # PTP Level 3 - confirmed via Account Aggregator, not self-declared
    digilocker_linked: bool = False  # PTP Level 4
    income_source: str = "gig"  # "gig" | "farmer" | "salaried" - see app/agents/seasonal.py

    @property
    def income_trend_pct(self) -> float | None:
        """% change of the most recent sample vs. the mean of the prior ones."""
        if len(self.income_samples) < 2:
            return None
        *prior, latest = self.income_samples
        prior_mean = sum(s.amount for s in prior) / len(prior)
        if prior_mean == 0:
            return None
        return round((latest.amount - prior_mean) / prior_mean * 100, 1)
