"""Embedding providers.

Ships with two implementations:

* `DeterministicEmbedding` — hash-based pseudo-embedding. Produces a
  stable 384-dim vector per input. **NOT semantically meaningful.**
  It exists so the full pipeline (ingest -> store -> search -> serve)
  runs in CI without an OpenAI/Anthropic/Voyage account. Same-input
  vectors are equal, so exact lookup works. That's all.

* `OpenAIEmbedding` — real embeddings via `text-embedding-3-small`.
  Turn it on with `EMBEDDING_PROVIDER=openai` + `OPENAI_API_KEY` in
  `.env`. Returns 1536-dim vectors.

The `EmbeddingProvider` protocol is intentionally tiny. Swap in Voyage,
Cohere, or a local e5-small-v2 by implementing `embed()`.
"""
from __future__ import annotations

import hashlib
import os
from typing import Protocol


class EmbeddingProvider(Protocol):
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class DeterministicEmbedding:
    """Pseudo-embedding for CI and offline dev. Not semantic — just stable."""

    dim = 384

    def embed(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            # Tile the 32-byte digest into a 384-dim float vector in [-1, 1]
            vec = []
            for i in range(self.dim):
                b = digest[i % len(digest)]
                vec.append((b - 128) / 128.0)
            # L2 normalize so cosine similarity stays well-behaved
            norm = sum(x * x for x in vec) ** 0.5 or 1.0
            out.append([x / norm for x in vec])
        return out


class OpenAIEmbedding:
    """Real embeddings via OpenAI's text-embedding-3-small."""

    dim = 1536

    def __init__(self, api_key: str | None = None, model: str = "text-embedding-3-small"):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "openai package not installed. `pip install openai` or use "
                "EMBEDDING_PROVIDER=deterministic for the demo."
            ) from exc
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        resp = self.client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in resp.data]


def make_provider(name: str | None = None) -> EmbeddingProvider:
    name = (name or os.environ.get("EMBEDDING_PROVIDER") or "deterministic").lower()
    if name == "openai":
        return OpenAIEmbedding()
    if name == "deterministic":
        return DeterministicEmbedding()
    raise ValueError(f"unknown embedding provider: {name}")
