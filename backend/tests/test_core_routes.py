from types import SimpleNamespace

import app.routes.core as core_routes


class FakeTable:
    def __init__(self, rows):
        self._rows = rows
        self._limit = None
        self._single = False
        self._maybe_single = False

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, value):
        self._limit = value
        return self

    def single(self):
        self._single = True
        return self

    def maybe_single(self):
        self._maybe_single = True
        return self

    def execute(self):
        data = self._rows
        if self._limit is not None:
            data = data[: self._limit]
        if self._single:
            data = data[0] if data else {}
        elif self._maybe_single:
            data = data[0] if data else None
        return SimpleNamespace(data=data)


class FakeSupabase:
    def __init__(self, table_rows):
        self._table_rows = table_rows

    def table(self, name):
        return FakeTable(self._table_rows.get(name, []))


class FakeEventsService:
    def __init__(self, payload):
        self._payload = payload

    def list(self, **_kwargs):
        return self

    def execute(self):
        return self._payload


class FakeCalendarService:
    def __init__(self, payload):
        self._payload = payload

    def events(self):
        return FakeEventsService(self._payload)


def test_get_tasks_returns_tasks(client, monkeypatch):
    monkeypatch.setattr(
        core_routes,
        "supabase",
        FakeSupabase(
            {
                "tasks": [
                    {
                        "task_id": 1,
                        "title": "Study",
                        "priority": "high",
                        "source": "manual",
                        "deadline": "2026-06-24",
                        "completed": False,
                    }
                ]
            }
        ),
    )

    response = client.get("/tasks")

    assert response.status_code == 200
    assert response.json()["tasks"][0]["title"] == "Study"


def test_get_calendar_maps_google_event_fields(client, monkeypatch):
    payload = {
        "items": [
            {
                "id": "evt-1",
                "summary": "Project Sync",
                "start": {"dateTime": "2026-06-22T09:30:00+08:00"},
                "extendedProperties": {"private": {"protected": "true"}},
            }
        ]
    }
    monkeypatch.setattr(
        core_routes,
        "supabase",
        FakeSupabase({"users": [{"google_refresh_token": "fake-refresh"}]}),
    )
    monkeypatch.setattr(
        core_routes,
        "get_google_calendar_service",
        lambda _refresh_token: FakeCalendarService(payload),
    )

    response = client.get("/calendar")

    assert response.status_code == 200
    schedule = response.json()["schedule"]
    assert schedule[0]["event_id"] == "evt-1"
    assert schedule[0]["date"] == "2026-06-22"
    assert schedule[0]["start_time"] == "09:30"
    assert schedule[0]["protected"] is True
