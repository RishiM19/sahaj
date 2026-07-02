"""Scheme RAG - embeds the seed set in app/data/schemes.json with
sentence-transformers and indexes it into Qdrant, so the Scheme Navigator
agent retrieves against real government schemes instead of nothing. See
docs/ROADMAP.md - growing this seed set toward 400+ schemes is tracked
separately from the indexing mechanics here, which don't need to change.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from qdrant_client import AsyncQdrantClient, models
from sentence_transformers import SentenceTransformer

from app.config import get_settings

_SCHEMES_PATH = Path(__file__).resolve().parent.parent / "data" / "schemes.json"
_COLLECTION = "schemes"
_EMBED_MODEL = "all-MiniLM-L6-v2"  # matches the exec-summary spec, 384-dim, CPU-friendly


def _load_schemes() -> list[dict]:
    return json.loads(_SCHEMES_PATH.read_text())["schemes"]


def _scheme_text(scheme: dict) -> str:
    return (
        f"{scheme['name']} ({scheme['category']}). "
        f"Benefit: {scheme['benefit']} "
        f"Eligibility: {scheme['eligibility']} "
        f"{scheme['description']}"
    )


class SchemeIndex:
    def __init__(self, qdrant: AsyncQdrantClient) -> None:
        self._qdrant = qdrant
        self._model: SentenceTransformer | None = None

    def _get_model(self) -> SentenceTransformer:
        # loaded lazily and lazily-once - sentence-transformers pulls in torch,
        # no need to pay that startup cost for requests that never search
        if self._model is None:
            self._model = SentenceTransformer(_EMBED_MODEL)
        return self._model

    async def _embed(self, texts: list[str]) -> list[list[float]]:
        model = self._get_model()
        vectors = await asyncio.to_thread(model.encode, texts, normalize_embeddings=True)
        return vectors.tolist()

    async def ensure_collection(self) -> None:
        exists = await self._qdrant.collection_exists(_COLLECTION)
        if not exists:
            dim = self._get_model().get_embedding_dimension()
            await self._qdrant.create_collection(
                collection_name=_COLLECTION,
                vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
            )

    async def index_all(self) -> int:
        await self.ensure_collection()
        schemes = _load_schemes()
        vectors = await self._embed([_scheme_text(s) for s in schemes])
        points = [
            models.PointStruct(id=i, vector=vec, payload=scheme)
            for i, (vec, scheme) in enumerate(zip(vectors, schemes))
        ]
        await self._qdrant.upsert(collection_name=_COLLECTION, points=points)
        return len(points)

    async def search(self, query: str, top_k: int = 3) -> list[dict]:
        [query_vector] = await self._embed([query])
        hits = await self._qdrant.query_points(
            collection_name=_COLLECTION, query=query_vector, limit=top_k
        )
        return [{"score": round(h.score, 3), **h.payload} for h in hits.points]
