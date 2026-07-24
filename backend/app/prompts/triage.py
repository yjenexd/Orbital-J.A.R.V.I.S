"""Background task-triage prompt (structured JSON scoring).

Consumed by app.graph.triage_graph. The model MUST return the exact JSON shape
below; the strict output contract here is what the post-generation schema
guardrail validates.

CHANGELOG
- 1.0.0  Initial triage rubric (CRITICAL/HIGH/MEDIUM/LOW score bands + JSON out).
- 1.1.0  Extracted from triage_graph into the versioned prompts package; no text
         change to the scoring rubric or output schema.
"""

from app.prompts.registry import PromptSpec, register


TRIAGE_PROMPT_VERSION = "1.1.0"


def build_triage_prompt(title: str, deadline: str, user_context: str, current_date: str) -> str:
    """Render the triage scoring prompt. `current_date` is injected (ISO date str)
    rather than read from a module global so the prompt stays a pure function and
    is trivially testable."""
    return f"""
    You are J.A.R.V.I.S's background task triage engine. Evaluate this task and output a JSON object scoring its priority.

    Task Title: {title}
    Deadline: {deadline}
    Current Date: {current_date}
    User Update Notes: '{user_context if user_context else "None"}'

    EVALUATION CRITERIA:
    Assess this based on a rigorous Computer Science workload.
    - CRITICAL (Score 90-100): Overdue items, Orbital project deployments, major CS assignments, or Secondary 4 national exam prep due within 48 hours.
    - HIGH (Score 75-89): Standard assignments or important errands due within 3 days.
    - MEDIUM (Score 50-74): Routine maintenance (e.g., aquarium water changes, general studying) due within 4-7 days.
    - LOW (Score 10-49): Distant deadlines (>7 days), minor personal errands, or hobby-related tasks.
    * Adjust upwards by 15 points if the user notes explicitly state it is important, capping at 100.

    Return EXACTLY this JSON format and nothing else. priority_level MUST be one of: "low", "medium", "high" — never "CRITICAL":
    {{
        "priority_level": "high",
        "priority_score": 85,
        "triage_rationale": "One short sentence explaining why."
    }}
    """


register(
    PromptSpec(
        id="triage.score",
        version=TRIAGE_PROMPT_VERSION,
        description="Background task-priority scoring rubric with strict JSON output.",
        changelog=[
            "1.0.0 initial rubric + JSON output contract",
            "1.1.0 moved into versioned prompts package (no rubric change)",
        ],
        text=None,
    )
)
