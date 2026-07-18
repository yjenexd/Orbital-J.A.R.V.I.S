"""State-transition tests for the chat graph, invoking the compiled graph
directly (not via HTTP) so each routing branch is exercised in isolation."""

import asyncio

from langchain_core.messages import AIMessage

import app.chat.tool_handlers as tool_handlers
import app.graph.chat_graph as chat_graph
import app.graph.llm as graph_llm
from tests._fakes import FakeSupabase


def _invoke(state, config=None):
    return asyncio.run(
        chat_graph.chat_graph.ainvoke(state, config=config or {"configurable": {}})
    )


def _base_state(message):
    return {"user_id": "test-user-id", "user_message": message, "messages": []}


class _FakeModel:
    def __init__(self, ai_message):
        self._ai_message = ai_message
        self.calls = 0

    def bind_tools(self, _tools):
        return self

    async def ainvoke(self, _messages):
        self.calls += 1
        return self._ai_message


class _ModelMustNotRun:
    def bind_tools(self, _tools):
        return self

    async def ainvoke(self, _messages):
        raise AssertionError("Model must not be called on this path")


class _CapturingModel:
    """Records the system prompt it was handed, replies with plain text."""

    def __init__(self, reply="ok"):
        self._reply = reply
        self.system_prompt = None

    def bind_tools(self, _tools):
        return self

    async def ainvoke(self, messages):
        self.system_prompt = messages[0].content
        return AIMessage(content=self._reply)


def _enable_rag(monkeypatch):
    # Turn inline RAG on for this test, but stub the embedder so no model loads.
    monkeypatch.setenv("RAG_SKIP_WARMUP", "0")
    monkeypatch.setattr(chat_graph, "embed_text", lambda _text: [0.0] * 384)


class _FakeGcal:
    """Minimal Google Calendar stub: event listing returns nothing, which is all
    ingest_context needs."""

    def events(self):
        return self

    def list(self, **_kwargs):
        return self

    def execute(self):
        return {"items": []}


def _install(monkeypatch, supabase, model=None):
    monkeypatch.setattr(chat_graph, "supabase", supabase)
    monkeypatch.setattr(tool_handlers, "supabase", supabase)
    if model is not None:
        monkeypatch.setattr(graph_llm, "get_chat_model", lambda _key: model)


def test_date_shortcut_short_circuits_and_skips_user_message_insert(monkeypatch):
    db = {"messages": []}
    supabase = FakeSupabase(db)
    _install(monkeypatch, supabase, _ModelMustNotRun())

    result = _invoke(_base_state("what is the date today?"))

    assert result["final_reply"].startswith("Today's date is ")
    # Only the assistant reply is logged; the date shortcut never logs the user turn.
    assert [m["role"] for m in db["messages"]] == ["assistant"]


def test_non_action_guard_short_circuits_after_logging_user_message(monkeypatch):
    db = {"messages": [], "tasks": [], "users": [{"id": "test-user-id"}]}
    supabase = FakeSupabase(db)
    _install(monkeypatch, supabase, _ModelMustNotRun())

    result = _invoke(_base_state("hi"))

    assert result["final_reply"] == "Ready when you are. Tell me what task or event you want to manage."
    # Unlike the date shortcut, the guard runs after the user-message insert.
    assert [m["role"] for m in db["messages"]] == ["user", "assistant"]


def test_no_tool_call_returns_model_text(monkeypatch):
    db = {"messages": [], "tasks": [], "users": [{"id": "test-user-id", "google_refresh_token": None}]}
    supabase = FakeSupabase(db)
    model = _FakeModel(AIMessage(content="Here's what I found."))
    _install(monkeypatch, supabase, model)

    result = _invoke(_base_state("summarize my day"))

    assert result["final_reply"] == "Here's what I found."
    assert model.calls == 1
    assert [m["role"] for m in db["messages"]] == ["user", "assistant"]


