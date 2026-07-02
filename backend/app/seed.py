"""Seeds the four personas from the pitch deck into the Behavioral Financial
Twin so the golden-path demo (docs/ARCHITECTURE.md) works the moment the
stack comes up, instead of needing weeks of real usage first.

Run with: python -m app.seed
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from app.bft.service import BFTService
from app.db.clients import close_all, get_neo4j

PERSONAS = [
    {
        "phone": "+919820011111",
        "name": "Rajesh",
        "language": "hi",
        "trust_level": 3,
        # declining weekly gig income - "down 3 weeks in a row", trending
        # toward the deck's "slowest earning week" figure, and a balance
        # that's already been drawn down by the same slow stretch
        "income_samples": [7_100, 6_300, 4_800, 2_600],
        "current_balance": 4_200,
        "fixed_expenses": [{"label": "Rent", "amount": 7_000, "due_day": 1}],
    },
    {
        "phone": "+919820022222",
        "name": "Priya",
        "language": "en",
        "trust_level": 2,
        "income_samples": [44_000, 44_000, 44_000, 44_000],  # stable teacher salary
        "current_balance": 38_000,
        "fixed_expenses": [{"label": "Rent", "amount": 15_000, "due_day": 5}],
    },
    {
        "phone": "+919820033333",
        "name": "Kisan",
        "language": "kn",
        "trust_level": 1,  # low trust - form is in English, branch is 14km away
        "income_samples": [6_000, 0, 0, 42_000],  # seasonal paddy income
        "current_balance": 4_200,
        "fixed_expenses": [{"label": "Seed & fertiliser", "amount": 3_500, "due_day": 10}],
    },
    {
        "phone": "+919820044444",
        "name": "Divya",
        "language": "en",
        "trust_level": 2,
        "income_samples": [28_000, 29_500, 27_000, 30_000],  # freelance writing
        "current_balance": 21_000,
        "fixed_expenses": [{"label": "Rent", "amount": 12_000, "due_day": 3}],
    },
]


async def seed() -> None:
    bft = BFTService(get_neo4j())
    await bft.wipe_all()
    await bft.ensure_schema()

    for persona in PERSONAS:
        phone = persona["phone"]
        await bft.get_or_create_user(phone, name=persona["name"], language=persona["language"])
        await bft.set_trust_level(phone, persona["trust_level"])
        await bft.set_balance(phone, persona["current_balance"])
        await bft.update_behavioral_state(phone, score=0, factors=["seed"])

        base = datetime.now(UTC) - timedelta(weeks=len(persona["income_samples"]))
        for i, amount in enumerate(persona["income_samples"]):
            at = (base + timedelta(weeks=i)).isoformat()
            await bft.record_income_sample(phone, amount, source="seed", at=at)

        for exp in persona["fixed_expenses"]:
            await bft.record_expense(phone, exp["label"], exp["amount"], exp["due_day"])

        print(f"seeded {persona['name']} ({phone}) - trust level {persona['trust_level']}")

    await close_all()


if __name__ == "__main__":
    asyncio.run(seed())
