"""Background task-triage as a 2-node LangGraph state machine.

Replaces the flat triage_task_background function. The LLM scoring call itself is
unchanged (raw AsyncOpenAI JSON-mode against Groq) — only the control flow is
lifted into an explicit score -> (persist_result | persist_fallback) graph, which
is what gives triage a real, testable state schema. Invoked fire-and-forget via
FastAPI BackgroundTasks; the frontend polls /tasks to pick up the new score."""

import json

from openai import AsyncOpenAI

from app.clients import supabase
from app.config import CURR_DATE
from app.graph.triage_state import TriageState

try:  # LangGraph is a hard dep, but keep imports grouped/obvious.
    from langgraph.graph import END, START, StateGraph
except Exception:  # pragma: no cover
    raise


_LEVEL_MAP = {"critical": "high", "high": "high", "medium": "medium", "low": "low"}


def _build_triage_prompt(title: str, deadline: str, user_context: str) -> str:
    return f"""
    You are J.A.R.V.I.S's background task triage engine. Evaluate this task and output a JSON object scoring its priority.

    Task Title: {title}
    Deadline: {deadline}
    Current Date: {CURR_DATE.isoformat()}
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


async def score_priority(state: TriageState) -> dict:
    """LLM scoring call. On success -> priority_result; on any failure -> error."""
    client = AsyncOpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=state["x_groq_api_key"],
    )
    triage_prompt = _build_triage_prompt(
        state["title"], state["deadline"], state.get("user_context", "")
    )

    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": triage_prompt}],
            response_format={"type": "json_object"},
        )
        ai_data = json.loads(response.choices[0].message.content)
        level_raw = ai_data.get("priority_level", "medium").lower()
        priority_level = _LEVEL_MAP.get(level_raw, "medium")

        return {
            "priority_result": {
                "priority": priority_level,
                "priority_score": ai_data.get("priority_score", 50),
                "triage_rationale": ai_data.get(
                    "triage_rationale", "..pending review by AI triage engine.."
                ),
            }
        }
    except Exception as e:
        print(f"Triage failed for task {state['task_id']}: {str(e)}")
        return {"error": str(e)}
    finally:
        await client.close()


def persist_result(state: TriageState) -> dict:
    """Write the AI-scored priority back to the task row."""
    supabase.table("tasks").update(state["priority_result"]).eq(
        "task_id", state["task_id"]
    ).eq("user_id", state["user_id"]).execute()
    return {}


def persist_fallback(state: TriageState) -> dict:
    """AI triage failed — apply neutral standard sorting so the task is still ranked."""
    supabase.table("tasks").update(
        {
            "priority_score": 50,
            "triage_rationale": "Standard sorting applied (AI Triage offline).",
        }
    ).eq("task_id", state["task_id"]).execute()
    return {}


def _route_after_score(state: TriageState) -> str:
    return "success" if state.get("priority_result") else "fallback"


def build_triage_graph():
    graph = StateGraph(TriageState)
    graph.add_node("score_priority", score_priority)
    graph.add_node("persist_result", persist_result)
    graph.add_node("persist_fallback", persist_fallback)

    graph.add_edge(START, "score_priority")
    graph.add_conditional_edges(
        "score_priority",
        _route_after_score,
        {"success": "persist_result", "fallback": "persist_fallback"},
    )
    graph.add_edge("persist_result", END)
    graph.add_edge("persist_fallback", END)
    return graph.compile()


triage_graph = build_triage_graph()


async def run_triage_graph(
    task_id: int,
    user_id: str,
    title: str,
    deadline: str,
    x_groq_api_key: str,
    user_context: str = "",
):
    """Drop-in replacement for the old triage_task_background: same signature, so
    the tool_handlers BackgroundTasks call site only swaps the import."""
    if not x_groq_api_key:
        print("API_KEY_MISSING: Cannot perform triage without a valid API key.")
        return

    await triage_graph.ainvoke(
        {
            "task_id": task_id,
            "user_id": user_id,
            "title": title,
            "deadline": deadline,
            "user_context": user_context,
            "x_groq_api_key": x_groq_api_key,
        }
    )
