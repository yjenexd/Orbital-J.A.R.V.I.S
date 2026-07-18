-- Add the missing `time` column to public.schedule.
--
-- GET /schedule (app/routes/core.py), the add_/update_schedule_event tool
-- handlers (app/chat/tool_handlers.py), and the frontend SchedulePanel all
-- read/write schedule.time, but the table (originally created in the Supabase
-- dashboard) never had the column. That mismatch surfaced as a 500 once the
-- /schedule route was switched to read from Supabase instead of Google
-- Calendar directly:
--   column schedule.time does not exist  (SQLSTATE 42703)
--
-- Stored as a `time` value ("HH:MM"/"HH:MM:SS"); nullable so existing rows are
-- unaffected. Idempotent so it is safe to re-run.
alter table public.schedule
  add column if not exists "time" time;
