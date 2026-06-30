import json
from datetime import date
import re

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from openai import APIError, AsyncOpenAI

from app.chat.tool_definitions import TOOLS
from app.chat.tool_handlers import execute_tool_call
from app.clients import get_current_user_id, get_google_calendar_service, get_groq_client, supabase
from app.config import SYSTEM_PROMPT
from app.schemas import ChatRequest


router = APIRouter()


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

    casual_inputs = {
        "hi",
        "hello",
        "hey",
        "yo",
        "sup",
        "ok",
        "okay",
        "ping",
        "test",
        "testing",
    }
    return cleaned in casual_inputs


@router.post("/chat")
async def execute_chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    client: AsyncOpenAI = Depends(get_groq_client),
    authenticated_user_id: str = Depends(get_current_user_id),
    x_groq_api_key: str | None = Header(default=None),
):
    # Always trust the authenticated identity, not the client payload.
    user_id = authenticated_user_id
    user_message = request.message

    # Deterministic date/time answers prevent model drift from stale context.
    normalized_message = (user_message or "").strip().lower()
    if re.fullmatch(r"(what\s+is\s+)?(the\s+)?date(\s+today)?\??", normalized_message) or normalized_message in {
        "what is the date today",
        "what's the date today",
        "today's date",
        "date today",
    }:
        today_str = date.today().isoformat()
        ai_reply = f"Today's date is {today_str}."
        supabase.table("messages").insert(
            {
                "user_id": user_id,
                "role": "assistant",
                "content": ai_reply,
            }
        ).execute()
        return {"reply": ai_reply}

    try:
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

        supabase.table("messages").insert(
            {
                "user_id": user_id,
                "role": "user",
                "content": user_message,
            }
        ).execute()

        # Guardrail: ignore non-action probes so they cannot trigger state-changing tools.
        if _is_non_action_message(user_message):
            ai_reply = "Ready when you are. Tell me what task or event you want to manage."
            supabase.table("messages").insert(
                {
                    "user_id": user_id,
                    "role": "assistant",
                    "content": ai_reply,
                }
            ).execute()
            return {"reply": ai_reply}

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
        active_events_data = []
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

        messages_payload = [
            {"role": "system", "content": SYSTEM_PROMPT + db_context},
            *[{"role": msg["role"], "content": msg["content"]} for msg in recent_messages],
            {"role": "user", "content": user_message},
        ]

        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages_payload,
            tools=TOOLS,
            tool_choice="auto",
        )

        response_message = response.choices[0].message

        # Avoid a second model pass when no tool action is needed; this prevents
        # provider-side tool-choice errors on casual messages.
        if not response_message.tool_calls:
            ai_reply = response_message.content or "How can I help you with your schedule or tasks right now?"
            supabase.table("messages").insert(
                {
                    "user_id": user_id,
                    "role": "assistant",
                    "content": ai_reply,
                }
            ).execute()
            return {"reply": ai_reply}

        tool_errors: list[str] = []
        pending_prompt: str | None = None
        success_messages: list[str] = []

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

            try:
                tool_result = json.loads(function_response)
                status = tool_result.get("status")
                message = tool_result.get("message", "")
                if status == "error":
                    tool_errors.append(message or "Unknown tool error")
                elif status in {"pending_confirmation", "pending_information"}:
                    pending_prompt = _extract_user_facing_prompt(message)
                elif status == "success" and message:
                    success_messages.append(message)
            except Exception:
                pass

        if tool_errors:
            ai_reply = f"I couldn't complete that action: {tool_errors[0]}"
        elif pending_prompt:
            ai_reply = pending_prompt
        elif success_messages:
            ai_reply = success_messages[-1]
        else:
            ai_reply = "Done."

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
