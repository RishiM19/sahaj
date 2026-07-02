"""Lazily-created, process-wide handles to every backing store.

Everything here is a thin wrapper so the rest of the app never imports a
driver directly - if we ever swap Postgres for Cassandra (see
docs/ARCHITECTURE.md) only this file and app/db/cfti.py change.
"""

from __future__ import annotations

import asyncpg
import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from neo4j import AsyncDriver, AsyncGraphDatabase
from opensearchpy import AsyncOpenSearch
from qdrant_client import AsyncQdrantClient

from app.config import get_settings

_neo4j_driver: AsyncDriver | None = None
_mongo_client: AsyncIOMotorClient | None = None
_redis_client: redis.Redis | None = None
_qdrant_client: AsyncQdrantClient | None = None
_opensearch_client: AsyncOpenSearch | None = None
_pg_pool: asyncpg.Pool | None = None


def get_neo4j() -> AsyncDriver:
    global _neo4j_driver
    if _neo4j_driver is None:
        settings = get_settings()
        _neo4j_driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )
    return _neo4j_driver


def get_mongo_db() -> AsyncIOMotorDatabase:
    global _mongo_client
    settings = get_settings()
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(settings.mongo_uri)
    return _mongo_client[settings.mongo_db]


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(get_settings().redis_url, decode_responses=True)
    return _redis_client


def get_qdrant() -> AsyncQdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = AsyncQdrantClient(url=get_settings().qdrant_url)
    return _qdrant_client


def get_opensearch() -> AsyncOpenSearch:
    global _opensearch_client
    if _opensearch_client is None:
        _opensearch_client = AsyncOpenSearch(hosts=[get_settings().opensearch_url], use_ssl=False)
    return _opensearch_client


async def get_pg_pool() -> asyncpg.Pool:
    global _pg_pool
    if _pg_pool is None:
        _pg_pool = await asyncpg.create_pool(get_settings().postgres_dsn)
    return _pg_pool


async def close_all() -> None:
    if _neo4j_driver is not None:
        await _neo4j_driver.close()
    if _mongo_client is not None:
        _mongo_client.close()
    if _redis_client is not None:
        await _redis_client.aclose()
    if _pg_pool is not None:
        await _pg_pool.close()
    if _opensearch_client is not None:
        await _opensearch_client.close()
