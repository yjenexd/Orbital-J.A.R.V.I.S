import re
from datetime import date

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from app.chat.tool_definitions import TOOLS
from app.clients import get_google_calendar_service, supabase
from app.prompts import CHAT_SYSTEM_PROMPT
from app.graph import llm
from app.graph.state import AgentState
from app.graph.tools_adapter import tools_node
from app.guardrails import judge as judge_module
from app.guardrails.config import (
    GENERATION_FALLBACK,
    INJECTION_REFUSAL,
    MALFORMED_INPUT_REFUSAL,
    MAX_RETRIES,
    judge_enabled,
)
from app.guardrails.input_validation import validate_input
from app.guardrails.output_validation import validate_chat_output
from app.rag.embedder import embed_text, embeddings_enabled
from app.rag.retriever import retrieve_relevant_messages


def _embed_or_none(text: str):
    """Best-effort embedding for embed-on-insert. Returns None (→ row stored with
    a NULL embedding, which match_messages filters out) when RAG is disabled or
    embedding fails — never blocks the write."""
    if not embeddings_enabled():
        return None
    try:
        return embed_text(text)
    except Exception as e:
        print(f"[RAG] embed-on-insert failed, storing without embedding: {e}")
        return None


# ---------------------------------------------------------------------------
# Helpers ported verbatim from the pre-migration routes/chat.py
# ---------------------------------------------------------------------------

_DATE_QUESTION_RE = re.compile(r"(what\s+is\s+)?(the\s+)?date(\s+today)?\??")
_DATE_QUESTION_LITERALS = {
    "what is the date today",
    "what's the date today",
    "today's date",
    "date today",
}

_CASUAL_INPUTS = {
    "hi", "hello", "hey", "yo", "sup", "ok", "okay", "ping", "test", "testing",
}


def _extract_user_facing_prompt(tool_message: str) -> str:
    if not tool_message:
        return "I need a quick clarification before I continue."

    ask_patterns = [
        r"You MUST reply by asking:\s*'([^']+)'",
        r"You MUST reply by asking the user:\s*'([^']+)'",
    ]
    for pattern in ask_patterns:
        match = re.search(pattern, tool_message)
        if match:
            return match.group(1)
    return tool_message


def _is_non_action_message(message: str) -> bool:
    cleaned = re.sub(r"[^a-z0-9\s]", "", (message or "").strip().lower())
    if not cleaned:
        return True
    if re.fullmatch(r"test(ing)?(\s+\d+)?", cleaned):
        return True
    return cleaned in _CASUAL_INPUTS


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def check_date_shortcut(state: AgentState) -> dict:
    """Deterministic date answer — fires before any DB write, so (unlike every
    other path) it never logs the user's message. Setting final_reply here routes
    straight to persist_reply."""
    normalized = (state["user_message"] or "").strip().lower()
    if _DATE_QUESTION_RE.fullmatch(normalized) or normalized in _DATE_QUESTION_LITERALS:
        return {"final_reply": f"Today's date is {date.today().isoformat()}."}
    return {}


