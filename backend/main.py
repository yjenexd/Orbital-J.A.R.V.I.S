from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from openai import AsyncOpenAI, APIError # NEW: Importing OpenAI
from supabase import create_client, Client

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

def _get_required_env_var(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

SUPABASE_URL = _get_required_env_var("SUPABASE_URL")
SUPABASE_KEY = _get_required_env_var("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# NEW: Configure the client to point to GitHub Models instead of standard OpenAI
client = AsyncOpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.getenv("GITHUB_TOKEN"),
)
class ChatRequest(BaseModel):
    user_id: int
    message: str
    history_limit: int = 10

system_prompt = """You are J.a.r.v.i.s (Reactive Virtual Intelligence System), an autonomous, highly proactive AI secretary designed to manage the academic, personal, and professional life of a busy university student. Your persona is efficient, highly capable, politely direct, and proactive.

YOUR CORE DIRECTIVES & CAPABILITIES:
1. Goal-Aligned Scheduling: Do not simply fill every empty calendar slot with project meetings. You must actively understand the user's lifestyle priorities and protect dedicated time for their personal and academic goals.
2. Proactive Conflict Resolution: When asked to schedule meetings, you must automatically identify schedule conflicts and resolve them autonomously before confirming the slot.
3. Email Triage: When interacting with Gmail data, analyze unread threads and generate concise summaries strictly between 3 to 5 sentences. 
4. Task Prioritization: Actively rank the user's pending tasks by urgency, link them directly to the calendar, and provide motivating reminders regarding upcoming deadlines.

HARD CONFLICTS & CONSTRAINTS - DO NOT BOOK:
- May 30 to June 10, 2026: Overseas in China (Shanghai, Suzhou, Beijing).
- July 6 to July 17, 2026: NUS Summer Enterprise Program.
If a user requests a meeting, internship scheduling, or task during these windows, politely decline and suggest alternative dates immediately before or after these blocks.

OPERATIONAL MODE (ROUTER AGENT):
You act as the central intelligence orchestrator. For every user input, classify the intent and formulate your response based on these workflows:
- If DASHBOARD/SUMMARY: Generate a highly readable "Day at a Glance" briefing that consolidates pending tasks, classes, and urgent emails so the user does not have to traverse multiple tabs.
- If CALENDAR: Evaluate against the Hard Conflicts above, suggest times, and prepare the tool-call payload for Google Calendar.
- If EMAIL: Extract the most urgent action items and format your 3-5 sentence summary."""



@app.get("/tasks")
async def get_tasks():
    try:
        data = supabase.table("tasks") \
            .select("title, priority, source, deadline, completed") \
            .eq("user_id", 1) \
            .order("deadline", desc=False) \
            .execute().data
        return {"tasks": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/schedule")
async def get_schedule():
    try:
        data = supabase.table("schedule") \
            .select("event_id, date, time, event, protected") \
            .eq("user_id", 1) \
            .order("date", desc=False) \
            .order("time", desc=False) \
            .execute().data
        return {"schedule": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/history")
async def get_chat_history(user_id: int, limit: int = 5):
    try:
        response = supabase.table("messages") \
            .select("message_id, role, content, created_at") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
            
        sorted_message = response.data[::-1]
        return {"messages": sorted_message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat") #only messages table queried for now
async def execute_chat(request: ChatRequest):
    user_id = request.user_id
    user_message = request.message

    try:
        #insert incoming user message
        supabase.table("messages") \
            .insert({
                "user_id": user_id,
                "role": "user",
                "content" : user_message
            }).execute()
        
        #Fetch recent conversation history for context
        history_response = supabase.table("messages")\
            .select("message_id, role, content, created_at") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .limit(request.history_limit) \
            .execute()

        sorted_history = history_response.data[::-1]
        
        #Build the payload with the system prompt + history, send the previous messages limited to 50 for context
        messages_payload = [{"role" : "system", "content" : system_prompt}] +\
            [{"role" : msg["role"], "content" : msg["content"]} for msg in sorted_history]
        
        ##send over the message payload async, wait for response
        response = await client.chat.completions.create(
            model= "gpt-4o-mini",
            messages = messages_payload
        )

        ai_reply = response.choices[0].message.content

        supabase.table("messages").insert({
            "user_id": user_id,
            "role": "assistant",
            "content": ai_reply
        }) .execute()

        return {"reply" : ai_reply}

    except APIError as e:
        print(f"GitHub Models API returned an error: {str(e)}")
        raise HTTPException(status_code=502, detail="Upstream provider error: Intelligence backend is currently unavailable.")
    except Exception as e:
        print(f"Unexpected error in chat execution engine: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error processing the chat request.")
    






#New route: day at a glance briefing
@app.get("/api/briefing") ##if anyone sends a GET request to this address, run the function below
async def day_at_a_glance_briefing(): ##does not pause the entire backend, function becomes "coroutine", can be paused and resumed
    try:
       
       # TODO: Replace hardcoded user_id with dynamic auth context later
        current_user_id = 1 
        
        # Get today's date formatted as YYYY-MM-DD to match your 'date' column type
        #today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        # TODO: # Hardcoded sample date for testing (May 19, 2026)
        sample_date = "2026-05-19"

        #Fetch Today's schedule
        schedule_res = supabase.table("schedule") \
            .select("event_id, date, time, event, protected, users(name)") \
            .eq("date", sample_date) \
            .eq("user_id", current_user_id) \
            .execute()

        # 2. Fetch Pending Tasks
        tasks_res = supabase.table("tasks") \
            .select("task_id, title, priority, deadline, source") \
            .eq("completed", False) \
            .eq("user_id", current_user_id) \
            .execute()
            
        # 3. Fetch Emails 
        email_res = supabase.table("email") \
            .select("email_id, sender, subject, summary, urgency") \
            .eq("user_id", current_user_id) \
            .limit(5) \
            .execute()
       
        if not schedule_res.data and not tasks_res.data and not email_res.data:
              return {"briefing": "You have no scheduled events, pending tasks, or urgent emails for today. Enjoy your day!",
                      "has_events": False}
   
        # Updated Prompt Engineering to handle the multi-table JSON structure
        briefing_prompt = f""" 
        You are the user's elite, highly competent, and warm executive assistant. You speak in a natural, human voice—highly organized, proactive, and empathetic. 
        
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
            model= "gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a proactive AI secretary."},
                {"role": "user", "content": briefing_prompt}
            ]
        )

        briefing_text = ai_response.choices[0].message.content
        return {"briefing": briefing_text, "has_events": True}

    except Exception as e:
        print(f"Error generating briefing: {str(e)}")
        raise HTTPException(status_code=500, detail="failed to initialize summary")

    


