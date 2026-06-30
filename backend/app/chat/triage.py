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
    You are J.A.R.V.I.S's background task triage engine. Evaluate this task and output a JSON object scoring its priority.

    Task Title: {title}
    Deadline: {deadline}
    Current Date: {CURR_DATE.isoformat()}
    User Update Notes: '{user_context if user_context else "None"}'

    EVALUATION CRITERIA:
    Assess this based on a rigorous Computer Science workload. 
    - CRITICAL (Score 90-100): Overdue items, Orbital project deployments, major CS assignments, or Secondary 4 national exam prep due within 48 hours.
    - HIGH (Score 75-89): Standard assignments or important errands due within 3 days.
    - MEDIUM (Score 50-74): Routine maintenance (e.g., aquarium water changes, general studying) due within 4-7 days.
    - LOW (Score 10-49): Distant deadlines (>7 days), minor personal errands, or hobby-related tasks.
    * Adjust upwards by 15 points if the user notes explicitly state it is important, capping at 100.

    Return EXACTLY this JSON format and nothing else:
    {{
        "priority_level": "high",
        "priority_score": 85,
        "triage_rationale": "One short sentence explaining why."
    }}
    """

    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
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
