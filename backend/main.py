from datetime import date, datetime, timezone
import json
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from openai import AsyncOpenAI, APIError # NEW: Importing OpenAI
from supabase import create_client, Client
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

#temporary hardcoded user_id and date for testing purposes, will replace with dynamic auth and real-time date later
user_id = 1
curr_date = date(2026, 5, 19)

def _get_required_env_var(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

SUPABASE_URL = _get_required_env_var("SUPABASE_URL")
SUPABASE_KEY = _get_required_env_var("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_google_calendar_service():
    creds = Credentials(
        token=None,
        refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token"
    )
    return build("calendar", "v3", credentials=creds)

#  Configure the client to point to GitHub Models instead of standard OpenAI
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
def get_tasks():
    try:
        data = supabase.table("tasks") \
            .select("task_id, title, priority, source, deadline, completed") \
            .eq("user_id", user_id) \
            .order("deadline", desc=False) \
            .execute().data
        return {"tasks": data}
    except Exception as e:
        print(f"Tasks Error: {str(e)}") # Add this line!
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/schedule")
def get_schedule():
    try:
        data = supabase.table("schedule") \
            .select("event_id, date, time, event, protected") \
            .eq("user_id", user_id) \
            .eq("date", curr_date.isoformat()) \
            .order("date", desc=False) \
            .order("time", desc=False) \
            .execute().data
        return {"schedule": data}
    except Exception as e:
        print(f"Schedule Error: {str(e)}") # Add this line!
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/calendar")
def get_calendar(time_min: str = Query(default=None), time_max: str = Query(default=None)):
    try:
        service = get_google_calendar_service()
        
        # If no time_min provided, default to current month start
        if not time_min:
            month_start = curr_date.replace(day=1).isoformat() + "T00:00:00+08:00"
            if curr_date.month == 12:
                month_end = curr_date.replace(year=curr_date.year + 1, month=1, day=1).isoformat() + "T00:00:00+08:00"
            else:
                month_end = curr_date.replace(month=curr_date.month + 1, day=1).isoformat() + "T00:00:00+08:00"
        else:
            month_start = time_min
            month_end = time_max

        result = service.events().list(
            calendarId="primary",
            maxResults=100,
            singleEvents=True,
            orderBy="startTime",
            timeMin=month_start,
            timeMax=month_end
        ).execute()

        events = []
        for e in result.get("items", []):
            start_e = e.get("start", {})
            extended = e.get("extendedProperties", {}).get("private", {})
            events.append({
                "event_id": e["id"],
                "event": e.get("summary", ""),
                "date": start_e.get("dateTime", start_e.get("date", ""))[:10],
                "time": start_e.get("dateTime", "T00:00:00")[11:19],
                "protected": extended.get("protected", "false") == "true"
            })

        return {"schedule": events}
    except Exception as e:
        print(f"Google Calendar Error: {str(e)}") # This will print the actual error to your terminal!
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

##CHAT INTERFACE (check out tool calling documentation: OPENAI developers)

tools = [
    {
        "type": "function",
        "function": {
            "name": "add_task",
            "description": (
                f"Add a new pending task to the user's database. Use this when the user that they have a new task to complete, "
                f"such as an assignment, project, or personal errand. If the user does not specify a priority, default to 'medium'. "
                f"You should only call this function when the user explicitly states they have a new task to add, or if they provide "
                f"details about a task that is not already in the database. Do not use this function to update existing tasks; "
                f"use update_task for that purpose."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The name or description of the task."
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "The urgency of the task. Default to 'medium' if not specified."
                    },
                    "deadline": {
                        "type": "string",
                        "description": "The deadline for the task in YYYY-MM-DD format. Pass 'none' if the user explicitly states there is no deadline."
                    }
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": (
                f"Update an existing task, such as marking it as completed or changing its priority. If you do not know the task_id, "
                f"you must fetch the user's tasks first. If task does not exist, you should not call this function; instead, "
                f"if the user is describing a new task, you should call add_task to create it in the database. "
                f"Only use update_task when you are certain the task already exists and you are modifying its status or priority."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "The unique ID of the task."
                    },
                    "completed": {
                        "type": "boolean",
                        "description": "Set to true if the user finished the task, or false if it is incomplete."
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "The updated urgency of the task."
                    },
                    "deadline": {
                        "type": "string",
                        "description": "The updated deadline for the task in YYYY-MM-DD format. Optional, but if provided, it should be a valid date string."
                    }
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": (
                f"Permanently remove a task from the database. Use only when the user explicitly asks to delete or remove it. "
                f"Upon receiving a user message that indicates they want to delete a task, "
                f"you should first confirm the task details with the user (e.g., 'Just to confirm, you want to delete the task "
                f"\"Finish AI assignment\" with a deadline of May 20th?') before calling this function. "
                f"If the user confirms, then proceed to call delete_task with the appropriate task_id. "
                f"If the user does not confirm or if there is any ambiguity about which task to delete, do not call this function "
                f"and instead ask clarifying questions to ensure you are deleting the correct task."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "The unique ID of the task to delete."
                    },
                    "user_confirmed": {
                        "type": "boolean",
                        "description": "CRITICAL: If the user is asking to delete this for the FIRST time, you MUST set this to false. ONLY set to true if you have ALREADY asked them 'Are you sure?' and they replied 'Yes'."
                    }
                },
                "required": ["task_id", "user_confirmed"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_schedule_event",
            "description": (
                f"Add a new event to the user's calendar. Use this when the user explicitly states they have a new event to add, "
                f"such as a meeting, class, or personal appointment. "
                f"If the user does not specify a time, you should ask them for clarification before calling this function, "
                f"as time is required to create a calendar event."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "The date of the event in YYYY-MM-DD format."
                    },
                    "time": {
                        "type": "string",
                        "description": "The start time of the event in HH:MM format (24-hour)."
                    },
                    "event_title": {
                        "type": "string",
                        "description": "The name or description of the event."
                    }
                },
                "required": ["date", "time", "event_title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_schedule_event",
            "description": (
                f"Update an existing calendar event (e.g., rescheduling a meeting or changing its name). "
                f"If you do not know the event_id, use check_calendar first to find it. Only use this function when you are certain "
                f"the event already exists and you are modifying its details. "
                f"If the user is describing a new event that does not exist in the calendar, you should call add_schedule_event "
                f"instead to create it in the database."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "integer",
                        "description": "The unique ID of the event to update."
                    },
                    "date": {
                        "type": "string",
                        "description": "The new date in YYYY-MM-DD format (only if it is being changed)."
                    },
                    "time": {
                        "type": "string",
                        "description": "The new time in HH:MM format (24-hour) (only if it is being changed)."
                    },
                    "event_title": {
                        "type": "string",
                        "description": "The new name or description of the event (only if it is being changed)."
                    }
                },
                "required": ["event_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_schedule_event",
            "description": (
                f"Cancel or delete an event from the calendar. If you do not know the event_id, use check_calendar first to find it. "
                f"You should first call the check_calendar function to confirm the event details with the user "
                f"(e.g., 'Just to confirm, you want to delete the event \"Project Meeting\" scheduled for May 20th at 3 PM?') "
                f"before calling this function. "
                f"If the user confirms, then proceed to call delete_schedule_event with the appropriate event_id. If the user "
                f"does not confirm or if there is any ambiguity about which event to delete, "
                f"do not call this function and instead ask clarifying questions to ensure you are deleting the correct event."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "integer",
                        "description": "The unique ID of the event to delete."
                    },
                    "user_confirmed": {
                        "type": "boolean",
                        "description": "CRITICAL: If the user is asking to delete this for the FIRST time, you MUST set this to false. ONLY set to true if you have ALREADY asked them 'Are you sure?' and they replied 'Yes'."
                    }
                },
                "required": ["event_id", "user_confirmed"]
            }
        }
    }
]

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

        ##FETCH LIVE DATABASE context 
        active_tasks = supabase.table("tasks") \
            .select("task_id, title, priority, deadline, completed") \
            .eq("user_id", user_id) \
            .execute()
        
        active_events = supabase.table("schedule") \
            .select("event_id, date, time, event, protected") \
            .eq("user_id", user_id) \
            .execute()
        
        user_name = supabase.table("users") \
                    .select("name") \
                    .eq("id", user_id) \
                    .single() \
                    .execute().data.get("name", "Unknown")
        
        db_context = f"""
        LIVE DATABASE CONTEXT (You must use these exact IDs for updates or deletions):
        Pending Tasks: {active_tasks.data}
        Calendar Events: {active_events.data}
        User's Name: {user_name}
        Current Date: {curr_date.isoformat()}
        """
            
        
        #Build the payload with the system prompt + history, send the previous messages limited to 50 for context
        messages_payload = [{"role" : "system", "content" : system_prompt + db_context }] +\
            [{"role" : msg["role"], "content" : msg["content"]} for msg in sorted_history]
        
        ##send over the message payload async, wait for response
        response = await client.chat.completions.create(
            model= "gpt-4o-mini",
            messages = messages_payload,
            tools = tools,
            tool_choice = "auto"
        )

        response_message = response.choices[0].message
        ai_reply = response_message.content

        # Intercept the tool calls
        if response_message.tool_calls:
            messages_payload.append(response_message.model_dump(exclude_none=True))

            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                function_response = json.dumps({"status": "error", "message": "Unknown function."})
                print(f" [AI TOOL CALL] -> {function_name} | Args: {function_args}")

                try:
                    ##TASK TOOL CALLS
                    ##TASK TOOL CALLS
                    if function_name == "add_task":
                        deadline_val = function_args.get("deadline")
                        
                        if not deadline_val:
                            function_response = json.dumps({
                                "status": "pending_information", 
                                "message": "SYSTEM OVERRIDE: Task creation blocked. DO NOT tell the user it was added. You MUST reply by asking: 'When is the deadline for this task?'"
                            })
                        else:
                            insert_payload = {
                                "user_id": user_id,
                                "title": function_args.get("title"),
                                "priority": function_args.get("priority", "medium")
                            }
                            
                            # Only add the deadline to the DB payload if it isn't "none"
                            if deadline_val.lower() != "none":
                                insert_payload["deadline"] = deadline_val

                            res = supabase.table("tasks").insert(insert_payload).execute()
                            function_response = json.dumps({"status": "success", "message": "Task added successfully."})
                    
                    elif function_name == "update_task":
                        update_payload = {}
                        if "completed" in function_args: update_payload["completed"] = function_args["completed"]
                        if "priority" in function_args: update_payload["priority"] = function_args["priority"]
                        if "deadline" in function_args: update_payload["deadline"] = function_args["deadline"]

                        res = supabase.table("tasks").update(update_payload)\
                            .eq("task_id", int(function_args["task_id"])) \
                            .eq("user_id", user_id).execute()
                        function_response = json.dumps({"status": "success", "message": "Task updated successfully."})

                    elif function_name == "delete_task":
                        if not function_args.get("user_confirmed"):
                            function_response = json.dumps({
                                "status": "pending_confirmation", 
                                "message": "SYSTEM OVERRIDE: Deletion blocked. DO NOT tell the user it was deleted. You MUST reply by asking the user: 'Are you sure you want to delete this task?'"
                            })
                        else:
                            res = supabase.table("tasks").delete()\
                                .eq("task_id", int(function_args["task_id"]))\
                                .eq("user_id", user_id).execute()

                            if len(res.data) == 0:
                                function_response = json.dumps({"status": "error", "message": "Deletion failed. No task found with that exact ID."})
                            else:
                                function_response = json.dumps({"status": "success", "message": "Task deleted successfully."})
                    
                    ##SCHEDULE TOOL CALLS
                    elif function_name == "add_schedule_event":
                        res = supabase.table("schedule").insert({
                            "user_id": user_id,
                            "date": function_args.get("date"),
                            "time": function_args.get("time"),
                            "event": function_args.get("event_title")
                        }).execute()
                        function_response = json.dumps({"status": "success", "message": "Event added successfully."})
                    
                    elif function_name == "update_schedule_event":
                        update_payload = {}
                        if "date" in function_args: update_payload["date"] = function_args["date"] 
                        if "time" in function_args: update_payload["time"] = function_args["time"]
                        if "event_title" in function_args: update_payload["event"] = function_args["event_title"]

                        res = supabase.table("schedule").update(update_payload)\
                            .eq("event_id", int(function_args["event_id"])) \
                            .eq("user_id", user_id).execute()
                        function_response = json.dumps({"status": "success", "message": "Event updated successfully."})

                    elif function_name == "delete_schedule_event":
                        if not function_args.get("user_confirmed"):
                            function_response = json.dumps({
                                "status": "pending_confirmation", 
                                "message": "SYSTEM OVERRIDE: Deletion blocked. DO NOT tell the user it was deleted. You MUST reply by asking the user: 'Are you sure you want to cancel this event?'"
                            })
                        else:
                            res = supabase.table("schedule").delete()\
                                .eq("event_id", int(function_args["event_id"]))\
                                .eq("user_id", user_id).execute()
                           
                            if len(res.data) == 0:
                                function_response = json.dumps({"status": "error", "message": "Deletion failed. No event found with that exact ID."})
                            else:
                                function_response = json.dumps({"status": "success", "message": "Event deleted successfully."})



                except Exception as db_error:
                    function_response = json.dumps({"status": "error", "message": f"Database operation failed: {str(db_error)}"})
                    print(f"❌ [DB ERROR] -> {str(db_error)}")
                    
                messages_payload.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response
                })
        
        # THE HAND-SLAP: Force the LLM to obey the tool response
        messages_payload.append({
            "role": "user",
            "content": "CRITICAL INSTRUCTION: Review the tool responses you just received. If any tool returned 'pending_confirmation' or 'pending_information', you MUST halt and ask the user for the missing input. Under NO circumstances should you hallucinate or claim an action was successful if the tool response blocked it."
        })

        second_response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_payload,
        )
        ai_reply = second_response.choices[0].message.content

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


