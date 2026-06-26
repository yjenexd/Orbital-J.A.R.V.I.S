import os
from collections.abc import AsyncGenerator

from fastapi import Header, HTTPException
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from openai import AsyncOpenAI
from supabase import Client, create_client

from app.config import SUPABASE_KEY, SUPABASE_URL


supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_google_calendar_service(refresh_token: str):
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token",
    )
    return build("calendar", "v3", credentials=creds)


async def get_groq_client(
    x_groq_api_key: str | None = Header(default=None),
) -> AsyncGenerator[AsyncOpenAI, None]:
    if not x_groq_api_key:
        raise HTTPException(status_code=401, detail="API_KEY_MISSING")

    client = AsyncOpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=x_groq_api_key,
    )

    try:
        yield client
    finally:
        await client.close()
