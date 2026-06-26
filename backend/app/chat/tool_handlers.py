import json
from datetime import datetime, timedelta
from typing import Any

from fastapi import BackgroundTasks

from app.chat.triage import triage_task_background
from app.clients import supabase
from app.config import CURR_DATE


def _gcal_end_datetime(date: str, time: str) -> tuple[str, str]:
    start_dt = datetime.strptime(f"{date}T{time[:5]}", "%Y-%m-%dT%H:%M")
    end_dt = start_dt + timedelta(hours=1)
    return end_dt.strftime("%Y-%m-%d"), end_dt.strftime("%H:%M")


def execute_tool_call(
    function_name: str,
    function_args: dict[str, Any],
    user_id: str,
    user_message: str = "",
    background_tasks: BackgroundTasks | None = None,
    x_groq_api_key: str | None = None,
    gcal_service=None,
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

        deadline_str = str(deadline_val).lower()
        if deadline_str != "none":
            insert_payload["deadline"] = deadline_val

        res = supabase.table("tasks").insert(insert_payload).execute()

        if res.data:
            new_task = res.data[0]

            if background_tasks and x_groq_api_key:
                background_tasks.add_task(
                    triage_task_background,
                    task_id=new_task["task_id"],
                    user_id=user_id,
                    title=new_task["title"],
                    deadline=new_task.get("deadline", "none"),
                    x_groq_api_key=x_groq_api_key,
                )

            if gcal_service:
                try:
                    task_id = new_task["task_id"]
                    priority = new_task.get("priority", "medium")
                    gcal_date = deadline_val if deadline_str != "none" else CURR_DATE.isoformat()

                    gcal_event = {
                        "summary": new_task["title"],
                        "description": f"Task ID: {task_id}\nPriority: {priority}\nDeadline: {deadline_val}",
                        "start": {"date": gcal_date},
                        "end": {"date": gcal_date},
                        "extendedProperties": {"private": {"supabase_task_id": str(task_id)}},
                    }
                    created = gcal_service.events().insert(calendarId="primary", body=gcal_event).execute()
                    supabase.table("tasks").update({"gcal_event_id": created["id"]}).eq("task_id", task_id).execute()
                except Exception as e:
                    print(f"[GCAL ERROR] add_task: {e}")

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

        task_res = (
            supabase.table("tasks")
            .select("title, deadline, gcal_event_id")
            .eq("task_id", task_id_int)
            .execute()
        )

        if task_res.data:
            updated_task = task_res.data[0]

            if background_tasks and x_groq_api_key:
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

            if gcal_service:
                try:
                    gcal_event_id = updated_task.get("gcal_event_id")
                    if gcal_event_id:
                        deadline = updated_task.get("deadline")
                        priority = function_args.get("priority", "")
                        patch_body = {
                            "summary": updated_task["title"],
                            "description": f"Task ID: {task_id_int}\nPriority: {priority}\nDeadline: {deadline or 'none'}",
                        }
                        if deadline:
                            patch_body["start"] = {"date": deadline}
                            patch_body["end"] = {"date": deadline}
                        gcal_service.events().patch(
                            calendarId="primary", eventId=gcal_event_id, body=patch_body
                        ).execute()
                except Exception as e:
                    print(f"[GCAL ERROR] update_task: {e}")

        return json.dumps({"status": "success", "message": "Task updated and queued for AI re-triage."})

    if function_name == "delete_task":
        if not function_args.get("user_confirmed"):
            return json.dumps(
                {
                    "status": "pending_confirmation",
                    "message": "SYSTEM OVERRIDE: Deletion blocked. DO NOT tell the user it was deleted. You MUST reply by asking the user: 'Are you sure you want to delete this task?'",
                }
            )

        task_id_int = int(function_args["task_id"])

        gcal_event_id = None
        if gcal_service:
            try:
                task_res = (
                    supabase.table("tasks")
                    .select("gcal_event_id")
                    .eq("task_id", task_id_int)
                    .eq("user_id", user_id)
                    .execute()
                )
                if task_res.data:
                    gcal_event_id = task_res.data[0].get("gcal_event_id")
            except Exception as e:
                print(f"[GCAL ERROR] delete_task fetch: {e}")

        res = (
            supabase.table("tasks")
            .delete()
            .eq("task_id", task_id_int)
            .eq("user_id", user_id)
            .execute()
        )

        if len(res.data) == 0:
            return json.dumps({"status": "error", "message": "Deletion failed. No task found with that exact ID."})

        if gcal_service and gcal_event_id:
            try:
                gcal_service.events().delete(calendarId="primary", eventId=gcal_event_id).execute()
            except Exception as e:
                print(f"[GCAL ERROR] delete_task: {e}")

        return json.dumps({"status": "success", "message": "Task deleted successfully."})

    if function_name == "add_schedule_event":
        if not gcal_service:
            return json.dumps({"status": "error", "message": "Google Calendar is not connected. Please link your Google account."})

        try:
            date_val = function_args.get("date")
            time_val = function_args.get("time")[:5]
            event_title = function_args.get("event_title")
            end_date, end_time = _gcal_end_datetime(date_val, time_val)

            gcal_event = {
                "summary": event_title,
                "start": {"dateTime": f"{date_val}T{time_val}:00+08:00"},
                "end": {"dateTime": f"{end_date}T{end_time}:00+08:00"},
            }
            gcal_service.events().insert(calendarId="primary", body=gcal_event).execute()
        except Exception as e:
            print(f"[GCAL ERROR] add_schedule_event: {e}")
            return json.dumps({"status": "error", "message": f"Failed to add event: {str(e)}"})

        return json.dumps({"status": "success", "message": "Event added to Google Calendar successfully."})

    if function_name == "update_schedule_event":
        gcal_event_id = str(function_args["event_id"])

        if not gcal_service:
            return json.dumps({"status": "error", "message": "Google Calendar is not connected."})

        try:
            current = gcal_service.events().get(calendarId="primary", eventId=gcal_event_id).execute()
            current_start = current.get("start", {})
            current_date = current_start.get("dateTime", current_start.get("date", ""))[:10]
            current_time = current_start.get("dateTime", "T00:00")[11:16]

            date_val = function_args.get("date", current_date)
            time_val = function_args.get("time", current_time)[:5]
            event_title = function_args.get("event_title", current.get("summary", ""))
            end_date, end_time = _gcal_end_datetime(date_val, time_val)

            patch_body = {
                "summary": event_title,
                "start": {"dateTime": f"{date_val}T{time_val}:00+08:00"},
                "end": {"dateTime": f"{end_date}T{end_time}:00+08:00"},
            }
            gcal_service.events().patch(calendarId="primary", eventId=gcal_event_id, body=patch_body).execute()
        except Exception as e:
            print(f"[GCAL ERROR] update_schedule_event: {e}")
            return json.dumps({"status": "error", "message": f"Failed to update event: {str(e)}"})

        return json.dumps({"status": "success", "message": "Event updated in Google Calendar successfully."})

    if function_name == "delete_schedule_event":
        if not function_args.get("user_confirmed"):
            return json.dumps(
                {
                    "status": "pending_confirmation",
                    "message": "SYSTEM OVERRIDE: Deletion blocked. DO NOT tell the user it was deleted. You MUST reply by asking the user: 'Are you sure you want to cancel this event?'",
                }
            )

        gcal_event_id = str(function_args["event_id"])

        if not gcal_service:
            return json.dumps({"status": "error", "message": "Google Calendar is not connected."})

        try:
            gcal_service.events().delete(calendarId="primary", eventId=gcal_event_id).execute()
        except Exception as e:
            print(f"[GCAL ERROR] delete_schedule_event: {e}")
            return json.dumps({"status": "error", "message": f"Failed to delete event: {str(e)}"})

        return json.dumps({"status": "success", "message": "Event deleted from Google Calendar successfully."})

    return function_response
