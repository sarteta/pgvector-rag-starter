from app.embeddings import DeterministicEmbedding
from app.pipeline import IngestRequest, Pipeline, QueryRequest
from app.store import InMemoryStore


def make_pipeline() -> Pipeline:
    return Pipeline(embedder=DeterministicEmbedding(), store=InMemoryStore())


def test_ingest_produces_at_least_one_chunk():
    p = make_pipeline()
    r = p.ingest(
        IngestRequest(
            doc_id="doc1",
            tenant_id="t1",
            title="Horarios",
            body="Atendemos de lunes a viernes de 9 a 18 hs. Sabados de 9 a 13 hs.",
        )
    )
    assert r.chunks_written >= 1


def test_empty_body_produces_zero_chunks():
    p = make_pipeline()
    r = p.ingest(IngestRequest(doc_id="d", tenant_id="t", title="x", body="   "))
    assert r.chunks_written == 0


def test_ingested_doc_is_searchable():
    p = make_pipeline()
    p.ingest(
        IngestRequest(
            doc_id="turnos",
            tenant_id="clinica",
            title="Turnos",
            body="Podes reservar un turno respondiendo este mensaje con tu DNI.",
        )
    )
    result = p.query(
        QueryRequest(
            query="Podes reservar un turno respondiendo este mensaje con tu DNI.",
            tenant_id="clinica",
            limit=3,
        )
    )
    assert len(result.hits) >= 1
    assert result.hits[0].chunk.doc_id == "turnos"


def test_tenant_isolation_blocks_cross_tenant_hits():
    p = make_pipeline()
    p.ingest(IngestRequest(doc_id="d", tenant_id="A", title="t", body="Contenido confidencial de tenant A."))
    result = p.query(QueryRequest(query="Contenido confidencial de tenant A.", tenant_id="B", limit=5))
    assert len(result.hits) == 0


def test_limit_parameter_respected():
    p = make_pipeline()
    for i in range(10):
        p.ingest(
            IngestRequest(
                doc_id=f"doc{i}",
                tenant_id="t",
                title=f"Title {i}",
                body=f"Body number {i} with some filler text that is long enough to count as a real chunk.",
            )
        )
    result = p.query(QueryRequest(query="body", tenant_id="t", limit=3))
    assert len(result.hits) <= 3
