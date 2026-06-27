import json
from types import SimpleNamespace

import app.chat.tool_handlers as tool_handlers
import app.routes.chat as chat_routes
from app.app_factory import app
from app.clients import get_groq_client


class FakeTable:
    def __init__(self, db, name):
        self._db = db
        self._name = name
        self._filters = []
        self._limit = None
        self._single = False
        self._insert_payload = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, key, value):
        self._filters.append((key, value))
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, value):
        self._limit = value
        return self

    def single(self):
        self._single = True
        return self

    def insert(self, payload):
        self._insert_payload = payload
        return self

    def _rows(self):
        rows = self._db.setdefault(self._name, [])
        filtered = rows
        for key, value in self._filters:
            filtered = [r for r in filtered if r.get(key) == value]
        return filtered

    def execute(self):
        if self._insert_payload is not None:
            payload = dict(self._insert_payload)
            self._db.setdefault(self._name, []).append(payload)
            return SimpleNamespace(data=[payload])

        rows = self._rows()
        if self._limit is not None:
            rows = rows[: self._limit]
        if self._single:
            return SimpleNamespace(data=rows[0] if rows else {})
        return SimpleNamespace(data=rows)


class FakeSupabase:
    def __init__(self, db):
        self._db = db

    def table(self, name):
        return FakeTable(self._db, name)


class FakeMessageWithTools:
    def __init__(self, tool_calls):
        self.content = None
        self.tool_calls = tool_calls


class FakeChatCompletionsNoSecondCall:
    def __init__(self, first_message):
        self.first_message = first_message
        self.calls = 0

    async def create(self, **_kwargs):
        self.calls += 1
        if self.calls > 1:
            raise AssertionError("Second model call should not happen")
        return SimpleNamespace(choices=[SimpleNamespace(message=self.first_message)])


class FakeChatCompletionsMustNotRun:
    def __init__(self):
        self.calls = 0

    async def create(self, **_kwargs):
        self.calls += 1
        raise AssertionError("Model should not be called for non-action probes")


class FakeOpenAIClient:
    def __init__(self, completions):
        self.chat = SimpleNamespace(completions=completions)


def _set_client_override(completions):
    async def _override_groq_client():
        yield FakeOpenAIClient(completions)

    app.dependency_overrides[get_groq_client] = _override_groq_client


def test_chat_non_action_probe_is_blocked_before_model_call(client, monkeypatch):
    fake_db = {
        "messages": [],
        "tasks": [],
        "users": [{"id": "test-user-id", "name": "Test", "google_refresh_token": None}],
    }
    fake_supabase = FakeSupabase(fake_db)
    monkeypatch.setattr(chat_routes, "supabase", fake_supabase)
    monkeypatch.setattr(tool_handlers, "supabase", fake_supabase)

    completions = FakeChatCompletionsMustNotRun()
    _set_client_override(completions)

    response = client.post(
        "/chat",
        json={"user_id": "ignored", "message": "test", "history_limit": 10},
    )

    assert response.status_code == 200
    assert response.json()["reply"] == "Ready when you are. Tell me what task or event you want to manage."
    assert completions.calls == 0


def test_chat_pending_confirmation_returns_clean_question(client, monkeypatch):
    fake_db = {
        "messages": [],
        "tasks": [{"task_id": 12, "user_id": "test-user-id", "title": "Buy fish food"}],
        "users": [{"id": "test-user-id", "name": "Test", "google_refresh_token": None}],
    }
    fake_supabase = FakeSupabase(fake_db)
    monkeypatch.setattr(chat_routes, "supabase", fake_supabase)
    monkeypatch.setattr(tool_handlers, "supabase", fake_supabase)

    delete_call = SimpleNamespace(
        id="tool-1",
        function=SimpleNamespace(
            name="delete_task",
            arguments=json.dumps({"task_id": 12, "user_confirmed": False}),
        ),
    )
    completions = FakeChatCompletionsNoSecondCall(FakeMessageWithTools([delete_call]))
    _set_client_override(completions)

    response = client.post(
        "/chat",
        json={"user_id": "ignored", "message": "Delete task 12", "history_limit": 10},
    )

    assert response.status_code == 200
    assert response.json()["reply"] == "Are you sure you want to delete Buy fish food?"
    assert completions.calls == 1
