import datetime

from fastapi import APIRouter, Depends, HTTPException
from openai import AsyncOpenAI

from app.clients import get_groq_client, supabase
from app.config import USER_ID


router = APIRouter()


@router.get("/api/briefing")
async def day_at_a_glance_briefing(client: AsyncOpenAI = Depends(get_groq_client)):
    try:
        current_user_id = USER_ID
        sample_date = datetime.date.today().isoformat()

        schedule_res = (
            supabase.table("schedule")
            .select("event_id, date, time, event, protected, users(name)")
            .eq("date", sample_date)
            .eq("user_id", current_user_id)
            .execute()
        )

        tasks_res = (
            supabase.table("tasks")
            .select("task_id, title, priority, deadline, source")
            .eq("completed", False)
            .eq("user_id", current_user_id)
            .execute()
        )

        email_res = (
            supabase.table("email")
            .select("email_id, sender, subject, summary, urgency")
            .eq("user_id", current_user_id)
            .limit(5)
            .execute()
        )

        if not schedule_res.data and not tasks_res.data and not email_res.data:
            return {
                "briefing": "You have no scheduled events, pending tasks, or urgent emails for today. Enjoy your day!",
                "has_events": False,
            }

        briefing_prompt = f"""
        You are the user's elite, highly competent, and warm executive assistant. You speak in a natural, human voice-highly organized, proactive, and empathetic.

        DATA STRUCTURE GUIDE:
        - `Schedule`: Contains 'event' (description), 'time', and a relational 'users' array (who they are meeting with). 'protected' means it cannot be moved.
        - `Tasks`: Contains 'title', 'deadline', and 'priority'.
        - `Emails`: Contains recent inbox items with pre-generated summaries and 'urgency' levels.

        INSTRUCTIONS:
        Formulate a brief, conversational daily briefing. Do not just output a dry bulleted list; speak directly to the user as if you are standing by their desk reviewing the day.

        1. Synthesize their schedule: Mention who they are meeting with, and explicitly flag any double-bookings or scheduling conflicts so they are aware.
        2. Gently remind them of their highest-priority tasks and explicitly mention any urgent emails that need their immediate attention.
        3. Keep your tone encouraging, supportive, and strictly under 5 sentences.
        4. Start directly with the briefing (do not use generic AI greetings like "Good morning" or "Here is your summary").

        LIVE DATABASE PAYLOAD:
        Schedule: {schedule_res.data}
        Pending Tasks: {tasks_res.data}
        Emails: {email_res.data}
        """

        ai_response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
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
