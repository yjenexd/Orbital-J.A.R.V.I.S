"""LLM-as-a-judge: rates a candidate reply for accuracy/alignment.

Runs only on the pure-text generation path (tool confirmations are already
deterministic, so there is nothing to hallucinate there) and only when
`judge_enabled()` is true. Fails OPEN: if the judge call errors or returns an
unparseable verdict, we pass the reply through rather than block a user on a
judge malfunction. A genuinely low score, by contrast, fails CLOSED and routes
the graph to retry/fallback.
"""

from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph import llm
from app.guardrails.config import JUDGE_ACCEPT_SCORE, judge_enabled
from app.guardrails.output_validation import validate_judge_output
from app.guardrails.schemas import JudgeVerdict
from app.prompts import JUDGE_SYSTEM_PROMPT, build_judge_prompt


_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_verdict(raw: str) -> JudgeVerdict | None:
    """Extract and schema-validate the judge's JSON verdict. Returns None if the
    text has no valid verdict object (caller then fails open)."""
    if not raw:
        return None
    match = _JSON_OBJECT_RE.search(raw)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except (ValueError, TypeError):
        return None

    schema_check = validate_judge_output(data)
    if not schema_check.passed:
        return None

    score = float(data["accuracy_score"])
    verdict = data["verdict"]
    reason = data.get("reason", "")
    # Trust the numeric score as the source of truth; the verdict string is a
    # convenience field the model can get inconsistent with.
    passed = score >= JUDGE_ACCEPT_SCORE and verdict == "pass"
    return JudgeVerdict(passed=passed, score=score, reason=reason)


async def run_judge(user_message: str, assistant_reply: str, api_key: str) -> JudgeVerdict:
    """Evaluate `assistant_reply` against `user_message`.

    Returns a passing verdict (score=None) when the judge is disabled or the call
    fails — the deterministic guardrails remain the hard gate; the judge is an
    additional, best-effort accuracy check.
    """
    if not judge_enabled():
        return JudgeVerdict(True, None, "Judge disabled.")

    try:
        model = llm.get_chat_model(api_key)
        response = await model.ainvoke(
            [
                SystemMessage(content=JUDGE_SYSTEM_PROMPT),
                HumanMessage(content=build_judge_prompt(user_message, assistant_reply)),
            ]
        )
        verdict = _parse_verdict(getattr(response, "content", "") or "")
        if verdict is None:
            return JudgeVerdict(True, None, "Judge returned no parseable verdict; passing open.")
        return verdict
    except Exception as e:  # pragma: no cover - defensive: judge never blocks on error
        print(f"[JUDGE] evaluation failed, passing open: {e}")
        return JudgeVerdict(True, None, f"Judge error: {e}")
