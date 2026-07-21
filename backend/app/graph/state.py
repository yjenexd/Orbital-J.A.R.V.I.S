from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """State for the chat graph (one /chat turn).

    Split convention (mirrors the RunnableConfig boundary):
    - ``config["configurable"]`` holds request-scoped handles known before the
      graph starts (the BYOK Groq key, FastAPI ``BackgroundTasks``).
    - This state holds the turn's identity + everything produced while the graph
      runs (context, retrieval results, the LLM response, the final reply).
    """

    # Known at invocation time.
    user_id: str
    user_message: str

    # LangChain message log for the LLM turn: the AIMessage from `agent` and the
    # ToolMessages from `tools` are appended here via the add_messages reducer.
    messages: Annotated[list, add_messages]

    # Produced during execution.
    recent_messages: list[dict]          # prior assistant turn(s) pulled from DB
    db_context: str                      # tasks/schedule/user_name block for the prompt
    gcal_service: Any                    # Google Calendar client, or None
    retrieved_docs: list[dict]           # RAG hits (empty in Phase 1 / on failure)
    retrieval_error: str | None
    current_user_message_id: Any         # message_id of the just-inserted user row
    agent_text: str                      # the LLM's text content (no-tool-call path)
    tool_statuses: list[dict]            # parsed {status, message} from each tool call
    final_reply: str                     # what we return + persist as the assistant msg

    # Guardrail / evaluator state (see app.guardrails and the chat graph nodes).
    validation_status: str               # last guardrail outcome slug (audit/trace)
    guardrail_feedback: str              # error feedback threaded back to `agent` on retry
    guardrail_route: str                 # internal routing hint set by guardrail/judge nodes
    retry_count: int                     # generate->validate->retry loops used so far
    judge_score: float | None            # LLM-judge accuracy score for this turn (or None)
