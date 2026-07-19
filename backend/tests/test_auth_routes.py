from types import SimpleNamespace

import app.routes.core as core_routes
from app.app_factory import app
from app.clients import get_current_user_id


class _FakeTable:
    def __init__(self, rows):
        self._rows = rows

    def select(self, *_): return self
    def eq(self, *_): return self
    def order(self, *_): return self

    def maybe_single(self):
        self._maybe = True
        return self

    def execute(self):
        data = self._rows[0] if getattr(self, "_maybe", False) and self._rows else (self._rows[0] if self._rows else None)
        return SimpleNamespace(data=data)


class _FakeSupabase:
    def __init__(self, tables):
        self._tables = tables

    def table(self, name):
        return _FakeTable(self._tables.get(name, []))


def test_unauthenticated_request_returns_401(client):
    app.dependency_overrides.pop(get_current_user_id, None)
    response = client.get("/tasks")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing authorization header"


def test_missing_google_refresh_token_on_calendar_returns_401(client, monkeypatch):
    monkeypatch.setattr(
        core_routes,
        "supabase",
        _FakeSupabase({"users": [{"google_refresh_token": None}]}),
    )
    response = client.get("/calendar")
    assert response.status_code == 401
    assert "Google account not connected" in response.json()["detail"]


def test_missing_groq_key_returns_401(client):
    response = client.post(
        "/chat",
        json={"message": "hello", "user_id": "u1"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "API_KEY_MISSING"