def test_tool_call_success_round_trip(monkeypatch):
    db = {
        "messages": [],
        "tasks": [],
        "users": [{"id": "test-user-id", "google_refresh_token": None}],
    }
    supabase = FakeSupabase(db)
    ai = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "add_task",
                "args": {"title": "Finish CS2040S lab", "deadline": "2026-08-01"},
                "id": "tc-1",
            }
        ],
    )
    _install(monkeypatch, supabase, _FakeModel(ai))

    result = _invoke(_base_state("add a task to finish the CS2040S lab by Aug 1"))

    assert result["final_reply"] == "Task added successfully."
    assert any(t.get("title") == "Finish CS2040S lab" for t in db["tasks"])


def test_pending_confirmation_flow(monkeypatch):
    db = {
        "messages": [],
        "tasks": [{"task_id": 7, "user_id": "test-user-id", "title": "Water the aquarium"}],
        "users": [{"id": "test-user-id", "google_refresh_token": None}],
    }
    supabase = FakeSupabase(db)
    ai = AIMessage(
        content="",
        tool_calls=[
            {"name": "delete_task", "args": {"task_id": 7, "user_confirmed": False}, "id": "tc-1"}
        ],
    )
    _install(monkeypatch, supabase, _FakeModel(ai))

    result = _invoke(_base_state("delete the aquarium task"))

    assert result["final_reply"] == "Are you sure you want to delete Water the aquarium?"


# --- Phase 3: retrieval paths ------------------------------------------------

def _rag_db():
    return {"messages": [], "tasks": [], "users": [{"id": "test-user-id", "google_refresh_token": None}]}


def test_retrieval_success_injects_docs_into_prompt(monkeypatch):
    supabase = FakeSupabase(_rag_db())
    _enable_rag(monkeypatch)
    monkeypatch.setattr(
        chat_graph,
        "retrieve_relevant_messages",
        lambda *a, **k: [{"role": "user", "content": "remind me to buy fish food", "similarity": 0.88}],
    )
    model = _CapturingModel()
    _install(monkeypatch, supabase, model)

    result = _invoke(_base_state("did I mention anything about the aquarium?"))

    assert result["final_reply"] == "ok"
    assert "RELEVANT PAST MESSAGES" in model.system_prompt
    assert "buy fish food" in model.system_prompt


def test_retrieval_passes_self_exclusion_id(monkeypatch):
    supabase = FakeSupabase(_rag_db())
    _enable_rag(monkeypatch)
    captured = {}

    def _fake_retrieve(user_id, query, k=3, exclude_message_id=None):
        captured["exclude_message_id"] = exclude_message_id
        captured["user_id"] = user_id
        return []

    monkeypatch.setattr(chat_graph, "retrieve_relevant_messages", _fake_retrieve)
    _install(monkeypatch, supabase, _CapturingModel())

    _invoke(_base_state("anything relevant?"))

    # FakeSupabase auto-assigns message_id 1001 to the first inserted message;
    # the just-logged user message must be excluded from its own retrieval.
    assert captured["exclude_message_id"] == 1001
    assert captured["user_id"] == "test-user-id"


def test_retrieval_failure_falls_back_and_still_replies(monkeypatch):
    supabase = FakeSupabase(_rag_db())
    _enable_rag(monkeypatch)

    def _boom(*_a, **_k):
        raise RuntimeError("vector store unreachable")

    monkeypatch.setattr(chat_graph, "retrieve_relevant_messages", _boom)
    model = _CapturingModel()
    _install(monkeypatch, supabase, model)

    result = _invoke(_base_state("what did we discuss last week?"))

    # Turn still completes; prompt simply carries no retrieved section.
    assert result["final_reply"] == "ok"
    assert "RELEVANT PAST MESSAGES" not in (model.system_prompt or "")


def test_retrieval_zero_hits_adds_no_section(monkeypatch):
    supabase = FakeSupabase(_rag_db())
    _enable_rag(monkeypatch)
    monkeypatch.setattr(chat_graph, "retrieve_relevant_messages", lambda *a, **k: [])
    model = _CapturingModel()
    _install(monkeypatch, supabase, model)

    result = _invoke(_base_state("hello there, any context?"))

    assert result["final_reply"] == "ok"
    assert "RELEVANT PAST MESSAGES" not in model.system_prompt
