"""Indexes app/data/schemes.json into Qdrant for the Scheme Navigator agent.

Separate from app/seed.py (which only touches Neo4j/Postgres) because this
one pulls in sentence-transformers/torch - no reason to pay that import cost
for a plain persona reseed.

Run with: python -m app.seed_schemes
"""

from __future__ import annotations

import asyncio

from app.db.clients import close_all, get_qdrant
from app.rag.schemes import SchemeIndex


async def seed() -> None:
    index = SchemeIndex(get_qdrant())
    count = await index.index_all()
    print(f"indexed {count} schemes into Qdrant")
    await close_all()


if __name__ == "__main__":
    asyncio.run(seed())
