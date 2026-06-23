import json
from typing import Any

from fastapi import BackgroundTasks

from app.chat.triage import triage_task_background
from app.clients import supabase


def execute_tool_call(
    function_name: str,
    function_args: dict[str, Any],
    user_id: str,
    user_message: str = "",
    background_tasks: BackgroundTasks | None = None,
    x_groq_api_key: str | None = None,
) -> str:
    function_response = json.dumps({"status": "error", "message": "Unknown function."})

    if function_name == "add_task":
        deadline_val = function_args.get("deadline")

        if not deadline_val:
            return json.dumps(
                {
                    "status": "pending_information",
                    "message": "SYSTEM OVERRIDE: Task creation blocked. DO NOT tell the user it was added. You MUST reply by asking: 'When is the deadline for this task?'",
                }
            )

        insert_payload = {
            "user_id": user_id,
            "title": function_args.get("title"),
            "priority": function_args.get("priority", "medium"),
        }

        if str(deadline_val).lower() != "none":
            insert_payload["deadline"] = deadline_val

        res = supabase.table("tasks").insert(insert_payload).execute()

        if background_tasks and x_groq_api_key and res.data:
            new_task = res.data[0]
            background_tasks.add_task(
                triage_task_background,
                task_id=new_task["task_id"],
                user_id=user_id,
                title=new_task["title"],
                deadline=new_task.get("deadline", "none"),
                x_groq_api_key=x_groq_api_key,
            )

        return json.dumps({"status": "success", "message": "Task added successfully."})

    if function_name == "update_task":
        task_id_int = int(function_args["task_id"])
        update_payload = {}

        if "completed" in function_args:
            update_payload["completed"] = function_args["completed"]
        if "priority" in function_args:
            update_payload["priority"] = function_args["priority"]
        if "deadline" in function_args:
            update_payload["deadline"] = function_args["deadline"]

        if update_payload:
            supabase.table("tasks").update(update_payload).eq("task_id", task_id_int).eq(
                "user_id", user_id
            ).execute()

        task_res = supabase.table("tasks").select("title, deadline").eq("task_id", task_id_int).execute()

        if background_tasks and x_groq_api_key and task_res.data:
            updated_task = task_res.data[0]
            context = function_args.get("user_context", user_message)
            background_tasks.add_task(
                triage_task_background,
                task_id=task_id_int,
                user_id=user_id,
                title=updated_task["title"],
                deadline=updated_task.get("deadline", "none"),
                x_groq_api_key=x_groq_api_key,
                user_context=context,
            )

        return json.dumps({"status": "success", "message": "Task updated and queued for AI re-triage."})

    if function_name == "delete_task":
        if not function_args.get("user_confirmed"):
            return json.dumps(
                {
                    "status": "pending_confirmation",
                    "message": "SYSTEM OVERRIDE: Deletion blocked. DO NOT tell the user it was deleted. You MUST reply by asking the user: 'Are you sure you want to delete this task?'",
                }
            )

        res = (
            supabase.table("tasks")
            .delete()
            .eq("task_id", int(function_args["task_id"]))
            .eq("user_id", user_id)
            .execute()
        )

        if len(res.data) == 0:
            return json.dumps({"status": "error", "message": "Deletion failed. No task found with that exact ID."})
        return json.dumps({"status": "success", "message": "Task deleted successfully."})

    if function_name == "add_schedule_event":
        supabase.table("schedule").insert(
            {
                "user_id": user_id,
                "date": function_args.get("date"),
                "time": function_args.get("time"),
                "event": function_args.get("event_title"),
            }
        ).execute()
        return json.dumps({"status": "success", "message": "Event added successfully."})

    if function_name == "update_schedule_event":
        update_payload = {}
        if "date" in function_args:
            update_payload["date"] = function_args["date"]
        if "time" in function_args:
            update_payload["time"] = function_args["time"]
        if "event_title" in function_args:
            update_payload["event"] = function_args["event_title"]

        supabase.table("schedule").update(update_payload).eq("event_id", int(function_args["event_id"])).eq(
            "user_id", user_id
        ).execute()
        return json.dumps({"status": "success", "message": "Event updated successfully."})

    if function_name == "delete_schedule_event":
        if not function_args.get("user_confirmed"):
            return json.dumps(
                {
                    "status": "pending_confirmation",
                    "message": "SYSTEM OVERRIDE: Deletion blocked. DO NOT tell the user it was deleted. You MUST reply by asking the user: 'Are you sure you want to cancel this event?'",
                }
            )

        res = (
            supabase.table("schedule")
            .delete()
            .eq("event_id", int(function_args["event_id"]))
            .eq("user_id", user_id)
            .execute()
        )
        if len(res.data) == 0:
            return json.dumps({"status": "error", "message": "Deletion failed. No event found with that exact ID."})
        return json.dumps({"status": "success", "message": "Event deleted successfully."})

    return function_response
