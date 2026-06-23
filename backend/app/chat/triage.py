import json

from openai import AsyncOpenAI

from app.clients import supabase
from app.config import CURR_DATE


async def triage_task_background(
    task_id: int,
    user_id: str,
    title: str,
    deadline: str,
    x_groq_api_key: str,
    user_context: str = "",
):
    if not x_groq_api_key:
        print("API_KEY_MISSING: Cannot perform triage without a valid API key.")
        return

    client = AsyncOpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=x_groq_api_key,
    )

    triage_prompt = f"""
    You are J.A.R.V.I.S's task triage engine. Evaluate the following task and return a JSON object evaluating its priority

    Task Title: {title}
    Deadline: {deadline}
    Current Date: {CURR_DATE.isoformat()}
    User Update Notes: '{user_context if user_context else "None"}'

    Evaluate based on a university student's lifestyle, academic workload, and personal commitments. Consider the urgency of the deadline, the typical time required for such a task, and how it fits into the user's overall schedule.:
    - Due within 48 hours: high priority (score 80-100)
    - Due within 3-7 days: medium priority (score 50-79)
    - Due in more than 7 days or minor errand: low priority (score 0-49)
    - if the user tells you it is important, adjust the score upwards by 10-20 points, but do not exceed 100.

    Return EXACTLY this JSON format and nothing else:
    {{
        "priority_level": "high",
        "priority_score": 85,
        "triage_rationale": "One short sentence explaining why."
    }}
    """

    try:
        response = await client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": triage_prompt}],
            response_format={"type": "json_object"},
        )

        ai_data = json.loads(response.choices[0].message.content)

        supabase.table("tasks").update(
            {
                "priority": ai_data.get("priority_level", "medium"),
                "priority_score": ai_data.get("priority_score", 50),
                "triage_rationale": ai_data.get(
                    "triage_rationale",
                    "..pending review by AI triage engine..",
                ),
            }
        ).eq("task_id", task_id).eq("user_id", user_id).execute()

    except Exception as e:
        print(f"Triage failed for task {task_id}: {str(e)}")
        supabase.table("tasks").update(
            {
                "priority_score": 50,
                "triage_rationale": "Standard sorting applied (AI Triage offline).",
            }
        ).eq("task_id", task_id).execute()
    finally:
        await client.close()
