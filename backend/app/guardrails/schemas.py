"""Typed verdicts and JSON schemas shared across the guardrail nodes.

Every guardrail returns a `GuardrailVerdict` (deterministic checks) or a
`JudgeVerdict` (the LLM judge). Keeping these as small frozen dataclasses — not
bare dicts — is what lets the graph route on `verdict.passed` without stringly
comparisons scattered through the nodes.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GuardrailVerdict:
    """Outcome of a deterministic (non-LLM) guardrail check.

    passed:    True if the content is allowed through as-is.
    category:  short machine slug for the check outcome (e.g. "clean",
               "prompt_injection", "markdown_table", "schema_invalid").
    reason:    human-readable explanation for logs / retry feedback.
    sanitized: a repaired version of the content when the guardrail could fix it
               in place (e.g. stripped markdown), else None.
    """

    passed: bool
    category: str = "clean"
    reason: str = ""
    sanitized: str | None = None


@dataclass(frozen=True)
class JudgeVerdict:
    """Outcome of the LLM-as-a-judge accuracy evaluation.

    passed:  True if score >= the accept threshold (or the judge is disabled).
    score:   accuracy in [0.0, 1.0], or None when the judge did not run.
    reason:  the judge's one-line justification (or why it was skipped).
    """

    passed: bool
    score: float | None
    reason: str = ""


# JSON schema (lightweight, dependency-free) for the task-triage engine output.
# Validated by app.guardrails.output_validation.validate_triage_output.
TRIAGE_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["priority_level", "priority_score", "triage_rationale"],
    "properties": {
        "priority_level": {"type": "string", "enum": ["low", "medium", "high"]},
        "priority_score": {"type": "number", "minimum": 0, "maximum": 100},
        "triage_rationale": {"type": "string", "min_length": 1},
    },
}


# JSON schema for the LLM judge's verdict object.
JUDGE_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["accuracy_score", "verdict"],
    "properties": {
        "accuracy_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "verdict": {"type": "string", "enum": ["pass", "fail"]},
        "reason": {"type": "string"},
    },
}
