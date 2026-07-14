-- Relax the legacy NOT NULL constraint on public.schedule.start_time.
--
-- The schedule table predates the switch to a single `time` column (added in
-- 20260713000001). It still carries the original start_time/end_time columns,
-- but no code path reads or writes them anymore -- add_schedule_event /
-- update_schedule_event and the /schedule + frontend readers all use `time`.
--
-- Because start_time is still NOT NULL, every insert from the current code
-- fails with:
--   null value in column "start_time" of relation "schedule"
--   violates not-null constraint  (SQLSTATE 23502)
--
-- Dropping the NOT NULL constraint unblocks inserts without touching existing
-- data. (The columns can be dropped entirely in a later migration once we've
-- confirmed nothing external depends on them.) Idempotent / safe to re-run.
alter table public.schedule
  alter column start_time drop not null;
