from fastapi import APIRouter, HTTPException, Query

from app.clients import get_google_calendar_service, supabase
from app.config import CURR_DATE, USER_ID


router = APIRouter()


@router.get("/tasks")
def get_tasks():
    try:
        data = (
            supabase.table("tasks")
            .select("task_id, title, priority, priority_score, triage_rationale, source, deadline, completed")
            .eq("user_id", USER_ID)
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
def get_schedule():
    try:
        data = (
            supabase.table("schedule")
            .select("event_id, date, time, event, protected")
            .eq("user_id", USER_ID)
            .eq("date", CURR_DATE.isoformat())
            .order("date", desc=False)
            .order("time", desc=False)
            .execute()
            .data
        )
        return {"schedule": data}
    except Exception as e:
        print(f"Schedule Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calendar")
def get_calendar(time_min: str | None = Query(default=None), time_max: str | None = Query(default=None)):
    try:
        service = get_google_calendar_service()

        if not time_min:
            month_start = CURR_DATE.replace(day=1).isoformat() + "T00:00:00+08:00"
            if CURR_DATE.month == 12:
                month_end = (
                    CURR_DATE.replace(year=CURR_DATE.year + 1, month=1, day=1).isoformat()
                    + "T00:00:00+08:00"
                )
            else:
                month_end = CURR_DATE.replace(month=CURR_DATE.month + 1, day=1).isoformat() + "T00:00:00+08:00"
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
    except Exception as e:
        print(f"Google Calendar Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/chat/history")
async def get_chat_history(user_id: str, limit: int = 5):
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
