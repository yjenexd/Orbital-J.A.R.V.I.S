from typing import Any, TypedDict


class TriageState(TypedDict, total=False):
    """State for the background task-triage graph.

    Inputs are the task facts + the per-request Groq key; `score_priority`
    produces either `priority_result` (success) or `error` (LLM/parse failure),
    which the conditional edge routes to the matching persist node."""

    task_id: int
    user_id: str
    title: str
    deadline: str
    user_context: str
    x_groq_api_key: str

    priority_result: dict[str, Any]
    error: str
