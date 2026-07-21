"""LLM-as-a-judge evaluation prompt.

Consumed by app.guardrails.judge. The judge rates a candidate reply for accuracy
and alignment with the user's request and MUST return the strict JSON shape below
so the post-generation schema guardrail can parse its verdict deterministically.

CHANGELOG
- 1.0.0  Initial judge rubric: 0.0-1.0 accuracy score + pass/fail verdict + reason.
"""

from app.prompts.registry import PromptSpec, register


JUDGE_PROMPT_VERSION = "1.0.0"


JUDGE_SYSTEM_PROMPT = (
    "You are a strict quality-control judge for an AI scheduling assistant. "
    "You evaluate whether the assistant's reply is accurate, grounded, and "
    "responsive to the user's request. You never rewrite the reply — you only "
    "score it. You always answer with a single JSON object and nothing else."
)


def build_judge_prompt(user_message: str, assistant_reply: str) -> str:
    """Render the judge user prompt. The judge scores `assistant_reply` against
    `user_message` on accuracy and alignment."""
    return f"""
Evaluate the assistant's reply below.

USER REQUEST:
{user_message}

ASSISTANT REPLY:
{assistant_reply}

SCORING RUBRIC (accuracy_score, 0.0 to 1.0):
- 1.0  Fully accurate, grounded, and directly responsive. Invents nothing.
- 0.7  Mostly correct and responsive; minor vagueness.
- 0.4  Partially off: unresponsive, hedged, or lightly speculative.
- 0.0  Hallucinated, fabricated details, contradicts the request, or claims an
       action succeeded without evidence.

A reply that fabricates events, tasks, dates, or people not present in the user
request MUST score at or below 0.3.

Return EXACTLY this JSON object and nothing else:
{{
    "accuracy_score": 0.9,
    "verdict": "pass",
    "reason": "One short sentence explaining the score."
}}
verdict MUST be "pass" or "fail".
"""


register(
    PromptSpec(
        id="judge.accuracy",
        version=JUDGE_PROMPT_VERSION,
        description="LLM-as-a-judge accuracy/alignment scorer with strict JSON output.",
        changelog=["1.0.0 initial accuracy rubric + JSON verdict contract"],
        text=None,
    )
)
