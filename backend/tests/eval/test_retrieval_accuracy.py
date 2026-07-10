"""Retrieval-accuracy evaluation: Hit Rate@k and MRR over a golden query set.

Runs against the real fastembed model + a brute-force match_messages fake, so it
loads the model and is slower than the unit suite — run it separately:

    pytest tests/eval -v -s

Scope: a ~6-query smoke-level signal on a tiny seeded corpus, NOT a rigorous
benchmark. It guards against gross retrieval regressions (wrong metric, broken
embedding, mis-wired RPC params), not fine-grained ranking quality.
"""

import json
from pathlib import Path

import app.rag.retriever as retriever
from tests.eval.fixtures import USER_ID, build_match_messages_supabase

K = 3
# Floors are set below the observed scores (see the printed report) to catch
# regressions without being flaky on the tiny corpus.
HIT_RATE_FLOOR = 0.80
MRR_FLOOR = 0.70


def _load_dataset():
    path = Path(__file__).parent / "eval_dataset.json"
    return json.loads(path.read_text())


def test_retrieval_hit_rate_and_mrr(monkeypatch, capsys):
    dataset = _load_dataset()
    monkeypatch.setattr(retriever, "supabase", build_match_messages_supabase())

    hits = 0
    reciprocal_ranks = []
    rows = []

    for case in dataset:
        expected = set(case["expected_message_ids"])
        results = retriever.retrieve_relevant_messages(USER_ID, case["query"], k=K)
        retrieved_ids = [r["message_id"] for r in results]

        rank = next((i + 1 for i, mid in enumerate(retrieved_ids) if mid in expected), None)
        if rank is not None:
            hits += 1
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)

        rows.append((case["query"], retrieved_ids, rank))

    hit_rate = hits / len(dataset)
    mrr = sum(reciprocal_ranks) / len(dataset)

    with capsys.disabled():
        print(f"\n=== Retrieval accuracy (k={K}, n={len(dataset)}) ===")
        for query, retrieved_ids, rank in rows:
            status = f"rank {rank}" if rank else "MISS"
            print(f"  [{status:>7}] top{K}={retrieved_ids}  <- {query!r}")
        print(f"  Hit Rate@{K}: {hit_rate:.3f}   MRR: {mrr:.3f}")

    assert hit_rate >= HIT_RATE_FLOOR, f"Hit Rate@{K} {hit_rate:.3f} below floor {HIT_RATE_FLOOR}"
    assert mrr >= MRR_FLOOR, f"MRR {mrr:.3f} below floor {MRR_FLOOR}"
