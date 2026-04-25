"""High-level RAG pipeline -- ingest + query."""
from __future__ import annotations

from dataclasses import dataclass

from .chunking import chunk_text
from .embeddings import EmbeddingProvider
from .store import Chunk, SearchHit, VectorStore


@dataclass
class IngestRequest:
    doc_id: str
    tenant_id: str
    title: str
    body: str
    metadata: dict | None = None


@dataclass
class IngestResult:
    doc_id: str
    chunks_written: int


@dataclass
class QueryRequest:
    query: str
    tenant_id: str
    limit: int = 5


@dataclass
class QueryResult:
    hits: list[SearchHit]


class Pipeline:
    def __init__(self, *, embedder: EmbeddingProvider, store: VectorStore) -> None:
        self.embedder = embedder
        self.store = store

    def ingest(self, req: IngestRequest) -> IngestResult:
        pieces = chunk_text(req.body)
        if not pieces:
            return IngestResult(doc_id=req.doc_id, chunks_written=0)
        vectors = self.embedder.embed([p.text for p in pieces])
        chunks: list[Chunk] = []
        for i, (piece, vec) in enumerate(zip(pieces, vectors)):
            chunks.append(
                Chunk(
                    id=f"{req.doc_id}::chunk_{i:04d}",
                    tenant_id=req.tenant_id,
                    doc_id=req.doc_id,
                    title=req.title,
                    body=piece.text,
                    embedding=vec,
                    metadata=req.metadata or {},
                )
            )
        self.store.upsert(chunks)
        return IngestResult(doc_id=req.doc_id, chunks_written=len(chunks))

    def query(self, req: QueryRequest) -> QueryResult:
        [qvec] = self.embedder.embed([req.query])
        hits = self.store.search(embedding=qvec, tenant_id=req.tenant_id, limit=req.limit)
        return QueryResult(hits=hits)
