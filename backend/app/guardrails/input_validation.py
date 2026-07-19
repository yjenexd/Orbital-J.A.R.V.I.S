"""Pre-generation guardrail: injection defence + malformed-input rejection.

Deterministic and dependency-free (regex only) so it is fast, offline, and
trivially testable against an adversarial dataset. This runs on the raw user
message BEFORE it is ever composed into a prompt or handed to the model.

The goal is not perfect NLP — it is a high-precision signature filter for the
well-known prompt-injection / instruction-override / prompt-exfiltration
families, tuned to avoid firing on ordinary scheduling requests.
"""

from __future__ import annotations

import re

from app.guardrails.config import MAX_INPUT_CHARS
from app.guardrails.schemas import GuardrailVerdict


# Each pattern targets a known injection family. Kept narrow (anchored verbs +
# objects) so legitimate messages like "change my meeting" don't match.
_INJECTION_PATTERNS: list[tuple[str, re.Pattern]] = [
    (
        "instruction_override",
        re.compile(
            r"\b(ignore|disregard|forget|override|bypass)\b[\w\s,'\"]{0,40}?\b"
            r"(instruction|instructions|rule|rules|prompt|prompts|guardrail|guardrails|"
            r"restriction|restrictions|direction|directions)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "persona_hijack",
        re.compile(
            r"\b(you\s+are\s+now|from\s+now\s+on\s+you\s+are|act\s+as|pretend\s+to\s+be|"
            r"roleplay\s+as|behave\s+as|you\s+must\s+now\s+act)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "jailbreak_alias",
        re.compile(
            r"\b(developer\s+mode|do\s+anything\s+now|\bDAN\b|jailbreak|unfiltered\s+mode|"
            r"without\s+any\s+restrictions|no\s+(limits|restrictions|rules|guardrails|filters|boundaries))\b",
            re.IGNORECASE,
        ),
    ),
    (
        "instruction_reset",
        re.compile(
            r"\b(forget|ignore|disregard)\b[\w\s,'\"]*\byou\s+were\s+"
            r"(told|instructed|given|programmed|configured|trained)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "prompt_exfiltration",
        re.compile(
            r"\b(reveal|repeat|print|show|display|leak|output|reprint)\b[\w\s,'\"]*\b"
            r"(system\s+prompt|your\s+prompt|your\s+instructions|initial\s+instructions|"
            r"the\s+prompt\s+above|your\s+rules|api\s+key|secret)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "role_delimiter_injection",
        re.compile(
            r"(<\|im_start\|>|<\|im_end\|>|<\|system\|>|\[/?INST\]|"
            r"^\s*(system|assistant|developer)\s*:)",
            re.IGNORECASE | re.MULTILINE,
        ),
    ),
    (
        "fake_instruction_block",
        re.compile(
            r"\b(new|updated|real|actual)\s+(instruction|instructions|system\s+prompt|rules)\s*:",
            re.IGNORECASE,
        ),
    ),
]


def _control_char_ratio(text: str) -> float:
    if not text:
        return 0.0
    control = sum(1 for ch in text if ord(ch) < 32 and ch not in "\n\r\t")
    return control / len(text)


def contains_injection(text: str) -> str | None:
    """Return the name of the first injection signature `text` matches, or None.

    The shared detector behind every channel that feeds the model — the live user
    message (validate_input), retrieved RAG history, and DB-derived context —
    so all three screen against one signature set that can't drift apart.
    """
    if not text:
        return None
    for category, pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            return category
    return None


def validate_input(text: str) -> GuardrailVerdict:
    """Screen a raw user message before generation.

    Returns a passing verdict for ordinary requests, or a failing verdict tagged
    with the offending category for injection attempts and malformed payloads.
    """
    if text is None:
        return GuardrailVerdict(False, "malformed_input", "Empty message.")

    stripped = text.strip()
    if not stripped:
        return GuardrailVerdict(False, "malformed_input", "Empty message.")

    if len(text) > MAX_INPUT_CHARS:
        return GuardrailVerdict(
            False,
            "malformed_input",
            f"Message exceeds {MAX_INPUT_CHARS} characters.",
        )

    if _control_char_ratio(text) > 0.10:
        return GuardrailVerdict(
            False, "malformed_input", "Message contains excessive control characters."
        )

    category = contains_injection(text)
    if category:
        return GuardrailVerdict(
            False,
            "prompt_injection",
            f"Blocked input matching {category} signature.",
        )

    return GuardrailVerdict(True, "clean", "Input passed pre-generation guardrails.")
