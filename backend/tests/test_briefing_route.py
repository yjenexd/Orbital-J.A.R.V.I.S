from types import SimpleNamespace

import app.routes.briefing as briefing_routes
from app.app_factory import app
from app.clients import get_groq_client


class FakeTable:
    def __init__(self, rows):
        self._rows = rows
        self._limit = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def limit(self, value):
        self._limit = value
        return self

    def execute(self):
        data = self._rows
        if self._limit is not None:
            data = data[: self._limit]
        return SimpleNamespace(data=data)


class FakeSupabase:
    def __init__(self, table_rows):
        self._table_rows = table_rows

    def table(self, name):
        return FakeTable(self._table_rows.get(name, []))


class FakeChatCompletions:
    def __init__(self, content):
        self._content = content

    async def create(self, **_kwargs):
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self._content))]
        )


class FakeOpenAIClient:
    def __init__(self, content):
        self.chat = SimpleNamespace(completions=FakeChatCompletions(content))


async def _override_groq_client():
    yield FakeOpenAIClient("Today you have one meeting and one urgent email.")


def test_briefing_returns_empty_summary_without_data(client, monkeypatch):
    monkeypatch.setattr(
        briefing_routes,
        "supabase",
        FakeSupabase({"schedule": [], "tasks": [], "email": []}),
    )
    app.dependency_overrides[get_groq_client] = _override_groq_client

    response = client.get("/api/briefing")

    assert response.status_code == 200
    body = response.json()
    assert body["has_events"] is False
    assert "no scheduled events" in body["briefing"].lower()


def test_briefing_uses_llm_when_data_exists(client, monkeypatch):
    monkeypatch.setattr(
        briefing_routes,
        "supabase",
        FakeSupabase(
            {
                "schedule": [{"event": "Demo", "time": "10:00:00"}],
                "tasks": [{"title": "Finalize slides", "priority": "high"}],
                "email": [{"subject": "Urgent feedback", "urgency": "high"}],
            }
        ),
    )
    app.dependency_overrides[get_groq_client] = _override_groq_client

    response = client.get("/api/briefing")

    assert response.status_code == 200
    body = response.json()
    assert body["has_events"] is True
    assert "urgent email" in body["briefing"].lower()
