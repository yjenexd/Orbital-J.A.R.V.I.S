import json
from types import SimpleNamespace

import pytest

import app.chat.tool_handlers as tool_handlers


class FakeTable:
    def __init__(self, database, name):
        self._database = database
        self._name = name
        self._filters = []
        self._select_cols = None
        self._pending_insert = None
        self._pending_update = None
        self._delete_mode = False

    def select(self, cols):
        self._select_cols = [c.strip() for c in cols.split(",")]
        return self

    def eq(self, key, value):
        self._filters.append((key, value))
        return self

    def insert(self, payload):
        self._pending_insert = payload
        return self

    def update(self, payload):
        self._pending_update = payload
        return self

    def delete(self):
        self._delete_mode = True
        return self

    def _filtered_rows(self):
        rows = self._database.setdefault(self._name, [])
        filtered = rows
        for key, value in self._filters:
            filtered = [r for r in filtered if r.get(key) == value]
        return filtered

    def execute(self):
        rows = self._database.setdefault(self._name, [])

        if self._pending_insert is not None:
            payload = dict(self._pending_insert)
            if "task_id" not in payload and self._name == "tasks":
                payload["task_id"] = max([r.get("task_id", 0) for r in rows] + [0]) + 1
            rows.append(payload)
            return SimpleNamespace(data=[payload])

        if self._pending_update is not None:
            updated = []
            for row in self._filtered_rows():
                row.update(self._pending_update)
                updated.append(row)
            return SimpleNamespace(data=updated)

        if self._delete_mode:
            to_delete = self._filtered_rows()
            self._database[self._name] = [r for r in rows if r not in to_delete]
            return SimpleNamespace(data=to_delete)

        selected = [dict(r) for r in self._filtered_rows()]
        if self._select_cols is not None:
            selected = [{k: r.get(k) for k in self._select_cols} for r in selected]
        return SimpleNamespace(data=selected)


class FakeSupabase:
    def __init__(self, database):
        self._database = database

    def table(self, name):
        return FakeTable(self._database, name)


class FakeEventsAPI:
    def __init__(self, event_lookup):
        self._event_lookup = event_lookup
        self.insert_calls = []
        self.patch_calls = []
        self.delete_calls = []

    def insert(self, **kwargs):
        self.insert_calls.append(kwargs)
        return SimpleNamespace(execute=lambda: {"id": "evt-new"})

    def patch(self, **kwargs):
        self.patch_calls.append(kwargs)
        return SimpleNamespace(execute=lambda: {"ok": True})

    def delete(self, **kwargs):
        self.delete_calls.append(kwargs)
        return SimpleNamespace(execute=lambda: {"ok": True})

    def get(self, calendarId, eventId):
        event = self._event_lookup[eventId]
        return SimpleNamespace(execute=lambda: event)


class FakeGcalService:
    def __init__(self, event_lookup=None):
        self._events_api = FakeEventsAPI(event_lookup or {})

    def events(self):
        return self._events_api


class FakeBackgroundTasks:
    def __init__(self):
        self.calls = []

    def add_task(self, fn, **kwargs):
        self.calls.append((fn, kwargs))


def test_add_task_missing_deadline_returns_pending_information():
    res = tool_handlers.execute_tool_call(
        "add_task",
        {"title": "buy fish food"},
        user_id="u1",
    )

    parsed = json.loads(res)
    assert parsed["status"] == "pending_information"
    assert "When is the deadline for this task?" in parsed["message"]


def test_update_task_vague_context_is_forwarded_to_background_triage(monkeypatch):
    db = {
        "tasks": [
            {
                "task_id": 42,
                "user_id": "u1",
                "title": "CS2040S assignment",
                "deadline": "2026-06-30",
                "gcal_event_id": None,
            }
        ]
    }
    monkeypatch.setattr(tool_handlers, "supabase", FakeSupabase(db))
    background_tasks = FakeBackgroundTasks()

    res = tool_handlers.execute_tool_call(
        "update_task",
        {"task_id": 42, "user_context": "it's actually super important"},
        user_id="u1",
        background_tasks=background_tasks,
        x_groq_api_key="test-key",
    )

    parsed = json.loads(res)
    assert parsed["status"] == "success"
    assert len(background_tasks.calls) == 1
    _, kwargs = background_tasks.calls[0]
    assert kwargs["task_id"] == 42
    assert kwargs["user_context"] == "it's actually super important"


def test_update_task_unknown_id_reports_error_and_skips_triage(monkeypatch):
    # Task 999 does not exist (and task 42 belongs to a different user), so the
    # update touches zero rows. It must report an error rather than a false
    # "updated" success, and must not queue background triage.
    db = {"tasks": [{"task_id": 42, "user_id": "someone-else", "title": "Not yours"}]}
    monkeypatch.setattr(tool_handlers, "supabase", FakeSupabase(db))
    background_tasks = FakeBackgroundTasks()

    res = tool_handlers.execute_tool_call(
        "update_task",
        {"task_id": 999, "priority": "high"},
        user_id="u1",
        background_tasks=background_tasks,
        x_groq_api_key="test-key",
    )

    parsed = json.loads(res)
    assert parsed["status"] == "error"
    assert background_tasks.calls == []


def test_delete_task_pending_confirmation_includes_task_name(monkeypatch):
    db = {"tasks": [{"task_id": 12, "user_id": "u1", "title": "Buy fish food"}]}
    monkeypatch.setattr(tool_handlers, "supabase", FakeSupabase(db))

    res = tool_handlers.execute_tool_call(
        "delete_task",
        {"task_id": 12, "user_confirmed": False},
        user_id="u1",
    )

    parsed = json.loads(res)
    assert parsed["status"] == "pending_confirmation"
    assert "Are you sure you want to delete Buy fish food?" in parsed["message"]


