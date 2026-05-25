import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from openai import AsyncOpenAI, APIError # NEW: Importing OpenAI

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


class ChatRequest(BaseModel):
    message: str

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

# NEW: Configure the client to point to GitHub Models instead of standard OpenAI
client = AsyncOpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.getenv("GITHUB_TOKEN"),
)

#New route: day at a glance briefing
@app.get("/api/briefing") ##if anyone sends a GET request to this address, run the function below
async def day_at_a_glance_briefing(): ##does not pause the entire backend, function becomes "coroutine", can be paused and resumed
    mock_schedule = """
    Current Date: Friday, May 22, 2026
    Events:
    - 10:00 AM: CS2040S Revision Session
    - 2:00 PM: Orbital project sync with Jason
    Pending Tasks:
    - Finalize J.a.r.v.i.s frontend layout
    """

    briefing_prompt = f""" 
    You are J.a.r.v.i.s. Review the following schedule and tasks. 
    Formulate a brief, highly digestible cognitive system summary for the user to read upon waking up. 
    Identify any upcoming conflict blocks or critical deadlines. 
    Keep it encouraging, strictly under 4 sentences, and do not use greetings.
    
    Data:
    {mock_schedule}
    """

    try:
        response = await client.chat.completions.create(
            model= "gpt-4o-mini",
            messages=[ ##send the briefing brompt along with role to the AI
                {"role": "system", "content": "You are a proactive AI secretary."}, ##role that sets the AI persona
                {"role": "user", "content": briefing_prompt} ##users message
            ]
        )

        briefing_text: str = response.choices[0].message.content ##pick the first response, go the messages content and pluck out the string
        return {"briefing": briefing_text} #package briefing into JSON and sends it back to react
    except Exception as e:
        print(f"Error generating briefing: {str(e)}")
        raise HTTPException(status_code = 500, detail="failed to initialize summary")
    


@app.post("/chat") ##if someone sends a post request to this address, run the function below
async def chat_execution_engine(request: ChatRequest):
    try:
        # NEW: The OpenAI completion format
        response = await client.chat.completions.create(
            model="gpt-4o-mini", # Extremely fast and cost-effective for testing
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ]
        )

        # Extract text from the OpenAI response payload
        ai_reply = response.choices[0].message.content
        return {"reply": ai_reply}
    
    # NEW: OpenAI specific error handling
    except APIError as e:
        print(f"GitHub Models API returned an error: {str(e)}")
        raise HTTPException(status_code=502, detail="Upstream provider error: Intelligence backend is currently unavailable.")
    except Exception as e:
        print(f"Unexpected error in chat execution engine: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error processing the chat request.")