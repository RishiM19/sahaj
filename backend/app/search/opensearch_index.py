"""OpenSearch full-text search - complements Qdrant's semantic search in
app/rag/schemes.py for cases where exact/keyword matching beats "meaning"
matching: an exact scheme acronym (KCC, PMFBY), or looking up a CFTI threat
report by the precise lender name someone typed. See docs/ARCHITECTURE.md
for why OpenSearch over Elasticsearch.
"""

from __future__ import annotations

import asyncpg
from opensearchpy import AsyncOpenSearch

from app.rag.schemes import load_schemes

SCHEME_INDEX = "schemes"
THREAT_INDEX = "cfti_threats"

_TEXT_MAPPING = {"mappings": {"properties": {}}}  # let OpenSearch dynamic-map text fields


async def ensure_indices(client: AsyncOpenSearch) -> None:
    for index in (SCHEME_INDEX, THREAT_INDEX):
        if not await client.indices.exists(index=index):
            await client.indices.create(index=index, body=_TEXT_MAPPING)


async def index_schemes(client: AsyncOpenSearch) -> int:
    await ensure_indices(client)
    schemes = load_schemes()
    for scheme in schemes:
        await client.index(index=SCHEME_INDEX, id=scheme["id"], body=scheme, refresh=False)
    await client.indices.refresh(index=SCHEME_INDEX)
    return len(schemes)


async def index_threats(client: AsyncOpenSearch, pg_pool: asyncpg.Pool) -> int:
    await ensure_indices(client)
    async with pg_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, entity_name, entity_type, area, threat_type, reported_at FROM cfti_reports"
        )
    for row in rows:
        await client.index(
            index=THREAT_INDEX,
            id=row["id"],
            body={
                "entity_name": row["entity_name"],
                "entity_type": row["entity_type"],
                "area": row["area"],
                "threat_type": row["threat_type"],
                "reported_at": row["reported_at"].isoformat(),
            },
            refresh=False,
        )
    if rows:
        await client.indices.refresh(index=THREAT_INDEX)
    return len(rows)


async def search_schemes(client: AsyncOpenSearch, query: str, top_k: int = 5) -> list[dict]:
    result = await client.search(
        index=SCHEME_INDEX,
        body={
            "query": {"multi_match": {"query": query, "fields": ["name^3", "category", "benefit", "eligibility", "description"]}},
            "size": top_k,
        },
    )
    return [{"score": hit["_score"], **hit["_source"]} for hit in result["hits"]["hits"]]


async def search_threats(client: AsyncOpenSearch, query: str, top_k: int = 5) -> list[dict]:
    result = await client.search(
        index=THREAT_INDEX,
        body={
            "query": {"multi_match": {"query": query, "fields": ["entity_name^3", "area", "threat_type"]}},
            "size": top_k,
        },
    )
    return [{"score": hit["_score"], **hit["_source"]} for hit in result["hits"]["hits"]]
