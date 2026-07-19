"""Post-generation guardrail: structural (JSON schema) + tone/format checks.

Two families, both deterministic:

1. Schema validation for structured outputs (the triage engine, the judge
   verdict). A tiny dependency-free validator keeps the offline test suite free
   of a jsonschema dependency while covering the keywords we actually use.

2. Tone / format validation for conversational replies — enforces the OUTPUT
   FORMAT contract carried in the versioned chat prompt (no markdown tables, no
   code fences) and blocks system-prompt leakage. Format violations are
   sanitised in place where possible so a cosmetic slip doesn't burn a retry.
"""

from __future__ import annotations

import re

from app.guardrails.schemas import (
    JUDGE_OUTPUT_SCHEMA,
    TRIAGE_OUTPUT_SCHEMA,
    GuardrailVerdict,
)


# Fragments that should never appear in a user-facing reply — their presence
# means the model is echoing its own system instructions / injected context.
_PROMPT_LEAK_MARKERS = (
    "STRICT BAN ON",
    "CORE DIRECTIVES",
    "OUTPUT FORMAT:",
    "LIVE DATABASE CONTEXT",
    "TEMPORAL ANCHOR",
    "OPERATIONAL MODES",
    "You are J.a.r.v.i.s",
)

_MARKDOWN_TABLE_RE = re.compile(r"^\s*\|?[\s:-]*\|[\s:|-]*$", re.MULTILINE)
_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$", re.MULTILINE)
_CODE_FENCE_RE = re.compile(r"```")


# ---------------------------------------------------------------------------
# JSON schema validation (dependency-free subset)
# ---------------------------------------------------------------------------

_JSON_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
}


def _type_matches(value, json_type: str) -> bool:
    expected = _JSON_TYPES[json_type]
    if json_type == "number":
        # bool is a subclass of int in Python — exclude it from "number".
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if json_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, expected)


def validate_json_schema(obj, schema: dict) -> GuardrailVerdict:
    """Validate `obj` against the supported subset of JSON-schema keywords:
    type, required, properties, enum, minimum, maximum, min_length."""
    if not _type_matches(obj, schema.get("type", "object")):
        return GuardrailVerdict(
            False, "schema_invalid", f"Expected {schema.get('type')} at root."
        )

    if schema.get("type") == "object":
        for key in schema.get("required", []):
            if key not in obj:
                return GuardrailVerdict(
                    False, "schema_invalid", f"Missing required field '{key}'."
                )
        for key, subschema in schema.get("properties", {}).items():
            if key not in obj:
                continue
            value = obj[key]
            sub_type = subschema.get("type")
            if sub_type and not _type_matches(value, sub_type):
                return GuardrailVerdict(
                    False, "schema_invalid", f"Field '{key}' must be {sub_type}."
                )
            if "enum" in subschema and value not in subschema["enum"]:
                return GuardrailVerdict(
                    False,
                    "schema_invalid",
                    f"Field '{key}'='{value}' not in {subschema['enum']}.",
                )
            if "minimum" in subschema and value < subschema["minimum"]:
                return GuardrailVerdict(
                    False, "schema_invalid", f"Field '{key}' below minimum."
                )
            if "maximum" in subschema and value > subschema["maximum"]:
                return GuardrailVerdict(
                    False, "schema_invalid", f"Field '{key}' above maximum."
                )
            if "min_length" in subschema and len(value) < subschema["min_length"]:
                return GuardrailVerdict(
                    False, "schema_invalid", f"Field '{key}' too short."
                )

    return GuardrailVerdict(True, "clean", "Output matches schema.")


def validate_triage_output(obj) -> GuardrailVerdict:
    return validate_json_schema(obj, TRIAGE_OUTPUT_SCHEMA)


def validate_judge_output(obj) -> GuardrailVerdict:
    return validate_json_schema(obj, JUDGE_OUTPUT_SCHEMA)


# ---------------------------------------------------------------------------
# Tone / format validation for conversational replies
# ---------------------------------------------------------------------------

def validate_chat_output(text: str) -> GuardrailVerdict:
    """Enforce the conversational OUTPUT FORMAT contract on a reply.

    Returns:
    - passed=True                      : reply is clean.
    - passed=False, sanitized=<text>   : a cosmetic format violation that was
                                          repaired (caller should use `sanitized`).
    - passed=False, sanitized=None     : a substantive violation (empty reply or
                                          system-prompt leakage) — caller should
                                          retry or fall back.
    """
    if not text or not text.strip():
        return GuardrailVerdict(False, "empty_output", "Reply was empty.", None)

    for marker in _PROMPT_LEAK_MARKERS:
        if marker in text:
            return GuardrailVerdict(
                False,
                "prompt_leak",
                f"Reply leaked internal prompt content ('{marker}').",
                None,
            )

    has_table = bool(_MARKDOWN_TABLE_RE.search(text))
    has_fence = bool(_CODE_FENCE_RE.search(text))
    if has_table or has_fence:
        sanitized = _strip_markdown(text)
        if sanitized.strip():
            reason = "Removed markdown formatting banned in conversational replies."
            return GuardrailVerdict(False, "markdown_format", reason, sanitized)
        # Nothing left after stripping — not a cosmetic fix, force a retry.
        return GuardrailVerdict(False, "markdown_format", "Reply was only markdown.", None)

    return GuardrailVerdict(True, "clean", "Reply passed tone/format checks.")


def _strip_markdown(text: str) -> str:
    """Remove markdown table rows and code fences, collapsing leftover blank lines."""
    without_tables = "\n".join(
        line
        for line in text.splitlines()
        if not _TABLE_ROW_RE.match(line) and not _MARKDOWN_TABLE_RE.match(line)
    )
    without_fences = _CODE_FENCE_RE.sub("", without_tables)
    collapsed = re.sub(r"\n{3,}", "\n\n", without_fences)
    return collapsed.strip()
