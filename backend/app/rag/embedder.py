"""Local embedding model for RAG.

Uses fastembed (ONNX Runtime, no torch) to serve
sentence-transformers/all-MiniLM-L6-v2 (384-dim) in-process. Chosen so retrieval
needs no paid embedding API (the app is already BYOK-Groq-only) and stays
deterministic/offline for tests. The model is a lazily-created module singleton —
first construction downloads (~90MB) + initializes ONNX, so it is warmed at app
startup rather than on a user request (see app_factory)."""

import os
from functools import lru_cache

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


def embeddings_enabled() -> bool:
    """Whether inline embedding (retrieval + embed-on-insert) should run in this
    process. Off whenever warmup is skipped — i.e. the test suite — so the
    offline test run never loads the model. Prod leaves RAG_SKIP_WARMUP unset."""
    return os.getenv("RAG_SKIP_WARMUP", "").strip().lower() not in {"1", "true", "yes"}


@lru_cache(maxsize=1)
def get_embedder():
    # Imported lazily so importing this module (e.g. in tests that monkeypatch
    # embed_text) doesn't pull in fastembed / trigger a model download.
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=EMBEDDING_MODEL)


def embed_text(text: str) -> list[float]:
    """Embed a single string into a 384-dim vector (plain list of floats, ready
    to hand to Supabase as a pgvector literal)."""
    embedding = next(iter(get_embedder().embed([text or ""])))
    return embedding.tolist()


def warm_embedder() -> None:
    """Force model construction ahead of first request (called at startup)."""
    get_embedder()
