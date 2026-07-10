import asyncio
import json
from datetime import timedelta
from types import SimpleNamespace

import app.chat.triage as triage
from app.config import CURR_DATE


class FakeUpdateQuery:
    def __init__(self, captured_updates, payload):
        self._captured_updates = captured_updates
        self._payload = payload

    def eq(self, *_args, **_kwargs):
        return self

    def execute(self):
        self._captured_updates.append(self._payload)
        return SimpleNamespace(data=[self._payload])


class FakeTable:
    def __init__(self, captured_updates):
        self._captured_updates = captured_updates

    def update(self, payload):
        return FakeUpdateQuery(self._captured_updates, payload)


class FakeSupabase:
    def __init__(self):
        self.captured_updates = []

    def table(self, _name):
        return FakeTable(self.captured_updates)


class FakeChatCompletions:
    def __init__(self, response_json, captured_messages):
        self._response_json = response_json
        self._captured_messages = captured_messages

    async def create(self, **kwargs):
        self._captured_messages.append(kwargs["messages"][0]["content"])
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(self._response_json)))]
        )


class FakeAsyncOpenAI:
    def __init__(self, response_json, captured_messages, **_kwargs):
        self.chat = SimpleNamespace(
            completions=FakeChatCompletions(response_json=response_json, captured_messages=captured_messages)
        )

    async def close(self):
        return None


def test_triage_prompt_contains_critical_cs_weighting_and_persists_high_score(monkeypatch):
    fake_supabase = FakeSupabase()
    captured_messages = []

    monkeypatch.setattr(triage, "supabase", fake_supabase)
    monkeypatch.setattr(
        triage,
        "AsyncOpenAI",
        lambda **kwargs: FakeAsyncOpenAI(
            response_json={
                "priority_level": "high",
                "priority_score": 95,
                "triage_rationale": "Core CS assignment due within 48 hours.",
            },
            captured_messages=captured_messages,
            **kwargs,
        ),
    )

    deadline = (CURR_DATE + timedelta(days=1)).isoformat()
    asyncio.run(
        triage.triage_task_background(
            task_id=1,
            user_id="u1",
            title="Submit CS2040S Assignment",
            deadline=deadline,
            x_groq_api_key="test-key",
        )
    )

    prompt = captured_messages[0]
    assert "Submit CS2040S Assignment" in prompt
    assert "CRITICAL (Score 90-100)" in prompt
    assert "within 48 hours" in prompt
    assert fake_supabase.captured_updates[0]["priority_score"] == 95


def test_triage_prompt_contains_hobby_band_and_persists_medium_score(monkeypatch):
    fake_supabase = FakeSupabase()
    captured_messages = []

    monkeypatch.setattr(triage, "supabase", fake_supabase)
    monkeypatch.setattr(
        triage,
        "AsyncOpenAI",
        lambda **kwargs: FakeAsyncOpenAI(
            response_json={
                "priority_level": "medium",
                "priority_score": 62,
                "triage_rationale": "Routine maintenance due in several days.",
            },
            captured_messages=captured_messages,
            **kwargs,
        ),
    )

    asyncio.run(
        triage.triage_task_background(
            task_id=2,
            user_id="u1",
            title="Change the water in my high-tech planted tank",
            deadline=(CURR_DATE + timedelta(days=5)).isoformat(),
            x_groq_api_key="test-key",
        )
    )

    prompt = captured_messages[0]
    assert "Routine maintenance" in prompt
    assert "MEDIUM (Score 50-74)" in prompt
    assert fake_supabase.captured_updates[0]["priority"] == "medium"
    assert fake_supabase.captured_updates[0]["priority_score"] == 62
