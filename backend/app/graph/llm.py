from langchain_groq import ChatGroq


CHAT_MODEL = "llama-3.3-70b-versatile"


def get_chat_model(api_key: str) -> ChatGroq:
    """Build a chat model from a per-request BYOK Groq key.

    Constructed fresh inside the `agent` node each invocation (a ChatGroq is a
    thin HTTP wrapper, not a loaded model) so the per-user key is never baked
    into the module-compiled graph. Tests monkeypatch this function to inject a
    fake model, so callers must reference it as ``llm.get_chat_model`` rather
    than importing the symbol directly.
    """
    return ChatGroq(api_key=api_key, model=CHAT_MODEL)
