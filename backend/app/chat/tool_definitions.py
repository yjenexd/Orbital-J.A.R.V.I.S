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
                f"instead to create it in the database."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "integer",
                        "description": "The unique ID of the event to update.",
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
                        "description": "The unique ID of the event to delete.",
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
