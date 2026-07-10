import datetime

from fastapi import APIRouter, Depends, HTTPException
from openai import AsyncOpenAI

from app.clients import get_current_user_id, get_google_calendar_service, get_groq_client, supabase

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
                    schedule_data.append({
                        "event": event.get("summary", ""),
                        "time": start_event.get("dateTime", "T00:00:00")[11:16],
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

        briefing_prompt = f"""
        You are the user's elite, highly competent, and warm executive assistant. You speak in a natural, human voice-highly organized, proactive, and empathetic.

        DATA STRUCTURE GUIDE:
        - `Schedule`: Contains 'event' (description) and 'time'. 'protected' means it cannot be moved.
        - `Tasks`: Contains 'title', 'deadline', and 'priority'.
        - `Emails`: Contains recent inbox items with pre-generated summaries and 'urgency' levels.

        INSTRUCTIONS:
        Formulate a brief, conversational daily briefing. Do not just output a dry bulleted list; speak directly to the user as if you are standing by their desk reviewing the day.

        1. Synthesize their schedule: Mention who they are meeting with, and explicitly flag any double-bookings or scheduling conflicts so they are aware.
        2. Gently remind them of their highest-priority tasks and explicitly mention any urgent emails that need their immediate attention.
        3. Keep your tone encouraging, supportive, and strictly under 5 sentences.
        4. Start directly with the briefing (do not use generic AI greetings like "Good morning" or "Here is your summary").

        LIVE DATABASE PAYLOAD:
        Schedule: {schedule_data}
        Pending Tasks: {tasks_res.data}
        Emails: {email_res.data}
        """

        ai_response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a proactive AI secretary."},
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
