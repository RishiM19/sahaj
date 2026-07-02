"""Progressive Trust Protocol - see docs/PTP.md for the full spec.

This is a hard gate: an agent that needs Level 2 data simply never runs for
a Level 0 or 1 user, no matter what the conversation is about. Nothing here
infers or defaults a user up a level - that's always an explicit action
elsewhere (see channels/chat.py `raise_trust_level`).
"""

from __future__ import annotations

PTP_LEVELS: dict[int, dict] = {
    0: {
        "label": "No sign-up",
        "data_required": [],
        "unlocks": "Regional scam alerts and area threat reports.",
    },
    1: {
        "label": "Phone + name",
        "data_required": ["name"],
        "unlocks": "Personalised scheme eligibility, basic guidance.",
    },
    2: {
        "label": "Income range",
        "data_required": ["income_range"],
        "unlocks": "Cash-flow projections, behavioral nudges, deficit warnings.",
    },
    3: {
        "label": "UPI consent",
        "data_required": ["account_aggregator_consent"],
        "unlocks": "Transaction monitoring, proactive distress detection.",
    },
    4: {
        "label": "DigiLocker",
        "data_required": ["digilocker_link"],
        "unlocks": "Full scheme enrollment, credit-building, life simulations.",
    },
}


def agent_allowed(agent_min_level: int, user_trust_level: int) -> bool:
    return user_trust_level >= agent_min_level


def max_response_depth(user_trust_level: int) -> str:
    """How much detail the Orchestrator is allowed to put in the composed reply."""
    if user_trust_level == 0:
        return "alert_only"
    if user_trust_level == 1:
        return "guidance"
    if user_trust_level == 2:
        return "projection"
    return "full"
