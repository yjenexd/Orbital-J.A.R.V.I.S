import json

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from openai import APIError, AsyncOpenAI

from app.chat.tool_definitions import TOOLS
from app.chat.tool_handlers import execute_tool_call
from app.clients import get_google_calendar_service, get_groq_client, supabase
from datetime import date

from app.config import SYSTEM_PROMPT
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

        user_row = (
            supabase.table("users")
            .select("name, google_refresh_token")
            .eq("id", user_id)
            .single()
            .execute()
            .data
        )
        user_name = user_row.get("name", "Unknown")

        gcal_service = None
        active_events_data = []
        google_refresh_token = user_row.get("google_refresh_token")
        if google_refresh_token:
            try:
                gcal_service = get_google_calendar_service(google_refresh_token)
                print("[GCAL] Service ready.")
                today = date.today()
                time_min = today.isoformat() + "T00:00:00+08:00"
                if today.month == 12:
                    time_max = today.replace(year=today.year + 1, month=1, day=1).isoformat() + "T00:00:00+08:00"
                else:
                    time_max = today.replace(month=today.month + 1, day=1).isoformat() + "T00:00:00+08:00"
                gcal_result = gcal_service.events().list(
                    calendarId="primary",
                    maxResults=50,
                    singleEvents=True,
                    orderBy="startTime",
                    timeMin=time_min,
                    timeMax=time_max,
                ).execute()
                for event in gcal_result.get("items", []):
                    start_event = event.get("start", {})
                    extended = event.get("extendedProperties", {}).get("private", {})
                    active_events_data.append({
                        "event_id": event["id"],
                        "event": event.get("summary", ""),
                        "date": start_event.get("dateTime", start_event.get("date", ""))[:10],
                        "time": start_event.get("dateTime", "T00:00:00")[11:19],
                        "protected": extended.get("protected", "false") == "true",
                    })
            except Exception as e:
                print(f"[GCAL] Failed to build service or fetch events: {e}")
        else:
            print("[GCAL] No refresh token found for user — GCal sync disabled.")

        db_context = f"""
        LIVE DATABASE CONTEXT (You must use these exact IDs for updates or deletions):
        Pending Tasks: {active_tasks.data}
        Calendar Events: {active_events_data}
        User's Name: {user_name}
        Current Date: {date.today().isoformat()}
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
                        gcal_service=gcal_service,
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
