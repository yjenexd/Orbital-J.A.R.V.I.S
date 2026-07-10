from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from openai import APIError, AsyncOpenAI

from app.clients import get_current_user_id, get_groq_client
from app.graph.chat_graph import chat_graph
from app.schemas import ChatRequest


router = APIRouter()


@router.post("/chat")
async def execute_chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    client: AsyncOpenAI = Depends(get_groq_client),
    authenticated_user_id: str = Depends(get_current_user_id),
    x_groq_api_key: str | None = Header(default=None),
):
    # Always trust the authenticated identity, not the client payload.
    # get_groq_client is kept purely as the "401 if key header missing" guard;
    # the actual model client is built inside the graph's agent node from the
    # per-request key threaded through RunnableConfig below.
    user_id = authenticated_user_id

    initial_state = {
        "user_id": user_id,
        "user_message": request.message,
        "messages": [],
    }
    config = {
        "configurable": {
            "groq_api_key": x_groq_api_key,
            "background_tasks": background_tasks,
        }
    }

    try:
        result = await chat_graph.ainvoke(initial_state, config=config)
        return {"reply": result["final_reply"]}
    except APIError as e:
        print(f"Groq API returned an error: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail="Upstream provider error: Intelligence backend is currently unavailable.",
        )
    except Exception as e:
        print(f"Unexpected error in chat execution engine: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error processing the chat request.")
