"""Shared redaction for untrusted content that flows into an LLM prompt.

Every place that folds stored or third-party data (task titles, calendar event
summaries, email sender/subject/body, retrieved history) into a prompt should
route it through here, so the injection-signature screening is applied uniformly
at each untrusted-content -> LLM boundary rather than re-implemented per call site.

Note (known limitation): this is signature-based, high-precision screening, not a
general prompt-injection solver. A paraphrased or novel instruction that matches
no signature will pass through; delimiting the block as data (done at the call
sites) is the remaining backstop. See app.guardrails.input_validation.
"""

from __future__ import annotations

from app.guardrails.config import REDACTED_CONTEXT
from app.guardrails.input_validation import contains_injection


def screen_text(value) -> str:
    """Return REDACTED_CONTEXT if `value` trips an injection signature, else the
    value coerced to str. Safe on None/non-str input."""
    text = "" if value is None else str(value)
    return REDACTED_CONTEXT if contains_injection(text) else text


def redact_rows(rows: list[dict] | None, *fields: str) -> list[dict]:
    """Return a copy of `rows` with each named field redacted in any row whose
    value for that field trips an injection signature. The rest of the row
    (notably its ID) is preserved so the model can still act on the item."""
    safe: list[dict] = []
    for row in rows or []:
        redacted = None
        for field in fields:
            if field in row and contains_injection(str(row.get(field, ""))):
                redacted = redacted if redacted is not None else dict(row)
                redacted[field] = REDACTED_CONTEXT
        safe.append(redacted if redacted is not None else row)
    return safe
