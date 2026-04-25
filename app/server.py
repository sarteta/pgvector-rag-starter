"""FastAPI server -- HTTP interface over the pipeline."""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .embeddings import make_provider
from .pipeline import IngestRequest, Pipeline, QueryRequest
from .store import InMemoryStore


class IngestBody(BaseModel):
    doc_id: str
    tenant_id: str
    title: str
    body: str
    metadata: dict[str, Any] | None = None


class QueryBody(BaseModel):
    query: str
    tenant_id: str
    limit: int = 5


class HitOut(BaseModel):
    id: str
    doc_id: str
    title: str
    snippet: str
    score: float


def build_app() -> FastAPI:
    pipeline = Pipeline(embedder=make_provider(), store=InMemoryStore())
    app = FastAPI(title="pgvector-rag-starter", version="0.1.0")

    @app.get("/health")
    def health() -> dict:
        return {"ok": True, "chunks": pipeline.store.count()}

    @app.post("/ingest")
    def ingest(body: IngestBody) -> dict:
        if not body.body.strip():
            raise HTTPException(400, "empty body")
        result = pipeline.ingest(
            IngestRequest(
                doc_id=body.doc_id,
                tenant_id=body.tenant_id,
                title=body.title,
                body=body.body,
                metadata=body.metadata,
            )
        )
        return {"doc_id": result.doc_id, "chunks_written": result.chunks_written}

    @app.post("/query")
    def query(body: QueryBody) -> dict:
        if not body.query.strip():
            raise HTTPException(400, "empty query")
        result = pipeline.query(QueryRequest(**body.model_dump()))
        return {
            "hits": [
                HitOut(
                    id=h.chunk.id,
                    doc_id=h.chunk.doc_id,
                    title=h.chunk.title,
                    snippet=h.chunk.body[:240],
                    score=round(h.score, 4),
                ).model_dump()
                for h in result.hits
            ]
        }

    return app


app = build_app()
