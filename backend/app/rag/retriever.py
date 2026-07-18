"""Retrieval over chat history via the match_messages pgvector RPC.

Every path fails open: any error (embedding failure, RPC error, bad shape)
returns an empty list so retrieval can never fail a /chat request. Retrieval is
an enhancement to the prompt, never a dependency of it."""

from app.clients import supabase
from app.rag.embedder import embed_text


def retrieve_relevant_messages(
    user_id: str,
    query: str,
    k: int = 3,
    exclude_message_id=None,
) -> list[dict]:
    """Return up to k of the user's past messages most similar to `query`.

    Each result: {message_id, role, content, created_at, similarity}. Returns []
    on empty query or any failure.
    """
    if not query or not query.strip():
        return []

    try:
        query_embedding = embed_text(query)
        response = supabase.rpc(
            "match_messages",
            {
                "query_embedding": query_embedding,
                "match_user_id": user_id,
                "match_count": k,
                "exclude_message_id": exclude_message_id,
            },
        ).execute()
        return response.data or []
    except Exception as e:
        print(f"[RAG] retrieval failed, continuing without context: {e}")
        return []
