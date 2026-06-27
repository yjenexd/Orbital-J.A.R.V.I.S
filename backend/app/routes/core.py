from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from app.clients import get_current_user_id, get_google_calendar_service, supabase

router = APIRouter()



@router.get("/tasks")
def get_tasks(user_id: str = Depends(get_current_user_id)):
    try:
        data = (
            supabase.table("tasks")
            .select("task_id, title, priority, priority_score, triage_rationale, source, deadline, completed")
            .eq("user_id", user_id)
            .order("completed", desc=False)
            .order("priority_score", desc=True)
            .order("deadline", desc=False)
            .execute()
            .data
        )
        return {"tasks": data}
    except Exception as e:
        print(f"Tasks Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedule")
def get_schedule(user_id: str = Depends(get_current_user_id)):
    try:
        user_row = (
            supabase.table("users")
            .select("google_refresh_token")
            .eq("id", user_id)
            .single()
            .execute()
            .data
        )
        refresh_token = user_row.get("google_refresh_token") if user_row else None
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Google account not connected.")

        service = get_google_calendar_service(refresh_token)
        today = date.today().isoformat()
        result = (
            service.events()
            .list(
                calendarId="primary",
                maxResults=50,
                singleEvents=True,
                orderBy="startTime",
                timeMin=f"{today}T00:00:00+08:00",
                timeMax=f"{today}T23:59:59+08:00",
            )
            .execute()
        )

        events = []
        for event in result.get("items", []):
            start_event = event.get("start", {})
            extended = event.get("extendedProperties", {}).get("private", {})
            events.append(
                {
                    "event_id": event["id"],
                    "event": event.get("summary", ""),
                    "date": start_event.get("dateTime", start_event.get("date", ""))[:10],
                    "time": start_event.get("dateTime", "T00:00:00")[11:19],
                    "protected": extended.get("protected", "false") == "true",
                }
            )

        return {"schedule": events}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Schedule Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calendar")
def get_calendar(
    user_id: str = Depends(get_current_user_id),
    time_min: str | None = Query(default=None),
    time_max: str | None = Query(default=None),
):
    try:
        user_row = (
            supabase.table("users")
            .select("google_refresh_token")
            .eq("id", user_id)
            .single()
            .execute()
            .data
        )
        refresh_token = user_row.get("google_refresh_token") if user_row else None
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Google account not connected.")

        service = get_google_calendar_service(refresh_token)

        if not time_min:
            today = date.today()
            month_start = today.replace(day=1).isoformat() + "T00:00:00+08:00"
            if today.month == 12:
                month_end = (
                    today.replace(year=today.year + 1, month=1, day=1).isoformat()
                    + "T00:00:00+08:00"
                )
            else:
                month_end = today.replace(month=today.month + 1, day=1).isoformat() + "T00:00:00+08:00"
        else:
            month_start = time_min
            month_end = time_max

        result = (
            service.events()
            .list(
                calendarId="primary",
                maxResults=100,
                singleEvents=True,
                orderBy="startTime",
                timeMin=month_start,
                timeMax=month_end,
            )
            .execute()
        )

        events = []
        for event in result.get("items", []):
            start_event = event.get("start", {})
            extended = event.get("extendedProperties", {}).get("private", {})
            events.append(
                {
                    "event_id": event["id"],
                    "event": event.get("summary", ""),
                    "date": start_event.get("dateTime", start_event.get("date", ""))[:10],
                    "time": start_event.get("dateTime", "T00:00:00")[11:19],
                    "protected": extended.get("protected", "false") == "true",
                }
            )

        return {"schedule": events}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Google Calendar Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/chat/history")
async def get_chat_history(user_id: str = Depends(get_current_user_id), limit: int = 5):
    try:
        response = (
            supabase.table("messages")
            .select("message_id, role, content, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        sorted_message = response.data[::-1]
        return {"messages": sorted_message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
