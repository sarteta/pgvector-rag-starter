-- pgvector schema + RLS skeleton for multi-tenant RAG.
-- Apply with psql: \i docs/pgvector-schema.sql

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
  id          TEXT PRIMARY KEY,
  tenant_id   TEXT NOT NULL,
  doc_id      TEXT NOT NULL,
  title       TEXT,
  body        TEXT NOT NULL,
  embedding   vector(1536) NOT NULL,      -- adjust dim to match your provider
  metadata    JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- HNSW index for cosine similarity search.
CREATE INDEX IF NOT EXISTS chunks_embedding_idx
  ON chunks USING hnsw (embedding vector_cosine_ops);

-- Secondary index on tenant filter -- search path is always tenant-first.
CREATE INDEX IF NOT EXISTS chunks_tenant_idx ON chunks (tenant_id);

-- Row-Level Security.
-- 1. Enable RLS on the table.
-- 2. Every query must set `app.tenant_id` via SET LOCAL before SELECT.
-- 3. The policy restricts visibility to rows matching that tenant.
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS chunks_tenant_isolation ON chunks
  USING (tenant_id = current_setting('app.tenant_id', true));

-- Example usage from Python (psycopg):
--
--   with conn.cursor() as cur:
--       cur.execute("SET LOCAL app.tenant_id = %s", (tenant_id,))
--       cur.execute(
--           "SELECT id, title, body, 1 - (embedding <=> %s::vector) AS score "
--           "FROM chunks ORDER BY embedding <=> %s::vector LIMIT %s",
--           (query_vec, query_vec, limit),
--       )
--
-- The `SET LOCAL` is committed for the duration of the transaction and
-- reset at commit/rollback. Never construct the SQL by string-formatting
-- the tenant id -- use SET LOCAL with a parameter.
