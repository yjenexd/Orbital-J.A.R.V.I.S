import json

from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig

from app.chat.tool_handlers import execute_tool_call
from app.graph.state import AgentState


def tools_node(state: AgentState, config: RunnableConfig) -> dict:
    """Execute every tool the model requested, reusing `execute_tool_call` as-is.

    We deliberately do NOT use LangGraph's prebuilt ToolNode: `execute_tool_call`
    needs request-scoped extras (background_tasks, groq key, gcal_service) that
    aren't part of the model's tool arguments. Those come from state/config here.

    Porting note: LangChain normalizes tool calls so ``tc["args"]`` is already a
    parsed dict — unlike the raw OpenAI SDK's JSON-string arguments. Do not
    json.loads it again.
    """
    configurable = config.get("configurable", {})
    last_message = state["messages"][-1]  # the AIMessage carrying tool_calls

    tool_messages: list[ToolMessage] = []
    tool_statuses: list[dict] = []

    for tool_call in last_message.tool_calls:
        function_name = tool_call["name"]
        function_args = tool_call["args"]
        print(f" [AI TOOL CALL] -> {function_name} | Args: {function_args}")

        try:
            function_response = execute_tool_call(
                function_name,
                function_args,
                state["user_id"],
                user_message=state["user_message"],
                background_tasks=configurable.get("background_tasks"),
                x_groq_api_key=configurable.get("groq_api_key"),
                gcal_service=state.get("gcal_service"),
            )
        except Exception as db_error:
            function_response = json.dumps(
                {"status": "error", "message": f"Database operation failed: {str(db_error)}"}
            )
            print(f"[DB ERROR] -> {str(db_error)}")

        tool_messages.append(
            ToolMessage(content=function_response, tool_call_id=tool_call["id"])
        )
        try:
            tool_statuses.append(json.loads(function_response))
        except Exception:
            pass

    return {"messages": tool_messages, "tool_statuses": tool_statuses}
