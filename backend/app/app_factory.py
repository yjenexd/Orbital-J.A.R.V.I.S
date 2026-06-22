from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.briefing import router as briefing_router
from app.routes.chat import router as chat_router
from app.routes.core import router as core_router


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(core_router)
app.include_router(chat_router)
app.include_router(briefing_router)
