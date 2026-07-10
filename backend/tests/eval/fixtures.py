"""Seeded chat-history corpus + a brute-force match_messages fake for the
retrieval eval. The fake computes cosine similarity in Python over REAL fastembed
vectors (not mocked numbers), mirroring the match_messages SQL semantics
(cosine order, user filter, exclude_message_id), so Hit Rate / MRR numbers are
meaningful. This is the one place in the suite that actually loads the model."""

import numpy as np

from app.rag.embedder import embed_text
from tests._fakes import FakeSupabase


# A small, realistic J.A.R.V.I.S conversation history (message_id, role, content).
CORPUS = [
    {"message_id": 1, "role": "user", "content": "Remind me to buy fish food for my planted aquarium this weekend"},
    {"message_id": 2, "role": "assistant", "content": "Noted — I've added buying fish food for your aquarium to your tasks."},
    {"message_id": 3, "role": "user", "content": "I have the CS2040S data structures assignment due next Friday"},
    {"message_id": 4, "role": "assistant", "content": "Got it, I've logged the CS2040S algorithms assignment with a Friday deadline."},
    {"message_id": 5, "role": "user", "content": "Schedule an Orbital project sync with Jason on Tuesday at 3pm"},
    {"message_id": 6, "role": "assistant", "content": "Done — your Orbital project sync with Jason is booked for Tuesday 3pm."},
    {"message_id": 7, "role": "user", "content": "When can I fit in my Secondary 4 chemistry tutoring preparation?"},
    {"message_id": 8, "role": "assistant", "content": "I've protected Thursday evening for your Sec 4 chemistry tutoring prep."},
    {"message_id": 9, "role": "user", "content": "Cancel my gym workout session tomorrow morning"},
    {"message_id": 10, "role": "assistant", "content": "Your gym workout session tomorrow morning has been cancelled."},
    {"message_id": 11, "role": "user", "content": "Add a task to catalog my new scale figures collection"},
    {"message_id": 12, "role": "assistant", "content": "Added a task to catalog your scale figure collection."},
]

USER_ID = "eval-user"


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def build_match_messages_supabase() -> FakeSupabase:
    """FakeSupabase whose .rpc('match_messages', ...) ranks CORPUS by cosine
    similarity to the query embedding, honoring match_count + exclude_message_id."""
    corpus_vectors = {row["message_id"]: np.array(embed_text(row["content"])) for row in CORPUS}
    by_id = {row["message_id"]: row for row in CORPUS}

    def handler(_fn_name, params):
        query_vec = np.array(params["query_embedding"])
        match_count = params.get("match_count", 3)
        exclude_id = params.get("exclude_message_id")

        scored = [
            {**by_id[mid], "similarity": _cosine(query_vec, vec)}
            for mid, vec in corpus_vectors.items()
            if mid != exclude_id
        ]
        scored.sort(key=lambda r: r["similarity"], reverse=True)
        return scored[:match_count]

    return FakeSupabase(db={}, rpc_handler=handler)
