"""Indexes schemes and CFTI threat reports into OpenSearch.

Run with: python -m app.seed_search
"""

from __future__ import annotations

import asyncio

from app.db.clients import close_all, get_opensearch, get_pg_pool
from app.search.opensearch_index import index_schemes, index_threats


async def seed() -> None:
    client = get_opensearch()
    pg_pool = await get_pg_pool()

    scheme_count = await index_schemes(client)
    threat_count = await index_threats(client, pg_pool)
    print(f"indexed {scheme_count} schemes and {threat_count} threat reports into OpenSearch")

    await close_all()


if __name__ == "__main__":
    asyncio.run(seed())
