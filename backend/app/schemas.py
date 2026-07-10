from pydantic import BaseModel


class ChatRequest(BaseModel):
    user_id: str
    message: str
    history_limit: int = 10
