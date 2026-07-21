import datetime

from fastapi import APIRouter, Depends, HTTPException
from openai import AsyncOpenAI

from app.clients import get_current_user_id, get_google_calendar_service, get_groq_client, supabase
from app.guardrails import redact_rows
from app.prompts import BRIEFING_SYSTEM_PROMPT, build_briefing_prompt

router = APIRouter()


@router.get("/api/briefing")
async def day_at_a_glance_briefing(
    client: AsyncOpenAI = Depends(get_groq_client),
    user_id: str = Depends(get_current_user_id),
):
    try:
        sample_date = datetime.date.today().isoformat()

        # Fetch today's schedule from Google Calendar
        schedule_data = []
        try:
            _result = (
                supabase.table("users")
                .select("name, google_refresh_token")
                .eq("id", user_id)
                .maybe_single()
                .execute()
            )
            user_row = _result.data if _result else None
            refresh_token = user_row.get("google_refresh_token") if user_row else None
            if refresh_token:
                gcal_service = get_google_calendar_service(refresh_token)
                gcal_result = gcal_service.events().list(
                    calendarId="primary",
                    maxResults=20,
                    singleEvents=True,
                    orderBy="startTime",
                    timeMin=f"{sample_date}T00:00:00+08:00",
                    timeMax=f"{sample_date}T23:59:59+08:00",
                ).execute()
                for event in gcal_result.get("items", []):
                    start_event = event.get("start", {})
                    end_event = event.get("end", {})
                    schedule_data.append({
                        "event": event.get("summary", ""),
                        "start_time": start_event.get("dateTime", "T00:00:00")[11:16],
                        "end_time": end_event.get("dateTime", "T00:00:00")[11:16],
                    })
        except Exception as e:
            print(f"[BRIEFING] GCal fetch failed: {e}")

        tasks_res = (
            supabase.table("tasks")
            .select("task_id, title, priority, deadline, source")
            .eq("completed", False)
            .eq("user_id", user_id)
            .execute()
        )

        email_res = (
            supabase.table("email")
            .select("email_id, sender, subject, summary, urgency")
            .eq("user_id", user_id)
            .limit(5)
            .execute()
        )

        if not schedule_data and not tasks_res.data and not email_res.data:
            return {
                "briefing": "You have no scheduled events, pending tasks, or urgent emails for today. Enjoy your day!",
                "has_events": False,
            }

        # Screen third-party content (event titles, task titles, and — the
        # highest-risk channel — email sender/subject/summary) for injection
        # payloads before it enters the briefing prompt.
        safe_schedule = redact_rows(schedule_data, "event")
        safe_tasks = redact_rows(tasks_res.data, "title")
        safe_emails = redact_rows(email_res.data, "sender", "subject", "summary")

        briefing_prompt = build_briefing_prompt(safe_schedule, safe_tasks, safe_emails)

        ai_response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": BRIEFING_SYSTEM_PROMPT},
                {"role": "user", "content": briefing_prompt},
            ],
        )

        briefing_text = ai_response.choices[0].message.content
        return {"briefing": briefing_text, "has_events": True}

    except Exception as e:
        print(f"Error generating briefing: {str(e)}")

        if isinstance(e, HTTPException):
            raise e

        raise HTTPException(status_code=500, detail="failed to initialize summary")
