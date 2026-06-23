import json

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from openai import APIError, AsyncOpenAI

from app.chat.tool_definitions import TOOLS
from app.chat.tool_handlers import execute_tool_call
from app.clients import get_groq_client, supabase
from app.config import CURR_DATE, SYSTEM_PROMPT
from app.schemas import ChatRequest


router = APIRouter()


@router.post("/chat")
async def execute_chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    client: AsyncOpenAI = Depends(get_groq_client),
    x_groq_api_key: str | None = Header(default=None),
):
    user_id = request.user_id
    user_message = request.message

    try:
        supabase.table("messages").insert(
            {
                "user_id": user_id,
                "role": "user",
                "content": user_message,
            }
        ).execute()

        history_response = (
            supabase.table("messages")
            .select("message_id, role, content, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(request.history_limit)
            .execute()
        )

        sorted_history = history_response.data[::-1]

        active_tasks = (
            supabase.table("tasks")
            .select("task_id, title, priority, deadline, completed")
            .eq("user_id", user_id)
            .execute()
        )

        active_events = (
            supabase.table("schedule")
            .select("event_id, date, time, event, protected")
            .eq("user_id", user_id)
            .execute()
        )

        user_name = (
            supabase.table("users")
            .select("name")
            .eq("id", user_id)
            .single()
            .execute()
            .data.get("name", "Unknown")
        )

        db_context = f"""
        LIVE DATABASE CONTEXT (You must use these exact IDs for updates or deletions):
        Pending Tasks: {active_tasks.data}
        Calendar Events: {active_events.data}
        User's Name: {user_name}
        Current Date: {CURR_DATE.isoformat()}
        """

        messages_payload = [{"role": "system", "content": SYSTEM_PROMPT + db_context}] + [
            {"role": msg["role"], "content": msg["content"]} for msg in sorted_history
        ]

        response = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages_payload,
            tools=TOOLS,
            tool_choice="auto",
        )

        response_message = response.choices[0].message

        if response_message.tool_calls:
            messages_payload.append(response_message.model_dump(exclude_none=True))

            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                print(f" [AI TOOL CALL] -> {function_name} | Args: {function_args}")

                try:
                    function_response = execute_tool_call(
                        function_name,
                        function_args,
                        user_id,
                        user_message=user_message,
                        background_tasks=background_tasks,
                        x_groq_api_key=x_groq_api_key,
                    )
                except Exception as db_error:
                    function_response = json.dumps(
                        {"status": "error", "message": f"Database operation failed: {str(db_error)}"}
                    )
                    print(f"[DB ERROR] -> {str(db_error)}")

                messages_payload.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )

        messages_payload.append(
            {
                "role": "user",
                "content": "CRITICAL INSTRUCTION: Review the tool responses you just received. If any tool returned 'pending_confirmation' or 'pending_information', you MUST halt and ask the user for the missing input. Under NO circumstances should you hallucinate or claim an action was successful if the tool response blocked it.",
            }
        )

        second_response = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages_payload,
        )
        ai_reply = second_response.choices[0].message.content

        supabase.table("messages").insert(
            {
                "user_id": user_id,
                "role": "assistant",
                "content": ai_reply,
            }
        ).execute()

        return {"reply": ai_reply}

    except APIError as e:
        print(f"GitHub Models API returned an error: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail="Upstream provider error: Intelligence backend is currently unavailable.",
        )
    except Exception as e:
        print(f"Unexpected error in chat execution engine: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error processing the chat request.")
