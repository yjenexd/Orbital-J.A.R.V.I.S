"""One-off backfill: embed messages rows that predate the embedding column.

New messages get embedded inline at insert time by the chat graph, so this only
needs running once after applying the pgvector migrations, to populate history
written before then.

Usage (from backend/):
    python -m scripts.backfill_message_embeddings [--batch 200] [--dry-run]
"""

import argparse

from app.clients import supabase
from app.rag.embedder import embed_text


def backfill(batch_size: int = 200, dry_run: bool = False) -> int:
    total = 0
    while True:
        rows = (
            supabase.table("messages")
            .select("message_id, content")
            .is_("embedding", "null")
            .limit(batch_size)
            .execute()
            .data
            or []
        )
        if not rows:
            break

        for row in rows:
            content = row.get("content") or ""
            if not content.strip():
                continue
            if dry_run:
                total += 1
                continue
            embedding = embed_text(content)
            supabase.table("messages").update({"embedding": embedding}).eq(
                "message_id", row["message_id"]
            ).execute()
            total += 1

        print(f"[backfill] processed {total} rows so far...")
        if dry_run:
            # Nothing is written, so the same rows would return forever.
            break

    print(f"[backfill] done. {'Would embed' if dry_run else 'Embedded'} {total} rows.")
    return total


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill embeddings for existing messages.")
    parser.add_argument("--batch", type=int, default=200, help="Rows per batch.")
    parser.add_argument("--dry-run", action="store_true", help="Count only; write nothing.")
    args = parser.parse_args()
    backfill(batch_size=args.batch, dry_run=args.dry_run)
