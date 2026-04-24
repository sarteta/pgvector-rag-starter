from app.store import Chunk, InMemoryStore, cosine


def test_cosine_identical_vectors_is_one():
    v = [1.0, 0.0, 0.0]
    assert abs(cosine(v, v) - 1.0) < 1e-9


def test_cosine_orthogonal_is_zero():
    assert abs(cosine([1.0, 0.0], [0.0, 1.0])) < 1e-9


def test_inmemory_store_upsert_and_search_filters_by_tenant():
    store = InMemoryStore()
    store.upsert([
        Chunk(id="1", tenant_id="A", doc_id="d", title="t", body="x", embedding=[1.0, 0.0]),
        Chunk(id="2", tenant_id="B", doc_id="d", title="t", body="x", embedding=[1.0, 0.0]),
    ])
    hits = store.search(embedding=[1.0, 0.0], tenant_id="A", limit=5)
    assert len(hits) == 1
    assert hits[0].chunk.tenant_id == "A"


def test_inmemory_store_count():
    store = InMemoryStore()
    store.upsert([
        Chunk(id="1", tenant_id="A", doc_id="d", title="t", body="x", embedding=[1.0, 0.0]),
        Chunk(id="2", tenant_id="A", doc_id="d", title="t", body="x", embedding=[1.0, 0.0]),
        Chunk(id="3", tenant_id="B", doc_id="d", title="t", body="x", embedding=[1.0, 0.0]),
    ])
    assert store.count() == 3
    assert store.count("A") == 2
    assert store.count("B") == 1


def test_reset_clears_all():
    store = InMemoryStore()
    store.upsert([Chunk(id="1", tenant_id="A", doc_id="d", title="t", body="x", embedding=[1.0, 0.0])])
    store.reset()
    assert store.count() == 0
