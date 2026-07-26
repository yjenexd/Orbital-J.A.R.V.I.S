from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from google.auth.exceptions import RefreshError

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
        data = (
            supabase.table("schedule")
            .select("event_id, date, start_time, end_time, event, gcal_event_id")
            .eq("user_id", user_id)
            .eq("date", date.today().isoformat())
            .order("start_time", desc=False)
            .execute()
            .data
        )
        return {"schedule": data}
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
        _result = (
            supabase.table("users")
            .select("google_refresh_token")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
        user_row = _result.data if _result else None
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
            end_event = event.get("end", {})
            extended = event.get("extendedProperties", {}).get("private", {})
            start_dt = start_event.get("dateTime") or ""
            end_dt = end_event.get("dateTime") or ""
            events.append(
                {
                    "event_id": event["id"],
                    "event": event.get("summary", ""),
                    "date": start_event.get("dateTime", start_event.get("date", ""))[:10],
                    "start_time": start_dt[11:16] if start_dt else "",
                    "end_date": end_dt[:10] if end_dt else "",
                    "end_time": end_dt[11:16] if end_dt else "",
                }
            )

        return {"schedule": events}
    except HTTPException:
        raise
    except RefreshError as e:
        # The stored Google refresh token is expired/revoked (invalid_grant).
        # This is a reconnect-required condition, not a server fault, so surface
        # it as a clear 401 instead of an opaque 500 the UI can't act on.
        print(f"Google Calendar auth expired (reconnect required): {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Google authorization expired. Please reconnect your Google account.",
        )
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
