"""Unit tests for the post-generation output guardrail (schema + tone/format)."""

from app.guardrails.output_validation import (
    validate_chat_output,
    validate_json_schema,
    validate_triage_output,
)
from app.guardrails.schemas import JUDGE_OUTPUT_SCHEMA


# --- JSON schema validation ------------------------------------------------

def test_triage_output_valid_passes():
    obj = {"priority_level": "high", "priority_score": 90, "triage_rationale": "Due soon."}
    assert validate_triage_output(obj).passed


def test_triage_output_missing_field_fails():
    obj = {"priority_level": "high", "priority_score": 90}
    verdict = validate_triage_output(obj)
    assert not verdict.passed and verdict.category == "schema_invalid"


def test_triage_output_bad_enum_fails():
    obj = {"priority_level": "CRITICAL", "priority_score": 90, "triage_rationale": "x"}
    assert not validate_triage_output(obj).passed


def test_triage_output_score_out_of_range_fails():
    obj = {"priority_level": "high", "priority_score": 150, "triage_rationale": "x"}
    assert not validate_triage_output(obj).passed


def test_triage_output_wrong_type_fails():
    obj = {"priority_level": "high", "priority_score": "ninety", "triage_rationale": "x"}
    assert not validate_triage_output(obj).passed


def test_bool_is_not_accepted_as_number():
    # bool is an int subclass in Python; the validator must reject it as a number.
    obj = {"accuracy_score": True, "verdict": "pass"}
    assert not validate_json_schema(obj, JUDGE_OUTPUT_SCHEMA).passed


# --- Chat tone / format validation -----------------------------------------

def test_clean_reply_passes():
    assert validate_chat_output("I've added your gym session for tomorrow at 6pm.").passed


def test_empty_reply_is_substantive_failure():
    verdict = validate_chat_output("")
    assert not verdict.passed
    assert verdict.category == "empty_output"
    assert verdict.sanitized is None


def test_system_prompt_leak_is_blocked_not_sanitized():
    verdict = validate_chat_output("Sure. STRICT BAN ON DATA DUMPS means I won't dump data.")
    assert not verdict.passed
    assert verdict.category == "prompt_leak"
    assert verdict.sanitized is None


def test_markdown_table_is_sanitized_in_place():
    reply = "Here is your day:\n| Time | Event |\n|------|-------|\n| 9am | Class |\nHave a good one!"
    verdict = validate_chat_output(reply)
    assert not verdict.passed
    assert verdict.category == "markdown_format"
    assert verdict.sanitized is not None
    assert "|" not in verdict.sanitized
    assert "Have a good one!" in verdict.sanitized


def test_code_fence_is_sanitized():
    reply = "Done.\n```\nsome code\n```\nAnything else?"
    verdict = validate_chat_output(reply)
    assert not verdict.passed
    assert "```" not in (verdict.sanitized or "")
