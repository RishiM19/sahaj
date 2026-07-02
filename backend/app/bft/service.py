"""The Behavioral Financial Twin - a live Neo4j graph per user.

Graph shape:

    (:User {phone, name, language, trustLevel, createdAt})
        -[:HAS_STATE_EVENT]->(:BehavioralStateEvent {value, score, factors, at})
        -[:HAS_INCOME_SAMPLE]->(:IncomeSample {amount, source, at})
        -[:HAS_EXPENSE]->(:FixedExpense {label, amount, dueDay})
        -[:MADE_QUERY]->(:Query {type, channel, resolved, at})

The "current" behavioral state is just the most recent BehavioralStateEvent -
we keep every past state as its own node instead of overwriting a property,
because the whole point of the Twin is that state is recomputed every
interaction and the trajectory matters, not just the latest value.
"""

from __future__ import annotations

from datetime import UTC, datetime

from neo4j import AsyncDriver

from app.bft.models import BFTSnapshot, BehavioralState, IncomeSample


class BFTService:
    def __init__(self, driver: AsyncDriver) -> None:
        self._driver = driver

    async def wipe_all(self) -> None:
        """Dev-only: clears the whole graph. Used by app/seed.py so reseeding
        is idempotent instead of piling up duplicate income/state history."""
        async with self._driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")

    async def ensure_schema(self) -> None:
        async with self._driver.session() as session:
            await session.run(
                "CREATE CONSTRAINT user_phone IF NOT EXISTS "
                "FOR (u:User) REQUIRE u.phone IS UNIQUE"
            )

    async def get_or_create_user(
        self, phone: str, name: str | None = None, language: str = "en"
    ) -> BFTSnapshot:
        async with self._driver.session() as session:
            await session.run(
                """
                MERGE (u:User {phone: $phone})
                ON CREATE SET u.name = $name, u.language = $language,
                              u.trustLevel = 0, u.createdAt = $now
                """,
                phone=phone,
                name=name,
                language=language,
                now=datetime.now(UTC).isoformat(),
            )
        return await self.get_snapshot(phone)

    async def get_snapshot(self, phone: str) -> BFTSnapshot:
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (u:User {phone: $phone})
                OPTIONAL MATCH (u)-[:HAS_STATE_EVENT]->(s:BehavioralStateEvent)
                WITH u, s ORDER BY s.at DESC
                WITH u, collect(s)[0] AS latestState
                OPTIONAL MATCH (u)-[:HAS_INCOME_SAMPLE]->(i:IncomeSample)
                WITH u, latestState, i ORDER BY i.at ASC
                WITH u, latestState, collect(i)[-6..] AS incomeSamples
                OPTIONAL MATCH (u)-[:HAS_EXPENSE]->(e:FixedExpense)
                RETURN u, latestState, incomeSamples, collect(e) AS expenses
                """,
                phone=phone,
            )
            record = await result.single()

        if record is None or record["u"] is None:
            raise ValueError(f"no user with phone {phone!r} - call get_or_create_user first")

        user = record["u"]
        latest_state = record["latestState"]
        income_samples = [
            IncomeSample(amount=i["amount"], source=i["source"], timestamp=i["at"])
            for i in record["incomeSamples"]
        ]
        expenses = [
            {"label": e["label"], "amount": e["amount"], "due_day": e["dueDay"]}
            for e in record["expenses"]
        ]

        score = latest_state["score"] if latest_state else 0.0
        return BFTSnapshot(
            phone=user["phone"],
            name=user.get("name"),
            language=user.get("language", "en"),
            trust_level=user.get("trustLevel", 0),
            behavioral_state=BehavioralState.from_score(score),
            state_score=score,
            income_samples=income_samples,
            fixed_expenses=expenses,
            current_balance=user.get("currentBalance"),
            income_verified=user.get("incomeVerified", False),
            digilocker_linked=user.get("digilockerLinked", False),
            income_source=user.get("incomeSource", "gig"),
        )

    async def set_income_source(self, phone: str, source: str) -> None:
        async with self._driver.session() as session:
            await session.run(
                "MATCH (u:User {phone: $phone}) SET u.incomeSource = $source",
                phone=phone,
                source=source,
            )

    async def set_balance(self, phone: str, balance: float) -> None:
        async with self._driver.session() as session:
            await session.run(
                "MATCH (u:User {phone: $phone}) SET u.currentBalance = $balance",
                phone=phone,
                balance=balance,
            )

    async def set_income_verified(self, phone: str, verified: bool = True) -> None:
        async with self._driver.session() as session:
            await session.run(
                "MATCH (u:User {phone: $phone}) SET u.incomeVerified = $verified",
                phone=phone,
                verified=verified,
            )

    async def set_digilocker_linked(self, phone: str, linked: bool = True) -> None:
        async with self._driver.session() as session:
            await session.run(
                "MATCH (u:User {phone: $phone}) SET u.digilockerLinked = $linked",
                phone=phone,
                linked=linked,
            )

    async def record_income_sample(
        self, phone: str, amount: float, source: str, at: str | None = None
    ) -> None:
        async with self._driver.session() as session:
            await session.run(
                """
                MATCH (u:User {phone: $phone})
                CREATE (u)-[:HAS_INCOME_SAMPLE]->(:IncomeSample {
                    amount: $amount, source: $source, at: $at
                })
                """,
                phone=phone,
                amount=amount,
                source=source,
                at=at or datetime.now(UTC).isoformat(),
            )

    async def record_expense(self, phone: str, label: str, amount: float, due_day: int) -> None:
        async with self._driver.session() as session:
            await session.run(
                """
                MATCH (u:User {phone: $phone})
                MERGE (u)-[:HAS_EXPENSE]->(e:FixedExpense {label: $label})
                SET e.amount = $amount, e.dueDay = $due_day
                """,
                phone=phone,
                label=label,
                amount=amount,
                due_day=due_day,
            )

    async def update_behavioral_state(
        self, phone: str, score: float, factors: list[str]
    ) -> BehavioralState:
        state = BehavioralState.from_score(score)
        async with self._driver.session() as session:
            await session.run(
                """
                MATCH (u:User {phone: $phone})
                CREATE (u)-[:HAS_STATE_EVENT]->(:BehavioralStateEvent {
                    value: $value, score: $score, factors: $factors, at: $now
                })
                """,
                phone=phone,
                value=state.name,
                score=score,
                factors=factors,
                now=datetime.now(UTC).isoformat(),
            )
        return state

    async def set_trust_level(self, phone: str, level: int) -> None:
        async with self._driver.session() as session:
            await session.run(
                "MATCH (u:User {phone: $phone}) SET u.trustLevel = $level",
                phone=phone,
                level=level,
            )

    async def log_query(self, phone: str, channel: str, query_type: str) -> None:
        async with self._driver.session() as session:
            await session.run(
                """
                MATCH (u:User {phone: $phone})
                CREATE (u)-[:MADE_QUERY]->(:Query {
                    type: $query_type, channel: $channel, resolved: true, at: $now
                })
                """,
                phone=phone,
                channel=channel,
                query_type=query_type,
                now=datetime.now(UTC).isoformat(),
            )