def test_delete_schedule_event_pending_confirmation_includes_event_details():
    gcal = FakeGcalService(
        {
            "evt-1": {
                "summary": "Milestone Sync",
                "start": {"dateTime": "2026-06-30T15:00:00+08:00"},
            }
        }
    )

    res = tool_handlers.execute_tool_call(
        "delete_schedule_event",
        {"event_id": "evt-1", "user_confirmed": False},
        user_id="u1",
        gcal_service=gcal,
    )

    parsed = json.loads(res)
    assert parsed["status"] == "pending_confirmation"
    assert "Milestone Sync" in parsed["message"]
    assert "2026-06-30" in parsed["message"]
    assert "15:00" in parsed["message"]


def test_add_schedule_event_persists_start_and_end_time(monkeypatch):
    db = {"schedule": []}
    monkeypatch.setattr(tool_handlers, "supabase", FakeSupabase(db))
    gcal = FakeGcalService()

    res = tool_handlers.execute_tool_call(
        "add_schedule_event",
        {"date": "2026-07-20", "start_time": "13:00", "end_time": "14:00", "event_title": "Run"},
        user_id="u1",
        gcal_service=gcal,
    )

    assert json.loads(res)["status"] == "success"
    row = db["schedule"][0]
    assert row["start_time"] == "13:00"
    assert row["end_time"] == "14:00"


@pytest.mark.skip(reason="Blackout window disabled (BLACKOUT_START=None); feature preserved for future use")
def test_add_schedule_event_blackout_window_is_rejected():
    gcal = FakeGcalService()

    res = tool_handlers.execute_tool_call(
        "add_schedule_event",
        {"date": "2026-07-10", "start_time": "14:00", "end_time": "15:00", "event_title": "Sync with Jason"},
        user_id="u1",
        gcal_service=gcal,
    )

    parsed = json.loads(res)
    assert parsed["status"] == "error"
    assert "blackout" in parsed["message"].lower()
    assert gcal.events().insert_calls == []


@pytest.mark.skip(reason="Blackout window disabled (BLACKOUT_START=None); feature preserved for future use")
def test_update_schedule_event_blackout_window_is_rejected():
    gcal = FakeGcalService(
        {
            "evt-2": {
                "summary": "Weekly Review",
                "start": {"dateTime": "2026-06-29T10:00:00+08:00"},
            }
        }
    )

    res = tool_handlers.execute_tool_call(
        "update_schedule_event",
        {"event_id": "evt-2", "date": "2026-07-12", "start_time": "10:00"},
        user_id="u1",
        gcal_service=gcal,
    )

    parsed = json.loads(res)
    assert parsed["status"] == "error"
    assert "blackout" in parsed["message"].lower()
    assert gcal.events().patch_calls == []


def test_add_schedule_event_calls_gcal_insert(monkeypatch):
    db = {"schedule": []}
    monkeypatch.setattr(tool_handlers, "supabase", FakeSupabase(db))
    gcal = FakeGcalService()

    res = tool_handlers.execute_tool_call(
        "add_schedule_event",
        {"date": "2026-07-05", "start_time": "14:00", "end_time": "15:00", "event_title": "Test Sync"},
        user_id="u1",
        gcal_service=gcal,
    )

    assert json.loads(res)["status"] == "success"
    insert_calls = gcal.events().insert_calls
    assert len(insert_calls) == 1
    body = insert_calls[0]["body"]
    assert body["summary"] == "Test Sync"
    assert "14:00" in body["start"]["dateTime"]
    assert "15:00" in body["end"]["dateTime"]


def test_delete_schedule_event_calls_gcal_delete(monkeypatch):
    db = {"schedule": [{"gcal_event_id": "evt-del", "user_id": "u1"}]}
    monkeypatch.setattr(tool_handlers, "supabase", FakeSupabase(db))
    gcal = FakeGcalService({
        "evt-del": {"summary": "Test Sync", "start": {"dateTime": "2026-07-05T14:00:00+08:00"}}
    })

    res = tool_handlers.execute_tool_call(
        "delete_schedule_event",
        {"event_id": "evt-del", "user_confirmed": True},
        user_id="u1",
        gcal_service=gcal,
    )

    assert json.loads(res)["status"] == "success"
    delete_calls = gcal.events().delete_calls
    assert len(delete_calls) == 1
    assert delete_calls[0]["eventId"] == "evt-del"


def test_update_schedule_event_calls_gcal_patch(monkeypatch):
    db = {"schedule": [{"gcal_event_id": "evt-upd", "user_id": "u1", "event": "Test Sync"}]}
    monkeypatch.setattr(tool_handlers, "supabase", FakeSupabase(db))
    gcal = FakeGcalService({
        "evt-upd": {
            "summary": "Test Sync",
            "start": {"dateTime": "2026-07-05T14:00:00+08:00"},
            "end": {"dateTime": "2026-07-05T15:00:00+08:00"},
        }
    })

    res = tool_handlers.execute_tool_call(
        "update_schedule_event",
        {"event_id": "evt-upd", "start_time": "16:00", "end_time": "17:00"},
        user_id="u1",
        gcal_service=gcal,
    )

    assert json.loads(res)["status"] == "success"
    patch_calls = gcal.events().patch_calls
    assert len(patch_calls) == 1
    assert "16:00" in patch_calls[0]["body"]["start"]["dateTime"]
