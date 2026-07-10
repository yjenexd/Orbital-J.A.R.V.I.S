-- Enable pgvector for semantic retrieval over chat history.
-- First versioned migration for this project; prior schema was applied ad hoc
-- (see backend/data/db.txt). This file only turns the extension on.
create extension if not exists vector;
