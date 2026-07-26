import json
from datetime import datetime, time as time_type, timedelta
from typing import Any

from fastapi import BackgroundTasks

from app.graph.triage_graph import run_triage_graph as triage_task_background
from app.clients import supabase
from app.config import CURR_DATE


def _parse_hhmm(t: str) -> time_type:
    h, m = t[:5].split(":")
    return time_type(int(h), int(m))


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

        if not res.data:
            return json.dumps({"status": "error", "message": "Failed to add the task. Please try again."})

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
            .eq("user_id", user_id)
            .execute()
        )

        if not task_res.data:
            return json.dumps({"status": "error", "message": "Update failed. No task found with that exact ID."})

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
            task_id_val = function_args.get("task_id")
            task_name = "this task"
            if task_id_val is not None:
                lookup = (
                    supabase.table("tasks")
                    .select("title")
                    .eq("task_id", int(task_id_val))
                    .eq("user_id", user_id)
                    .execute()
                )
                if lookup.data:
                    task_name = lookup.data[0].get("title") or task_name

            return json.dumps(
                {
                    "status": "pending_confirmation",
                    "message": (
                        "SYSTEM OVERRIDE: Deletion blocked. DO NOT tell the user it was deleted. "
                        f"You MUST reply by asking the user: 'Are you sure you want to delete {task_name}?'"
                    ),
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
            start_time_val = function_args.get("start_time")[:5]
            end_time_val = function_args.get("end_time")[:5]
            user_confirmed = function_args.get("user_confirmed", False)
            event_title = function_args.get("event_title")

            start_t = _parse_hhmm(start_time_val)
            end_t = _parse_hhmm(end_time_val)

            if start_t == end_t:
                return json.dumps({"status": "error", "message": "Start and end time cannot be the same."})

            if end_t < start_t and not user_confirmed:
                next_date = (datetime.strptime(date_val, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
                return json.dumps({
                    "status": "pending_confirmation",
                    "message": (
                        "SYSTEM OVERRIDE: Midnight-spanning event detected. DO NOT add the event yet. "
                        "You MUST reply by asking the user: "
                        f"'Adding {event_title} spans midnight — it will start on {date_val} at {start_time_val} "
                        f"and end on {next_date} at {end_time_val}. Do you want to proceed?'"
                    ),
                })

            end_date = (
                (datetime.strptime(date_val, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
                if end_t < start_t else date_val
            )

            if not user_confirmed:
                existing = (
                    supabase.table("schedule")
                    .select("event, start_time, end_time")
                    .eq("user_id", user_id)
                    .eq("date", date_val)
                    .execute()
                    .data
                )
                conflicts = []
                for row in existing:
                    if not row.get("start_time") or not row.get("end_time"):
                        continue
                    e_start = _parse_hhmm(row["start_time"])
                    e_end = _parse_hhmm(row["end_time"])
                    if start_t < e_end and end_t > e_start:
                        conflicts.append(f"{row['event']} ({row['start_time']}–{row['end_time']})")
                if conflicts:
                    conflict_list = ", ".join(conflicts)
                    return json.dumps({
                        "status": "pending_confirmation",
                        "message": (
                            "SYSTEM OVERRIDE: Schedule conflict detected. DO NOT add the event yet. "
                            "You MUST reply by asking the user: "
                            f"'Adding {event_title} ({start_time_val}–{end_time_val}) on {date_val} conflicts with: {conflict_list}. Do you still want to add it?'"
                        ),
                    })

            gcal_event = {
                "summary": event_title,
                "start": {"dateTime": f"{date_val}T{start_time_val}:00+08:00"},
                "end": {"dateTime": f"{end_date}T{end_time_val}:00+08:00"},
            }
            created = gcal_service.events().insert(calendarId="primary", body=gcal_event).execute()
            supabase.table("schedule").insert({
                "user_id": user_id,
                "event": event_title,
                "date": date_val,
                "start_time": start_time_val,
                "end_time": end_time_val,
                "gcal_event_id": created["id"],
            }).execute()
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
            current_end_obj = current.get("end", {})
            current_date = current_start.get("dateTime", current_start.get("date", ""))[:10]
            current_time = current_start.get("dateTime", "T00:00")[11:16]
            _current_end_raw = current_end_obj.get("dateTime", "")
            current_end = _current_end_raw[11:16] if len(_current_end_raw) > 15 else "23:59"

            date_val = function_args.get("date", current_date)
            start_time_val = function_args.get("start_time", current_time)[:5]
            end_time_val = function_args.get("end_time", current_end)[:5]
            user_confirmed = function_args.get("user_confirmed", False)
            event_title = function_args.get("event_title", current.get("summary", ""))

            start_t = _parse_hhmm(start_time_val)
            end_t = _parse_hhmm(end_time_val)

            if start_t == end_t:
                return json.dumps({"status": "error", "message": "Start and end time cannot be the same."})

            if end_t < start_t and not user_confirmed:
                next_date = (datetime.strptime(date_val, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
                return json.dumps({
                    "status": "pending_confirmation",
                    "message": (
                        "SYSTEM OVERRIDE: Midnight-spanning event detected. DO NOT update the event yet. "
                        "You MUST reply by asking the user: "
                        f"'This event spans midnight — it will start on {date_val} at {start_time_val} "
                        f"and end on {next_date} at {end_time_val}. Do you want to proceed?'"
                    ),
                })

            end_date = (
                (datetime.strptime(date_val, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
                if end_t < start_t else date_val
            )

            patch_body = {
                "summary": event_title,
                "start": {"dateTime": f"{date_val}T{start_time_val}:00+08:00"},
                "end": {"dateTime": f"{end_date}T{end_time_val}:00+08:00"},
            }
            gcal_service.events().patch(calendarId="primary", eventId=gcal_event_id, body=patch_body).execute()
            supabase.table("schedule").update({
                "event": event_title,
                "date": date_val,
                "start_time": start_time_val,
                "end_time": end_time_val,
            }).eq("gcal_event_id", gcal_event_id).eq("user_id", user_id).execute()
        except Exception as e:
            print(f"[GCAL ERROR] update_schedule_event: {e}")
            return json.dumps({"status": "error", "message": f"Failed to update event: {str(e)}"})

        return json.dumps({"status": "success", "message": "Event updated in Google Calendar successfully."})

    if function_name == "delete_schedule_event":
        if not function_args.get("user_confirmed"):
            event_id = str(function_args["event_id"])
            event_name = "this event"
            event_date = "unknown date"
            event_time = "unknown time"
            if gcal_service:
                try:
                    current = gcal_service.events().get(calendarId="primary", eventId=event_id).execute()
                    start_event = current.get("start", {})
                    start_value = start_event.get("dateTime", start_event.get("date", ""))
                    if start_value:
                        event_date = start_value[:10]
                        if "T" in start_value:
                            event_time = start_value[11:16]
                        else:
                            event_time = "00:00"
                    event_name = current.get("summary", event_name)
                except Exception as e:
                    print(f"[GCAL ERROR] delete_schedule_event lookup: {e}")

            return json.dumps(
                {
                    "status": "pending_confirmation",
                    "message": (
                        "SYSTEM OVERRIDE: Deletion blocked. DO NOT tell the user it was deleted. "
                        "You MUST reply by asking the user: "
                        f"'Are you sure you want to cancel {event_name} on {event_date} at {event_time}?'"
                    ),
                }
            )

        gcal_event_id = str(function_args["event_id"])

        if not gcal_service:
            return json.dumps({"status": "error", "message": "Google Calendar is not connected."})

        try:
            gcal_service.events().delete(calendarId="primary", eventId=gcal_event_id).execute()
            supabase.table("schedule").delete().eq("gcal_event_id", gcal_event_id).eq("user_id", user_id).execute()
        except Exception as e:
            print(f"[GCAL ERROR] delete_schedule_event: {e}")
            return json.dumps({"status": "error", "message": f"Failed to delete event: {str(e)}"})

        return json.dumps({"status": "success", "message": "Event deleted from Google Calendar successfully."})

    return function_response
