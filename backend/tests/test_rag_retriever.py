"""Tests for the RAG retriever. The embedding model is always monkeypatched
(never loaded) so these stay offline and fast."""

import app.rag.retriever as retriever


class _RecordingSupabase:
    """Captures the rpc call and returns a preset payload (or raises)."""

    def __init__(self, data=None, raise_exc=None):
        self._data = data if data is not None else []
        self._raise_exc = raise_exc
        self.last_call = None

    def rpc(self, fn_name, params):
        self.last_call = (fn_name, params)
        supabase = self

        class _Query:
            def execute(self):
                if supabase._raise_exc is not None:
                    raise supabase._raise_exc
                from types import SimpleNamespace

                return SimpleNamespace(data=supabase._data)

        return _Query()


def _patch(monkeypatch, supabase):
    monkeypatch.setattr(retriever, "embed_text", lambda _text: [0.1] * 384)
    monkeypatch.setattr(retriever, "supabase", supabase)


def test_returns_hits_and_passes_correct_rpc_params(monkeypatch):
    hits = [
        {"message_id": 5, "role": "user", "content": "buy fish food", "similarity": 0.9},
    ]
    supabase = _RecordingSupabase(data=hits)
    _patch(monkeypatch, supabase)

    result = retriever.retrieve_relevant_messages(
        "user-abc", "did I log fish food?", k=3, exclude_message_id=42
    )

    assert result == hits
    fn_name, params = supabase.last_call
    assert fn_name == "match_messages"
    assert params["match_user_id"] == "user-abc"
    assert params["match_count"] == 3
    assert params["exclude_message_id"] == 42
    assert len(params["query_embedding"]) == 384


def test_rpc_exception_fails_open_to_empty_list(monkeypatch):
    supabase = _RecordingSupabase(raise_exc=RuntimeError("pg down"))
    _patch(monkeypatch, supabase)

    result = retriever.retrieve_relevant_messages("user-abc", "anything")

    assert result == []


def test_zero_hits_returns_empty_list(monkeypatch):
    supabase = _RecordingSupabase(data=[])
    _patch(monkeypatch, supabase)

    result = retriever.retrieve_relevant_messages("user-abc", "no matches here")

    assert result == []


def test_none_data_returns_empty_list(monkeypatch):
    supabase = _RecordingSupabase(data=None)
    _patch(monkeypatch, supabase)

    assert retriever.retrieve_relevant_messages("user-abc", "q") == []


def test_empty_query_short_circuits_without_calling_rpc(monkeypatch):
    supabase = _RecordingSupabase(data=[{"message_id": 1}])
    _patch(monkeypatch, supabase)

    assert retriever.retrieve_relevant_messages("user-abc", "   ") == []
    assert supabase.last_call is None
