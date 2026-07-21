"""Unit tests for the LLM-as-a-judge (app.guardrails.judge)."""

import asyncio

from langchain_core.messages import AIMessage

import app.graph.llm as graph_llm
from app.guardrails import judge as judge_module


class _FakeJudgeModel:
    """Returns a fixed judge payload; records that it was asked to evaluate."""

    def __init__(self, content):
        self._content = content
        self.calls = 0

    async def ainvoke(self, _messages):
        self.calls += 1
        return AIMessage(content=self._content)


class _RaisingModel:
    async def ainvoke(self, _messages):
        raise RuntimeError("judge upstream down")


def _run(user_msg, reply):
    return asyncio.run(judge_module.run_judge(user_msg, reply, "fake-key"))


def _enable_judge(monkeypatch, model):
    monkeypatch.setenv("GUARDRAILS_JUDGE_DISABLED", "0")
    monkeypatch.setattr(graph_llm, "get_chat_model", lambda _key: model)


def test_judge_disabled_passes_open_without_calling_model(monkeypatch):
    monkeypatch.setenv("GUARDRAILS_JUDGE_DISABLED", "1")
    model = _FakeJudgeModel('{"accuracy_score": 0.0, "verdict": "fail"}')
    monkeypatch.setattr(graph_llm, "get_chat_model", lambda _key: model)

    verdict = _run("hi", "there")

    assert verdict.passed
    assert verdict.score is None
    assert model.calls == 0


def test_high_score_passes(monkeypatch):
    model = _FakeJudgeModel('{"accuracy_score": 0.95, "verdict": "pass", "reason": "good"}')
    _enable_judge(monkeypatch, model)

    verdict = _run("add gym at 6pm", "Added your gym session at 6pm.")

    assert verdict.passed
    assert verdict.score == 0.95
    assert model.calls == 1


def test_low_score_fails_closed(monkeypatch):
    model = _FakeJudgeModel('{"accuracy_score": 0.2, "verdict": "fail", "reason": "hallucinated"}')
    _enable_judge(monkeypatch, model)

    verdict = _run("what's on friday?", "You have lunch with the King of Spain.")

    assert not verdict.passed
    assert verdict.score == 0.2


def test_high_score_but_fail_verdict_is_rejected(monkeypatch):
    # Numeric score is the source of truth, but a "fail" verdict still fails.
    model = _FakeJudgeModel('{"accuracy_score": 0.9, "verdict": "fail"}')
    _enable_judge(monkeypatch, model)

    assert not _run("q", "a").passed


def test_verdict_wrapped_in_prose_is_extracted(monkeypatch):
    model = _FakeJudgeModel('Here is my verdict: {"accuracy_score": 0.8, "verdict": "pass"} done')
    _enable_judge(monkeypatch, model)

    assert _run("q", "a").passed


def test_unparseable_output_passes_open(monkeypatch):
    model = _FakeJudgeModel("I think it's fine honestly")
    _enable_judge(monkeypatch, model)

    verdict = _run("q", "a")
    assert verdict.passed
    assert verdict.score is None


def test_judge_error_passes_open(monkeypatch):
    _enable_judge(monkeypatch, _RaisingModel())

    verdict = _run("q", "a")
    assert verdict.passed
    assert verdict.score is None
