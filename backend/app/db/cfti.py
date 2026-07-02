"""Community Financial Threat Intelligence store.

docs/ARCHITECTURE.md explains why this is Postgres instead of Cassandra for
now - the access pattern (insert a report, count reports for an entity in an
area) is written behind these functions so the storage engine can change
without touching Scam Guard or Community Intelligence.
"""

from __future__ import annotations

from datetime import UTC, datetime

import asyncpg


async def ensure_schema(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cfti_reports (
                id SERIAL PRIMARY KEY,
                entity_name TEXT NOT NULL,
                entity_type TEXT NOT NULL DEFAULT 'lender',
                area TEXT,
                threat_type TEXT NOT NULL DEFAULT 'unregistered_lender',
                reported_at TIMESTAMPTZ NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_cfti_entity
                ON cfti_reports (lower(entity_name), area);
            """
        )


async def report_threat(
    pool: asyncpg.Pool,
    entity_name: str,
    area: str | None,
    threat_type: str = "unregistered_lender",
) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO cfti_reports (entity_name, area, threat_type, reported_at)
            VALUES ($1, $2, $3, $4)
            """,
            entity_name,
            area,
            threat_type,
            datetime.now(UTC),
        )


async def count_reports(pool: asyncpg.Pool, entity_name: str, area: str | None) -> int:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT count(*) AS n FROM cfti_reports
            WHERE lower(entity_name) = lower($1)
              AND ($2::text IS NULL OR area = $2)
            """,
            entity_name,
            area,
        )
        return row["n"] if row else 0
