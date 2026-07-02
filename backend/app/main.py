from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.channels import chat, document, search, ussd, voice
from app.db import cfti
from app.db.clients import close_all, get_neo4j, get_opensearch, get_pg_pool, get_qdrant
from app.orchestrator.graph import Orchestrator
from app.search.opensearch_index import ensure_indices


@asynccontextmanager
async def lifespan(app: FastAPI):
    neo4j_driver = get_neo4j()
    pg_pool = await get_pg_pool()
    await cfti.ensure_schema(pg_pool)

    orchestrator = Orchestrator(neo4j_driver, pg_pool, get_qdrant())
    await orchestrator.bft.ensure_schema()
    app.state.orchestrator = orchestrator

    app.state.opensearch = get_opensearch()
    await ensure_indices(app.state.opensearch)

    yield

    await close_all()


app = FastAPI(title="SAHAJ", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(ussd.router)
app.include_router(search.router)
app.include_router(voice.router)
app.include_router(document.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
