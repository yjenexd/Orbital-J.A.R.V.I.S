import os
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient


# Never download/load the embedding model during the (offline, fast) test suite;
# tests that need retrieval monkeypatch embed_text / the RPC directly.
os.environ.setdefault("RAG_SKIP_WARMUP", "1")

# Keep the LLM-as-a-judge off by default so the offline suite makes no real model
# calls; the dedicated guardrail tests opt in by clearing this env var.
os.environ.setdefault("GUARDRAILS_JUDGE_DISABLED", "1")

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.app_factory import app
from app.clients import get_current_user_id


def pytest_addoption(parser):
    parser.addoption(
        "--run-eval",
        action="store_true",
        default=False,
        help="Run the retrieval-accuracy eval (loads the embedding model; slower).",
    )


def pytest_collection_modifyitems(config, items):
    # Keep the default `pytest tests` run fully offline/fast: the eval suite loads
    # the fastembed model, so it only runs when explicitly opted in.
    if config.getoption("--run-eval"):
        return
    skip_eval = pytest.mark.skip(reason="retrieval eval loads the embedding model; pass --run-eval")
    for item in items:
        if "tests/eval/" in item.nodeid or "tests\\eval\\" in item.nodeid:
            item.add_marker(skip_eval)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()
    app.dependency_overrides[get_current_user_id] = lambda: "test-user-id"
    yield
    app.dependency_overrides.clear()
