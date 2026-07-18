-- Cosine-similarity retrieval over a user's chat history.
-- Called from Python via supabase.rpc("match_messages", {...}).
--
-- Multi-tenant boundary = the match_user_id filter here (this app uses a single
-- service-scoped Supabase key and filters by user_id at the app layer
-- everywhere; there is no RLS. Keep that convention — do not add RLS here).
--
-- exclude_message_id lets the caller drop the just-inserted current user message
-- so it can't self-match at distance 0 and dominate the results.
--
-- NOTE: assumes messages.message_id is bigint and users are keyed by uuid,
-- matching the rest of the schema. Confirm against the live DB before applying.
create or replace function match_messages(
  query_embedding vector(384),
  match_user_id uuid,
  match_count int default 3,
  exclude_message_id bigint default null
)
returns table (
  message_id bigint,
  role text,
  content text,
  created_at timestamptz,
  similarity float
)
language sql stable
as $$
  select
    message_id,
    role,
    content,
    created_at,
    1 - (embedding <=> query_embedding) as similarity
  from messages
  where user_id = match_user_id
    and embedding is not null
    and (exclude_message_id is null or message_id <> exclude_message_id)
  order by embedding <=> query_embedding
  limit match_count;
$$;
