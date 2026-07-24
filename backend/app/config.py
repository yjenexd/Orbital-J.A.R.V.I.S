from datetime import date
import os

from dotenv import load_dotenv


load_dotenv()


CURR_DATE: date = date.today()


def get_required_env_var(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


SUPABASE_URL = get_required_env_var("SUPABASE_URL")
SUPABASE_KEY = get_required_env_var("SUPABASE_KEY")


# Core LLM system prompts now live in the versioned app.prompts package
# (single source of truth). Import CHAT_SYSTEM_PROMPT from there.