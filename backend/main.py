import os
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.agent_engine import run_multi_turn_agent
from backend.analytics import generate_session_analytics
from backend.database import (
    init_db,
    interactions_collection,
    sessions_collection,
    users_collection,
)

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

app = FastAPI(title="Multi-Turn AI Chatbot with LLaMA 3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    try:
        res = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        res.raise_for_status()
    except Exception as exc:
        print(f"[Warning] Ollama check failed at startup: {exc}")


# ---------- Request Models ----------

class StartSessionRequest(BaseModel):
    user_id: str
    email: Optional[str] = "local_user@example.com"
    name: Optional[str] = "Local User"


class ChatRequest(BaseModel):
    session_id: str
    user_id: str
    message: str


class FeedbackRequest(BaseModel):
    interaction_id: str
    session_id: str
    rating: int = Field(..., ge=1, le=4)
    correctness: str = Field(..., pattern="^(Correct|Partial|Incorrect)$")
    length_type: str = Field(..., pattern="^(Short|To the Point|Lengthy)$")


class EndSessionRequest(BaseModel):
    session_id: str


# ---------- Helper Functions ----------

def get_last_interaction(session_id: str):
    return interactions_collection.find_one(
        {"session_id": session_id},
        sort=[("turn_number", -1)],
    )


# ---------- Endpoints ----------

@app.get("/health")
def health_check():
    return {"status": "ok", "model": OLLAMA_MODEL}


@app.post("/session/start")
def start_session(req: StartSessionRequest):
    users_collection.update_one(
        {"user_id": req.user_id},
        {
            "$setOnInsert": {
                "user_id": req.user_id,
                "email": req.email,
                "name": req.name,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        },
        upsert=True,
    )

    session_id = str(uuid.uuid4())
    session_doc = {
        "session_id": session_id,
        "user_id": req.user_id,
        "start_time": datetime.now(timezone.utc).isoformat(),
        "end_time": None,
        "status": "active",
    }
    sessions_collection.insert_one(session_doc)
    return {"session_id": session_id, "status": "active"}


@app.post("/chat")
def send_chat(req: ChatRequest):
    session = sessions_collection.find_one({"session_id": req.session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session.get("status") != "active":
        raise HTTPException(status_code=400, detail="Session has already ended.")

    # Backend-level Mandatory Feedback Lock
    last_turn = get_last_interaction(req.session_id)
    if last_turn and not last_turn.get("feedback", {}).get("submitted", False):
        raise HTTPException(
            status_code=403,
            detail="Feedback is mandatory before sending the next message.",
        )

    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    history = list(
        interactions_collection.find({"session_id": req.session_id}).sort("turn_number", 1)
    )

    start_ts = time.perf_counter()
    try:
        agent_out = run_multi_turn_agent(history, req.message)
        bot_reply = agent_out["response"]
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLaMA 3 error: {exc}")

    elapsed_sec = round(time.perf_counter() - start_ts, 2)
    interaction_id = str(uuid.uuid4())
    turn_number = agent_out["turn_number"]

    record = {
        "interaction_id": interaction_id,
        "session_id": req.session_id,
        "turn_number": turn_number,
        "user_message": req.message,
        "bot_response": bot_reply,
        "topic_label": agent_out["topic_label"],
        "topic_shifted": agent_out["topic_shifted"],
        "agent_action": agent_out["agent_action"],
        "response_time_sec": elapsed_sec,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "feedback": {
            "submitted": False,
            "rating": None,
            "correctness": None,
            "length_type": None,
        },
    }
    interactions_collection.insert_one(record)

    return {
        "interaction_id": interaction_id,
        "session_id": req.session_id,
        "turn_number": turn_number,
        "topic_label": agent_out["topic_label"],
        "topic_shifted": agent_out["topic_shifted"],
        "agent_action": agent_out["agent_action"],
        "response": bot_reply,
        "response_time_sec": elapsed_sec,
        "feedback_required": True,
    }


@app.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    turn = interactions_collection.find_one(
        {"interaction_id": req.interaction_id, "session_id": req.session_id}
    )
    if not turn:
        raise HTTPException(status_code=404, detail="Interaction not found.")

    interactions_collection.update_one(
        {"interaction_id": req.interaction_id},
        {
            "$set": {
                "feedback": {
                    "submitted": True,
                    "rating": req.rating,
                    "correctness": req.correctness,
                    "length_type": req.length_type,
                }
            }
        },
    )
    return {"status": "feedback_saved", "chat_unlocked": True}


@app.get("/analytics/{session_id}")
def get_session_analytics(session_id: str):
    session = sessions_collection.find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    if session.get("status") == "completed" and session.get("final_analytics_summary"):
        return session["final_analytics_summary"]

    turns = list(interactions_collection.find({"session_id": session_id}))
    return generate_session_analytics(session_id, turns)


@app.post("/session/end")
def end_session(req: EndSessionRequest):
    session = sessions_collection.find_one({"session_id": req.session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    turns = list(interactions_collection.find({"session_id": req.session_id}))
    summary = generate_session_analytics(req.session_id, turns)

    sessions_collection.update_one(
        {"session_id": req.session_id},
        {
            "$set": {
                "status": "completed",
                "end_time": datetime.now(timezone.utc).isoformat(),
                "final_analytics_summary": summary,
            }
        },
    )
    return {
        "session_id": req.session_id,
        "status": "completed",
        "analytics_summary": summary,
    }