def load_history_and_log_user_message(state: AgentState) -> dict:
    """Fetch the last assistant turn for context, then log the incoming user
    message. History is read before the insert so it excludes the current turn."""
    user_id = state["user_id"]

    history_result = (
        supabase.table("messages")
        .select("role, content")
        .eq("user_id", user_id)
        .eq("role", "assistant")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    recent_messages = history_result.data if history_result.data else []

    user_payload = {
        "user_id": user_id,
        "role": "user",
        "content": state["user_message"],
    }
    embedding = _embed_or_none(state["user_message"])
    if embedding is not None:
        user_payload["embedding"] = embedding

    inserted = supabase.table("messages").insert(user_payload).execute()
    current_user_message_id = None
    if inserted.data:
        current_user_message_id = inserted.data[0].get("message_id")

    return {
        "recent_messages": recent_messages,
        "current_user_message_id": current_user_message_id,
    }


def non_action_guard(state: AgentState) -> dict:
    """Block casual probes ("hi"/"ok"/"test") from ever reaching the model or a
    state-changing tool. Setting final_reply routes to persist_reply."""
    if _is_non_action_message(state["user_message"]):
        return {"final_reply": "Ready when you are. Tell me what task or event you want to manage."}
    return {}


def input_guardrail(state: AgentState) -> dict:
    """Pre-generation guardrail. Screens the raw user message for prompt
    injection / instruction-override signatures and malformed payloads BEFORE any
    prompt is composed or the model is called. A block sets a canned safe
    `final_reply`, routing straight to persist_reply (generation is skipped)."""
    verdict = validate_input(state["user_message"])
    if verdict.passed:
        return {"validation_status": "input_ok"}

    if verdict.category == "prompt_injection":
        print(f"[GUARDRAIL] input blocked: {verdict.reason}")
        return {"final_reply": INJECTION_REFUSAL, "validation_status": "input_blocked_injection"}

    print(f"[GUARDRAIL] input rejected: {verdict.reason}")
    return {"final_reply": MALFORMED_INPUT_REFUSAL, "validation_status": "input_blocked_malformed"}


def ingest_context(state: AgentState) -> dict:
    """Assemble the live DB context block (tasks + calendar + user) for the prompt,
    and build the per-user Google Calendar client into state for the tools node."""
    user_id = state["user_id"]

    active_tasks = (
        supabase.table("tasks")
        .select("task_id, title, priority, deadline, completed")
        .eq("user_id", user_id)
        .execute()
    )

    _result = (
        supabase.table("users")
        .select("name, google_refresh_token")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    user_row = _result.data if _result else None
    user_name = user_row.get("name", "Unknown") if user_row else "Unknown"

    gcal_service = None
    active_events_data: list[dict] = []
    google_refresh_token = user_row.get("google_refresh_token") if user_row else None
    if google_refresh_token:
        try:
            gcal_service = get_google_calendar_service(google_refresh_token)
            print("[GCAL] Service ready.")
            today = date.today()
            time_min = today.isoformat() + "T00:00:00+08:00"
            if today.month == 12:
                time_max = (
                    today.replace(year=today.year + 1, month=1, day=1).isoformat()
                    + "T00:00:00+08:00"
                )
            else:
                time_max = today.replace(month=today.month + 1, day=1).isoformat() + "T00:00:00+08:00"
            gcal_result = (
                gcal_service.events()
                .list(
                    calendarId="primary",
                    maxResults=50,
                    singleEvents=True,
                    orderBy="startTime",
                    timeMin=time_min,
                    timeMax=time_max,
                )
                .execute()
            )
            for event in gcal_result.get("items", []):
                start_event = event.get("start", {})
                extended = event.get("extendedProperties", {}).get("private", {})
                active_events_data.append(
                    {
                        "event_id": event["id"],
                        "event": event.get("summary", ""),
                        "date": start_event.get("dateTime", start_event.get("date", ""))[:10],
                        "time": start_event.get("dateTime", "T00:00:00")[11:19],
                        "protected": extended.get("protected", "false") == "true",
                    }
                )
        except Exception as e:
            print(f"[GCAL] Failed to build service or fetch events: {e}")
    else:
        print("[GCAL] No refresh token found for user - GCal sync disabled.")

    db_context = f"""
        LIVE DATABASE CONTEXT (You must use these exact IDs for updates or deletions):
        Pending Tasks: {active_tasks.data}
        Calendar Events: {active_events_data}
        User's Name: {user_name}
        Current Date: {date.today().isoformat()}
        TEMPORAL ANCHOR: Treat {date.today().isoformat()} as the only valid meaning of 'today', 'tonight', and 'this evening' unless the user explicitly provides another date. Ignore any conflicting date references from older conversation history.
        """

    return {"db_context": db_context, "gcal_service": gcal_service}


def retrieve(state: AgentState) -> dict:
    """RAG retrieval over the user's past messages. Excludes the just-inserted
    current message so it can't self-match. Always fails open — retrieval never
    fails the request; the agent simply proceeds without extra context."""
    if not embeddings_enabled():
        return {"retrieved_docs": [], "retrieval_error": None}
    try:
        docs = retrieve_relevant_messages(
            state["user_id"],
            state["user_message"],
            k=3,
            exclude_message_id=state.get("current_user_message_id"),
        )
        return {"retrieved_docs": docs, "retrieval_error": None}
    except Exception as e:
        print(f"[RAG] retrieve node error, continuing without context: {e}")
        return {"retrieved_docs": [], "retrieval_error": str(e)}


def _format_retrieved(docs: list[dict]) -> str:
    if not docs:
        return ""
    lines = [f"- ({d.get('role', 'msg')}) {d.get('content', '')}" for d in docs]
    return (
        "\n\nRELEVANT PAST MESSAGES (semantically retrieved; use only if helpful):\n"
        + "\n".join(lines)
    )


async def agent(state: AgentState, config: RunnableConfig) -> dict:
    """Single LLM call with tools bound. The Groq key comes from the per-request
    config, never the compiled graph."""
    api_key = config.get("configurable", {}).get("groq_api_key")
    model = llm.get_chat_model(api_key).bind_tools(TOOLS)

    system_content = CHAT_SYSTEM_PROMPT + state.get("db_context", "") + _format_retrieved(
        state.get("retrieved_docs", [])
    )

    # On a guardrail/judge retry, tell the model exactly why its last reply was
    # rejected so it can self-correct rather than repeat the violation.
    feedback = state.get("guardrail_feedback")
    if feedback:
        system_content += (
            f"\n\nREVISION REQUIRED: Your previous reply was rejected because: "
            f"{feedback}. Produce a corrected, fully compliant reply."
        )

    prompt_messages = [SystemMessage(content=system_content)]
    for msg in state.get("recent_messages", []):
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "assistant":
            prompt_messages.append(AIMessage(content=content))
        else:
            prompt_messages.append(HumanMessage(content=content))
    prompt_messages.append(HumanMessage(content=state["user_message"]))

    ai_message = await model.ainvoke(prompt_messages)
    return {"messages": [ai_message], "agent_text": ai_message.content or ""}


def synthesize_reply(state: AgentState) -> dict:
    """Derive the final reply. NO second LLM call — this deliberately breaks from
    the canonical ReAct loop to preserve the pre-migration cost/latency/UX: one
    model call per turn, with controlled (not model-generated) tool confirmations.
    Existing tests assert the second call never happens."""
    tool_statuses = state.get("tool_statuses") or []

    if not tool_statuses:
        # No tool calls this turn: reply with the model's own text.
        reply = state.get("agent_text") or "How can I help you with your schedule or tasks right now?"
        return {"final_reply": reply}

    tool_errors: list[str] = []
    pending_prompt: str | None = None
    success_messages: list[str] = []
    for result in tool_statuses:
        status = result.get("status")
        message = result.get("message", "")
        if status == "error":
            tool_errors.append(message or "Unknown tool error")
        elif status in {"pending_confirmation", "pending_information"}:
            pending_prompt = _extract_user_facing_prompt(message)
        elif status == "success" and message:
            success_messages.append(message)

    if tool_errors:
        reply = f"I couldn't complete that action: {tool_errors[0]}"
    elif pending_prompt:
        reply = pending_prompt
    elif success_messages:
        reply = success_messages[-1]
    else:
        reply = "Done."
    return {"final_reply": reply}


def output_guardrail(state: AgentState) -> dict:
    """Post-generation structural/tone guardrail. Enforces the conversational
    OUTPUT FORMAT contract on `final_reply`:

    - clean               -> pass through to the judge (text path) or persist.
    - cosmetic violation  -> sanitise in place and pass (doesn't spend a retry).
    - substantive failure -> retry generation with feedback (text path only, so
      no already-executed tool is re-run), or fall back once the retry budget is
      spent / on the tool path.
    """
    reply = state.get("final_reply", "")
    is_text_path = not (state.get("tool_statuses") or [])
    verdict = validate_chat_output(reply)

    if verdict.passed:
        return {"validation_status": "output_ok", "guardrail_route": "pass"}

    if verdict.sanitized:
        return {
            "final_reply": verdict.sanitized,
            "validation_status": f"output_sanitized:{verdict.category}",
            "guardrail_route": "pass",
        }

    retry_count = state.get("retry_count", 0)
    if is_text_path and retry_count < MAX_RETRIES:
        print(f"[GUARDRAIL] output retry ({retry_count + 1}/{MAX_RETRIES}): {verdict.reason}")
        return {
            "guardrail_feedback": verdict.reason,
            "retry_count": retry_count + 1,
            "validation_status": f"output_retry:{verdict.category}",
            "guardrail_route": "retry",
        }

    print(f"[GUARDRAIL] output fallback: {verdict.reason}")
    return {
        "final_reply": GENERATION_FALLBACK,
        "validation_status": f"output_fallback:{verdict.category}",
        "guardrail_route": "fallback",
    }


async def judge(state: AgentState, config: RunnableConfig) -> dict:
    """LLM-as-a-judge accuracy gate. Runs only on the pure-text path (tool
    confirmations are deterministic). A passing score persists the reply; a low
    score retries with feedback, or falls back once the budget is spent."""
    api_key = config.get("configurable", {}).get("groq_api_key")
    verdict = await judge_module.run_judge(
        state["user_message"], state.get("final_reply", ""), api_key
    )

    if verdict.passed:
        return {
            "judge_score": verdict.score,
            "validation_status": "judge_pass",
            "guardrail_route": "pass",
        }

    retry_count = state.get("retry_count", 0)
    if retry_count < MAX_RETRIES:
        print(f"[JUDGE] low accuracy ({verdict.score}), retry {retry_count + 1}/{MAX_RETRIES}")
        return {
            "judge_score": verdict.score,
            "guardrail_feedback": f"Low accuracy ({verdict.score}): {verdict.reason}",
            "retry_count": retry_count + 1,
            "validation_status": "judge_retry",
            "guardrail_route": "retry",
        }

    print(f"[JUDGE] low accuracy ({verdict.score}), retries exhausted -> fallback")
    return {
        "judge_score": verdict.score,
        "final_reply": GENERATION_FALLBACK,
        "validation_status": "judge_fallback",
        "guardrail_route": "fallback",
    }


def persist_reply(state: AgentState) -> dict:
    """Single consolidated assistant-message insert (replaces the 4 insert sites
    of the old route). The single place the assistant reply's embedding is
    attached."""
    assistant_payload = {
        "user_id": state["user_id"],
        "role": "assistant",
        "content": state["final_reply"],
    }
    embedding = _embed_or_none(state["final_reply"])
    if embedding is not None:
        assistant_payload["embedding"] = embedding

    supabase.table("messages").insert(assistant_payload).execute()
    return {}


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

def _route_after_date(state: AgentState) -> str:
    return "shortcut" if state.get("final_reply") else "continue"


def _route_after_guard(state: AgentState) -> str:
    return "casual" if state.get("final_reply") else "continue"


def _route_after_input_guardrail(state: AgentState) -> str:
    return "blocked" if state.get("final_reply") else "continue"


def _route_after_agent(state: AgentState) -> str:
    last_message = state["messages"][-1]
    return "tools" if getattr(last_message, "tool_calls", None) else "reply"


def _route_after_output_guardrail(state: AgentState) -> str:
    route = state.get("guardrail_route")
    if route == "retry":
        return "retry"
    # Only the pure-text path gets the (LLM) judge; tool confirmations are
    # deterministic, and re-running the model there would risk re-firing tools.
    is_text_path = not (state.get("tool_statuses") or [])
    if route == "pass" and is_text_path and judge_enabled():
        return "judge"
    return "persist"


def _route_after_judge(state: AgentState) -> str:
    return "retry" if state.get("guardrail_route") == "retry" else "persist"


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

def build_chat_graph():
    graph = StateGraph(AgentState)

    graph.add_node("check_date_shortcut", check_date_shortcut)
    graph.add_node("load_history", load_history_and_log_user_message)
    graph.add_node("non_action_guard", non_action_guard)
    graph.add_node("input_guardrail", input_guardrail)
    graph.add_node("ingest_context", ingest_context)
    graph.add_node("retrieve", retrieve)
    graph.add_node("agent", agent)
    graph.add_node("tools", tools_node)
    graph.add_node("synthesize_reply", synthesize_reply)
    graph.add_node("output_guardrail", output_guardrail)
    graph.add_node("judge", judge)
    graph.add_node("persist_reply", persist_reply)

    graph.add_edge(START, "check_date_shortcut")
    graph.add_conditional_edges(
        "check_date_shortcut",
        _route_after_date,
        {"shortcut": "persist_reply", "continue": "load_history"},
    )
    graph.add_edge("load_history", "non_action_guard")
    graph.add_conditional_edges(
        "non_action_guard",
        _route_after_guard,
        {"casual": "persist_reply", "continue": "input_guardrail"},
    )
    # Pre-generation guardrail: a block short-circuits straight to persist.
    graph.add_conditional_edges(
        "input_guardrail",
        _route_after_input_guardrail,
        {"blocked": "persist_reply", "continue": "ingest_context"},
    )
    graph.add_edge("ingest_context", "retrieve")
    graph.add_edge("retrieve", "agent")
    # Intentional: no loop-back edge from `tools` to `agent`. See synthesize_reply.
    graph.add_conditional_edges(
        "agent",
        _route_after_agent,
        {"tools": "tools", "reply": "synthesize_reply"},
    )
    graph.add_edge("tools", "synthesize_reply")
    graph.add_edge("synthesize_reply", "output_guardrail")
    # Post-generation guardrail -> (retry generation | LLM judge | persist).
    graph.add_conditional_edges(
        "output_guardrail",
        _route_after_output_guardrail,
        {"retry": "agent", "judge": "judge", "persist": "persist_reply"},
    )
    graph.add_conditional_edges(
        "judge",
        _route_after_judge,
        {"retry": "agent", "persist": "persist_reply"},
    )
    graph.add_edge("persist_reply", END)

    return graph.compile()


# Compiled once at import — safe because no per-request state (key, background
# tasks) is captured here; those flow in through RunnableConfig per invocation.
chat_graph = build_chat_graph()
