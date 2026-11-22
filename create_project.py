from pathlib import Path

BASE_DIR = Path(".")

folders = [
    BASE_DIR / "backend",
    BASE_DIR / "frontend-nextjs" / "src" / "app",
]

files = {
    BASE_DIR / ".env": """APP_SECRET_KEY=change-this-to-a-strong-secret-key
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=llama3_chatbot_db
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
""",
    BASE_DIR / "requirements.txt": """fastapi
uvicorn
pymongo
requests
httpx
pandas
scikit-learn
plotly
python-dotenv
authlib
itsdangerous
""",
    BASE_DIR / "backend" / "__init__.py": "",
    BASE_DIR / "backend" / "database.py": """import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "llama3_chatbot_db")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

users_collection = db["users"]
sessions_collection = db["sessions"]
interactions_collection = db["interactions"]


def init_db():
    users_collection.create_index("email", unique=True)
    sessions_collection.create_index("session_id", unique=True)
    interactions_collection.create_index([("session_id", 1), ("turn_number", 1)])
""",
    BASE_DIR / "backend" / "main.py": """import os
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

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


def get_last_interaction(session_id: str):
    return interactions_collection.find_one(
        {"session_id": session_id},
        sort=[("turn_number", -1)],
    )


def build_session_messages(session_id: str, new_message: str):
    history = list(
        interactions_collection.find({"session_id": session_id}).sort("turn_number", 1)
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful, accurate multi-turn AI assistant covering "
                "Machine Learning, Deep Learning, Healthcare AI, Power Systems, "
                "and E-commerce AI. Keep answers clear and structured."
            ),
        }
    ]
    for item in history:
        messages.append({"role": "user", "content": item["user_message"]})
        messages.append({"role": "assistant", "content": item["bot_response"]})

    messages.append({"role": "user", "content": new_message})
    return messages, len(history) + 1


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

    last_turn = get_last_interaction(req.session_id)
    if last_turn and not last_turn.get("feedback", {}).get("submitted", False):
        raise HTTPException(
            status_code=403,
            detail="Feedback is mandatory before sending the next message.",
        )

    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    messages, turn_number = build_session_messages(req.session_id, req.message)

    start_ts = time.perf_counter()
    try:
        ollama_res = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
            },
            timeout=180,
        )
        ollama_res.raise_for_status()
        data = ollama_res.json()
        bot_reply = data["message"]["content"]
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLaMA 3 error: {exc}")

    elapsed_sec = round(time.perf_counter() - start_ts, 2)
    interaction_id = str(uuid.uuid4())

    record = {
        "interaction_id": interaction_id,
        "session_id": req.session_id,
        "turn_number": turn_number,
        "user_message": req.message,
        "bot_response": bot_reply,
        "topic_label": "Pending Classification",
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


@app.post("/session/end")
def end_session(req: EndSessionRequest):
    result = sessions_collection.update_one(
        {"session_id": req.session_id},
        {
            "$set": {
                "status": "completed",
                "end_time": datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"session_id": req.session_id, "status": "completed"}
""",
    BASE_DIR / "backend" / "Dockerfile": """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend /app/backend

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
""",
    BASE_DIR / "docker-compose.yml": """services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    container_name: llama3_chatbot_backend
    ports:
      - "8000:8000"
    environment:
      - MONGO_URI=mongodb://host.docker.internal:27017
      - MONGO_DB_NAME=llama3_chatbot_db
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
      - OLLAMA_MODEL=llama3
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend-nextjs
      dockerfile: Dockerfile
    container_name: llama3_chatbot_frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_BASE=http://localhost:8000
    depends_on:
      - backend
    restart: unless-stopped
""",
    BASE_DIR / "frontend-nextjs" / "Dockerfile": """FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "run", "start"]
""",
    BASE_DIR / "frontend-nextjs" / "package.json": """{
  "name": "llama3-chatbot-nextjs",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "15.0.0",
    "react": "19.0.0",
    "react-dom": "19.0.0",
    "@mui/material": "^6.1.0",
    "@emotion/react": "^11.13.0",
    "@emotion/styled": "^11.13.0"
  }
}
""",
    BASE_DIR / "frontend-nextjs" / "src" / "app" / "layout.js": """export const metadata = {
  title: "Multi-Turn AI Chatbot with LLaMA 3",
  description: "Next.js + Material UI + FastAPI + Local LLaMA 3",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, backgroundColor: "#f3f4f6" }}>{children}</body>
    </html>
  );
}
""",
    BASE_DIR / "frontend-nextjs" / "src" / "app" / "page.js": """"use client";

import React, { useState } from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export default function HomePage() {
  const [userId] = useState("user_ahmad_01");
  const [sessionId, setSessionId] = useState(null);
  const [pendingInteractionId, setPendingInteractionId] = useState(null);
  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: 'Click "Start Session" to chat with local LLaMA 3. Submit feedback after each reply to unlock chat.',
    },
  ]);
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);

  const [rating, setRating] = useState("");
  const [correctness, setCorrectness] = useState("");
  const [lengthType, setLengthType] = useState("");

  const isLocked = Boolean(pendingInteractionId) || !sessionId || loading;

  const startSession = async () => {
    try {
      const res = await fetch(`${API_BASE}/session/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          email: "ahmadzafarawan@gmail.com",
          name: "Muhammad Ahmad Zafar",
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to start session");

      setSessionId(data.session_id);
      setPendingInteractionId(null);
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: `Session started: ${data.session_id}` },
      ]);
    } catch (err) {
      alert(err.message);
    }
  };

  const sendMessage = async () => {
    if (!inputText.trim() || !sessionId || pendingInteractionId) return;

    const userMsg = inputText.trim();
    setInputText("");
    setMessages((prev) => [...prev, { role: "user", text: userMsg }]);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          user_id: userId,
          message: userMsg,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Chat error");

      setPendingInteractionId(data.interaction_id);
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: data.response,
          meta: `Turn #${data.turn_number} | Latency: ${data.response_time_sec}s`,
        },
      ]);
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const submitFeedback = async () => {
    if (!rating || !correctness || !lengthType || !pendingInteractionId) {
      alert("Please select Rating (1-4), Correctness, and Length Type.");
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          interaction_id: pendingInteractionId,
          session_id: sessionId,
          rating: Number(rating),
          correctness,
          length_type: lengthType,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Feedback error");

      setPendingInteractionId(null);
      setRating("");
      setCorrectness("");
      setLengthType("");
    } catch (err) {
      alert(err.message);
    }
  };

  const endSession = async () => {
    if (!sessionId) return;
    try {
      const res = await fetch(`${API_BASE}/session/end`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to end session");

      setSessionId(null);
      setPendingInteractionId(null);
      setMessages((prev) => [...prev, { role: "bot", text: "Session completed." }]);
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <Box sx={{ maxWidth: 900, mx: "auto", p: 3 }}>
      <Paper elevation={3} sx={{ p: 3, borderRadius: 2 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
          <Box>
            <Typography variant="h6" fontWeight="bold">
              Multi-Turn AI Chatbot (LLaMA 3)
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {sessionId ? `Active Session: ${sessionId}` : "Session Not Active"}
            </Typography>
          </Box>
          <Stack direction="row" spacing={1}>
            <Button variant="contained" onClick={startSession} disabled={Boolean(sessionId)}>
              Start Session
            </Button>
            <Button variant="outlined" color="error" onClick={endSession} disabled={!sessionId}>
              End Session
            </Button>
          </Stack>
        </Stack>

        <Divider sx={{ mb: 2 }} />

        <Box
          sx={{
            height: 380,
            overflowY: "auto",
            p: 2,
            bgcolor: "#f8fafc",
            borderRadius: 1,
            mb: 2,
          }}
        >
          {messages.map((m, idx) => (
            <Box
              key={idx}
              sx={{
                display: "flex",
                justifyContent: m.role === "user" ? "flex-end" : "flex-start",
                mb: 1.5,
              }}
            >
              <Paper
                sx={{
                  p: 1.5,
                  maxWidth: "78%",
                  bgcolor: m.role === "user" ? "#2563eb" : "#e5e7eb",
                  color: m.role === "user" ? "#fff" : "#111827",
                  whiteSpace: "pre-wrap",
                }}
              >
                <Typography variant="body2">{m.text}</Typography>
                {m.meta && (
                  <Typography variant="caption" sx={{ display: "block", mt: 0.5, opacity: 0.8 }}>
                    {m.meta}
                  </Typography>
                )}
              </Paper>
            </Box>
          ))}
          {loading && (
            <Typography variant="caption" color="text.secondary">
              LLaMA 3 is generating response...
            </Typography>
          )}
        </Box>

        {pendingInteractionId && (
          <Card sx={{ mb: 2, bgcolor: "#fffbeb", border: "1px solid #f59e0b" }}>
            <CardContent>
              <Typography variant="subtitle2" fontWeight="bold" mb={1.5}>
                Mandatory Feedback Required to Unlock Input
              </Typography>
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2} mb={2}>
                <FormControl fullWidth size="small">
                  <InputLabel>Rating (1-4)</InputLabel>
                  <Select value={rating} label="Rating (1-4)" onChange={(e) => setRating(e.target.value)}>
                    <MenuItem value={1}>1</MenuItem>
                    <MenuItem value={2}>2</MenuItem>
                    <MenuItem value={3}>3</MenuItem>
                    <MenuItem value={4}>4</MenuItem>
                  </Select>
                </FormControl>

                <FormControl fullWidth size="small">
                  <InputLabel>Correctness</InputLabel>
                  <Select
                    value={correctness}
                    label="Correctness"
                    onChange={(e) => setCorrectness(e.target.value)}
                  >
                    <MenuItem value="Correct">Correct</MenuItem>
                    <MenuItem value="Partial">Partial</MenuItem>
                    <MenuItem value="Incorrect">Incorrect</MenuItem>
                  </Select>
                </FormControl>

                <FormControl fullWidth size="small">
                  <InputLabel>Length Type</InputLabel>
                  <Select
                    value={lengthType}
                    label="Length Type"
                    onChange={(e) => setLengthType(e.target.value)}
                  >
                    <MenuItem value="Short">Short</MenuItem>
                    <MenuItem value="To the Point">To the Point</MenuItem>
                    <MenuItem value="Lengthy">Lengthy</MenuItem>
                  </Select>
                </FormControl>
              </Stack>
              <Button variant="contained" color="success" onClick={submitFeedback}>
                Submit Feedback & Unlock
              </Button>
            </CardContent>
          </Card>
        )}

        <Stack direction="row" spacing={1}>
          <TextField
            fullWidth
            size="small"
            placeholder={
              pendingInteractionId
                ? "Submit feedback above to unlock input..."
                : "Type your message..."
            }
            value={inputText}
            disabled={isLocked}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") sendMessage();
            }}
          />
          <Button variant="contained" disabled={isLocked} onClick={sendMessage}>
            Send
          </Button>
        </Stack>
      </Paper>
    </Box>
  );
}
""",
}


def main():
    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)
    for file_path, content in files.items():
        file_path.write_text(content, encoding="utf-8")
    print("Clean project structure created successfully.")


if __name__ == "__main__":
    main()