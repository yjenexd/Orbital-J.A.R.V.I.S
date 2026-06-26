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
        res = supabase.table("schedule").insert(
            {
                "user_id": user_id,
                "date": function_args.get("date"),
                "time": function_args.get("time"),
                "event": function_args.get("event_title"),
            }
        ).execute()

        if gcal_service and res.data:
            try:
                new_event = res.data[0]
                event_id = new_event["event_id"]
                date = new_event["date"]
                time = new_event["time"][:5]
                event_title = new_event["event"]
                end_date, end_time = _gcal_end_datetime(date, time)

                gcal_event = {
                    "summary": event_title,
                    "description": f"Event ID: {event_id}\nDate: {date}\nTime: {time}",
                    "start": {"dateTime": f"{date}T{time}:00+08:00"},
                    "end": {"dateTime": f"{end_date}T{end_time}:00+08:00"},
                    "extendedProperties": {"private": {"supabase_event_id": str(event_id)}},
                }
                created = gcal_service.events().insert(calendarId="primary", body=gcal_event).execute()
                supabase.table("schedule").update({"gcal_event_id": created["id"]}).eq("event_id", event_id).execute()
            except Exception as e:
                print(f"[GCAL ERROR] add_schedule_event: {e}")

        return json.dumps({"status": "success", "message": "Event added successfully."})

    if function_name == "update_schedule_event":
        event_id_int = int(function_args["event_id"])

        event_res = (
            supabase.table("schedule")
            .select("date, time, event, gcal_event_id")
            .eq("event_id", event_id_int)
            .eq("user_id", user_id)
            .execute()
        )

        update_payload = {}
        if "date" in function_args:
            update_payload["date"] = function_args["date"]
        if "time" in function_args:
            update_payload["time"] = function_args["time"]
        if "event_title" in function_args:
            update_payload["event"] = function_args["event_title"]

        supabase.table("schedule").update(update_payload).eq("event_id", event_id_int).eq(
            "user_id", user_id
        ).execute()

        if gcal_service and event_res.data:
            try:
                current = event_res.data[0]
                gcal_event_id = current.get("gcal_event_id")
                if gcal_event_id:
                    date = function_args.get("date", current["date"])
                    time = function_args.get("time", current["time"])[:5]
                    event_title = function_args.get("event_title", current["event"])
                    end_date, end_time = _gcal_end_datetime(date, time)

                    patch_body = {
                        "summary": event_title,
                        "description": f"Event ID: {event_id_int}\nDate: {date}\nTime: {time}",
                        "start": {"dateTime": f"{date}T{time}:00+08:00"},
                        "end": {"dateTime": f"{end_date}T{end_time}:00+08:00"},
                    }
                    gcal_service.events().patch(
                        calendarId="primary", eventId=gcal_event_id, body=patch_body
                    ).execute()
            except Exception as e:
                print(f"[GCAL ERROR] update_schedule_event: {e}")

        return json.dumps({"status": "success", "message": "Event updated successfully."})

    if function_name == "delete_schedule_event":
        if not function_args.get("user_confirmed"):
            return json.dumps(
                {
                    "status": "pending_confirmation",
                    "message": "SYSTEM OVERRIDE: Deletion blocked. DO NOT tell the user it was deleted. You MUST reply by asking the user: 'Are you sure you want to cancel this event?'",
                }
            )

        event_id_int = int(function_args["event_id"])

        gcal_event_id = None
        if gcal_service:
            try:
                event_res = (
                    supabase.table("schedule")
                    .select("gcal_event_id")
                    .eq("event_id", event_id_int)
                    .eq("user_id", user_id)
                    .execute()
                )
                if event_res.data:
                    gcal_event_id = event_res.data[0].get("gcal_event_id")
            except Exception as e:
                print(f"[GCAL ERROR] delete_schedule_event fetch: {e}")

        res = (
            supabase.table("schedule")
            .delete()
            .eq("event_id", event_id_int)
            .eq("user_id", user_id)
            .execute()
        )
        if len(res.data) == 0:
            return json.dumps({"status": "error", "message": "Deletion failed. No event found with that exact ID."})

        if gcal_service and gcal_event_id:
            try:
                gcal_service.events().delete(calendarId="primary", eventId=gcal_event_id).execute()
            except Exception as e:
                print(f"[GCAL ERROR] delete_schedule_event: {e}")

        return json.dumps({"status": "success", "message": "Event deleted successfully."})

    return function_response
