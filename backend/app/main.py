import os
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import storage, weather
from .engine import build_engine
from .schemas import ChatRequest, ChatResponse, LeadModel, SessionRequest

engine = build_engine()
knowledge_base = engine.kb


@asynccontextmanager
async def lifespan(_app):
    storage.init_db()
    yield


app = FastAPI(
    title="Synergy Chatbot API",
    description="API чат-бота Университета «Синергия»: интенты, бытовые темы и приём заявок.",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "knowledge_base": knowledge_base.meta.get("name"),
        "intents": len(knowledge_base.intents),
        "sources": knowledge_base.source_paths,
        "weather_enabled": weather.enabled(),
    }


@app.get("/api/welcome")
def welcome():
    return {
        "reply": engine.welcome(),
        "quick_replies": list(knowledge_base.default_quick_replies),
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    session_id = payload.session_id or str(uuid4())
    result = engine.process(session_id, payload.message)
    return ChatResponse(
        session_id=session_id,
        reply=result["reply"],
        quick_replies=result["quick_replies"],
        state=result["state"],
        intent=result["intent"],
    )


@app.post("/api/session/reset")
def reset_session(payload: SessionRequest):
    storage.reset_session(payload.session_id)
    return {"status": "ok"}


@app.get("/api/leads", response_model=list[LeadModel])
def leads(x_admin_token: str = Header(default="")):
    expected = os.environ.get("ADMIN_TOKEN", "")
    if expected and x_admin_token != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return storage.get_leads()
