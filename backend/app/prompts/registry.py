"""Version registry for J.A.R.V.I.S core LLM prompts.

Single source of truth for prompt *metadata*. Every core prompt (chat agent,
task-triage engine, daily briefing) is registered here with a semantic version
and a changelog so prompt edits are reviewable and traceable in git rather than
buried inline at the call site.

Bump the version whenever the prompt text changes:
- PATCH: wording/typo fixes that don't change behaviour or the rule set.
- MINOR: a rule reinforced or an output-format clause added (backwards compatible).
- MAJOR: a directive removed or the model's contract with callers changed.

The `guardrails` layer (input/output validation, LLM-as-judge) reads these
specs to tag every generation with the prompt version that produced it.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PromptSpec:
    """Metadata for one versioned prompt. `text` is the rendered system prompt
    for static prompts, or None for prompts assembled by a builder function."""

    id: str
    version: str
    description: str
    changelog: list[str] = field(default_factory=list)
    text: str | None = None


PROMPT_REGISTRY: dict[str, PromptSpec] = {}


def register(spec: PromptSpec) -> PromptSpec:
    """Record a prompt spec. Raises on duplicate id so two modules can't silently
    claim the same registry key."""
    if spec.id in PROMPT_REGISTRY:
        raise ValueError(f"Duplicate prompt id in registry: {spec.id}")
    PROMPT_REGISTRY[spec.id] = spec
    return spec


def get_spec(prompt_id: str) -> PromptSpec:
    return PROMPT_REGISTRY[prompt_id]
