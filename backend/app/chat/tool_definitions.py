TOOLS = [
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
                        "description": "The name or description of the task.",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "The urgency of the task. Default to 'medium' if not specified.",
                    },
                    "deadline": {
                        "type": "string",
                        "description": "The deadline for the task in YYYY-MM-DD format. Pass 'none' if the user explicitly states there is no deadline.",
                    },
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": (
                "Update an existing task. CRITICAL OVERRIDE: If the user provides vague conversational context regarding a task update"
                "(e.g., 'it is important', 'I need more time', 'update this task'), you MUST IMMEDIATELY call this function "
                "using ONLY the 'task_id' and the 'user_context' fields. "
                "DO NOT ask the user to clarify the priority level, deadline, or completion status. "
                "The background AI triage engine is explicitly designed to calculate the new priority from the 'user_context'. "
                "Only use the exact 'priority' or 'deadline' fields if the user explicitly dictates them."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "The unique ID of the task.",
                    },
                    "completed": {
                        "type": "boolean",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                    },
                    "deadline": {
                        "type": "string",
                    },
                    "user_context": {
                        "type": "string",
                        "description": "The user's exact quote or context about why the task is changing.",
                    },
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": (
                "Permanently remove a task from the database. Use only when the user explicitly asks to delete or remove a task. "
                "STEP 1 — LOOKUP: Find the task_id from the LIVE DATABASE CONTEXT (Pending Tasks list) by matching the user's description to the correct task title. "
                "STEP 2 — REQUEST CONFIRMATION: Call this function with user_confirmed=false. The system will block the deletion and instruct you to ask the user to confirm. You MUST then ask: 'Are you sure you want to delete [task name]?' "
                "STEP 3 — EXECUTE: Only after the user explicitly confirms (e.g. 'yes', 'sure', 'go ahead'), call this function again with the same task_id and user_confirmed=true. "
                "If multiple tasks match the description, ask the user to clarify before calling."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "The unique ID of the task to delete.",
                    },
                    "user_confirmed": {
                        "type": "boolean",
                        "description": "CRITICAL: If the user is asking to delete this for the FIRST time, you MUST set this to false. ONLY set to true if you have ALREADY asked them 'Are you sure?' and they replied 'Yes'.",
                    },
                },
                "required": ["task_id", "user_confirmed"],
            },
        },
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
                        "description": "The date of the event in YYYY-MM-DD format.",
                    },
                    "time": {
                        "type": "string",
                        "description": "The start time of the event in HH:MM format (24-hour).",
                    },
                    "event_title": {
                        "type": "string",
                        "description": "The name or description of the event.",
                    },
                },
                "required": ["date", "time", "event_title"],
            },
        },
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
                f"instead to create it in Google Calendar."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "The Google Calendar event ID of the event to update.",
                    },
                    "date": {
                        "type": "string",
                        "description": "The new date in YYYY-MM-DD format (only if it is being changed).",
                    },
                    "time": {
                        "type": "string",
                        "description": "The new time in HH:MM format (24-hour) (only if it is being changed).",
                    },
                    "event_title": {
                        "type": "string",
                        "description": "The new name or description of the event (only if it is being changed).",
                    },
                },
                "required": ["event_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_schedule_event",
            "description": (
                "Cancel or delete an event from the schedule. Use only when the user explicitly asks to cancel or remove an event. "
                "STEP 1 — LOOKUP: Find the event_id from the LIVE DATABASE CONTEXT (Calendar Events list) by matching the user's description to the correct event by title, date, and time. Do NOT call any other function to look it up. "
                "STEP 2 — REQUEST CONFIRMATION: Call this function with user_confirmed=false. The system will block the deletion and instruct you to ask the user to confirm. You MUST then ask: 'Are you sure you want to cancel [event name] on [date] at [time]?' "
                "STEP 3 — EXECUTE: Only after the user explicitly confirms (e.g. 'yes', 'sure', 'go ahead'), call this function again with the same event_id and user_confirmed=true. "
                "If multiple events match the description, ask the user to clarify before calling."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "The Google Calendar event ID of the event to delete.",
                    },
                    "user_confirmed": {
                        "type": "boolean",
                        "description": "CRITICAL: If the user is asking to delete this for the FIRST time, you MUST set this to false. ONLY set to true if you have ALREADY asked them 'Are you sure?' and they replied 'Yes'.",
                    },
                },
                "required": ["event_id", "user_confirmed"],
            },
        },
    },
]
