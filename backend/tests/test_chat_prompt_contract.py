import pytest

from app.chat.tool_definitions import TOOLS
from app.config import SYSTEM_PROMPT


def _tool_description(name: str) -> str:
    for tool in TOOLS:
        fn = tool.get("function", {})
        if fn.get("name") == name:
            return fn.get("description", "")
    raise AssertionError(f"Tool not found: {name}")


def test_system_prompt_enforces_no_data_dump_and_no_markdown_tables():
    assert "STRICT BAN ON DATA DUMPS" in SYSTEM_PROMPT
    assert "STRICT BAN ON FORMATTING" in SYSTEM_PROMPT
    assert "NEVER use Markdown tables" in SYSTEM_PROMPT


@pytest.mark.skip(reason="Blackout window removed from system prompt; infrastructure preserved for future use")
def test_system_prompt_contains_blackout_window_constraint():
    assert "Blackout Period" in SYSTEM_PROMPT
    assert "July 6, 2026 to July 17, 2026" in SYSTEM_PROMPT


def test_add_schedule_event_description_requires_relative_date_resolution():
    desc = _tool_description("add_schedule_event")
    assert "relative day" in desc
    assert "YYYY-MM-DD" in desc


def test_update_task_description_requires_user_context_passthrough_for_vague_updates():
    desc = _tool_description("update_task")
    assert "using ONLY the 'task_id' and the 'user_context' fields" in desc
    assert "DO NOT ask the user to clarify" in desc


def test_delete_task_description_requires_two_step_confirmation():
    desc = _tool_description("delete_task")
    assert "STEP 2 — REQUEST CONFIRMATION" in desc
    assert "user_confirmed=false" in desc
    assert "STEP 3 — EXECUTE" in desc


def test_delete_schedule_event_description_requires_specific_confirmation_prompt():
    desc = _tool_description("delete_schedule_event")
    assert "Are you sure you want to cancel [event name] on [date] at [time]?" in desc
