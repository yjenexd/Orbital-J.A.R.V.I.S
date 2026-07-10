import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.briefing import router as briefing_router
from app.routes.chat import router as chat_router
from app.routes.core import router as core_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Warm the local embedding model once at startup so the first /chat request
    # doesn't pay the model download + ONNX init cost. Gated by an env var so the
    # test suite (which spins up TestClient) never triggers a model download, and
    # made non-fatal so a cold/offline start still serves (retrieval fails open).
    if os.getenv("RAG_SKIP_WARMUP", "").strip().lower() not in {"1", "true", "yes"}:
        try:
            from app.rag.embedder import warm_embedder

            warm_embedder()
            print("[RAG] Embedding model warmed.")
        except Exception as e:
            print(f"[RAG] Embedder warmup skipped ({e}); retrieval will fail open.")
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(core_router)
app.include_router(chat_router)
app.include_router(briefing_router)
