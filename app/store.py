"""Vector stores.

Two implementations share a Protocol:

* `InMemoryStore` -- list of chunks + cosine search. CI-friendly.
* `PgvectorStore` -- Postgres + pgvector extension. Real production target.

The pgvector impl expects a table like:

    CREATE EXTENSION IF NOT EXISTS vector;

    CREATE TABLE chunks (
      id          TEXT PRIMARY KEY,
      tenant_id   TEXT NOT NULL,
      doc_id      TEXT NOT NULL,
      title       TEXT,
      body        TEXT NOT NULL,
      embedding   vector(1536) NOT NULL,
      metadata    JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops);
    CREATE INDEX ON chunks (tenant_id);

See `docs/pgvector-schema.sql` for the full DDL + RLS policy template.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class Chunk:
    id: str
    tenant_id: str
    doc_id: str
    title: str
    body: str
    embedding: list[float]
    metadata: dict = field(default_factory=dict)


@dataclass
class SearchHit:
    chunk: Chunk
    score: float


class VectorStore(Protocol):
    def upsert(self, chunks: list[Chunk]) -> None: ...
    def search(self, *, embedding: list[float], tenant_id: str, limit: int = 5) -> list[SearchHit]: ...
    def count(self, tenant_id: str | None = None) -> int: ...
    def reset(self) -> None: ...


def cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)


class InMemoryStore:
    """List-backed store. Fine for up to low-thousands of chunks."""

    def __init__(self) -> None:
        self._chunks: dict[str, Chunk] = {}

    def upsert(self, chunks: list[Chunk]) -> None:
        for c in chunks:
            self._chunks[c.id] = c

    def search(self, *, embedding: list[float], tenant_id: str, limit: int = 5) -> list[SearchHit]:
        hits: list[SearchHit] = []
        for c in self._chunks.values():
            if c.tenant_id != tenant_id:
                continue
            score = cosine(embedding, c.embedding)
            hits.append(SearchHit(chunk=c, score=score))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:limit]

    def count(self, tenant_id: str | None = None) -> int:
        if tenant_id is None:
            return len(self._chunks)
        return sum(1 for c in self._chunks.values() if c.tenant_id == tenant_id)

    def reset(self) -> None:
        self._chunks.clear()
