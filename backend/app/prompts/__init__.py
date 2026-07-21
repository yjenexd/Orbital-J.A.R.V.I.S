"""Versioned, single-source-of-truth home for every core LLM system prompt.

Import prompts from here (never inline them at the call site) so that prompt
text, its version, and its changelog stay reviewable in git and discoverable by
the guardrails / LLM-as-judge layer.
"""

from app.prompts.briefing import (
    BRIEFING_PROMPT_VERSION,
    BRIEFING_SYSTEM_PROMPT,
    build_briefing_prompt,
)
from app.prompts.chat import CHAT_PROMPT_VERSION, CHAT_SYSTEM_PROMPT
from app.prompts.judge import (
    JUDGE_PROMPT_VERSION,
    JUDGE_SYSTEM_PROMPT,
    build_judge_prompt,
)
from app.prompts.registry import PROMPT_REGISTRY, PromptSpec, get_spec
from app.prompts.triage import TRIAGE_PROMPT_VERSION, build_triage_prompt

# Backwards-compatible alias for the historical name.
SYSTEM_PROMPT = CHAT_SYSTEM_PROMPT

__all__ = [
    "CHAT_SYSTEM_PROMPT",
    "CHAT_PROMPT_VERSION",
    "SYSTEM_PROMPT",
    "build_triage_prompt",
    "TRIAGE_PROMPT_VERSION",
    "BRIEFING_SYSTEM_PROMPT",
    "build_briefing_prompt",
    "BRIEFING_PROMPT_VERSION",
    "JUDGE_SYSTEM_PROMPT",
    "build_judge_prompt",
    "JUDGE_PROMPT_VERSION",
    "PROMPT_REGISTRY",
    "PromptSpec",
    "get_spec",
]
