"""Keyword search over schemes and CFTI threat reports - see
app/search/opensearch_index.py. Separate from the chat/USSD turn flow;
this is a direct lookup tool the frontend (or a future agent) can call
when exact/keyword matching is what's needed, not semantic RAG.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.search.opensearch_index import search_schemes, search_threats

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/schemes")
async def search_schemes_endpoint(q: str, request: Request):
    client = request.app.state.opensearch
    return {"results": await search_schemes(client, q)}


@router.get("/threats")
async def search_threats_endpoint(q: str, request: Request):
    client = request.app.state.opensearch
    return {"results": await search_threats(client, q)}
