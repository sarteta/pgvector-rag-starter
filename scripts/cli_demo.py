"""End-to-end demo: ingest seed doc + run queries."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from app.embeddings import make_provider  # noqa: E402
from app.pipeline import IngestRequest, Pipeline, QueryRequest  # noqa: E402
from app.store import InMemoryStore  # noqa: E402

SEED = ROOT / "seed-data" / "clinica-san-pablo.json"


def main() -> None:
    print("pgvector-rag-starter -- local end-to-end demo")
    print("=" * 60)
    print("provider: deterministic (hash-based, CI-safe, NOT semantic)")
    print("note: use EMBEDDING_PROVIDER=openai + OPENAI_API_KEY for")
    print("      real semantic retrieval. This demo verifies the")
    print("      INFRASTRUCTURE (chunking, tenant isolation, pipeline")
    print("      wiring). The retrieval *quality* is intentionally dumb.")
    print()

    pipeline = Pipeline(embedder=make_provider("deterministic"), store=InMemoryStore())

    data = json.loads(SEED.read_text(encoding="utf-8"))
    tenant = data["tenant_id"]
    for doc in data["documents"]:
        r = pipeline.ingest(
            IngestRequest(
                doc_id=doc["doc_id"],
                tenant_id=tenant,
                title=doc["title"],
                body=doc["body"],
            )
        )
        print(f"[ingest] {r.doc_id}  -> {r.chunks_written} chunks")
    print()

    queries = [
        "a que hora abren",
        "quiero cancelar mi turno",
        "aceptan OSDE?",
        "hacen ecografias?",
        "atienden psicologos",
    ]
    for q in queries:
        result = pipeline.query(QueryRequest(query=q, tenant_id=tenant, limit=2))
        print(f"[query] {q!r}")
        for h in result.hits:
            print(f"  -> [{h.score:.3f}] {h.chunk.title}")
        print()

    # Tenant isolation check
    isolated = pipeline.query(QueryRequest(query="a que hora abren", tenant_id="OTHER-TENANT", limit=5))
    print(f"[isolation] query against 'OTHER-TENANT' -> {len(isolated.hits)} hits (expected 0)")


if __name__ == "__main__":
    main()
