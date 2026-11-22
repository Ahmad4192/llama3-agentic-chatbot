# Multi-Turn Agentic Chatbot with Local LLaMA 3

A full-stack, containerized multi-turn agentic chatbot built with **Next.js**, **Material UI**, **Recharts**, **FastAPI**, **MongoDB**, and local **Ollama (`llama3`)**. The system tracks conversation context, detects topic shifts across turns, enforces a mandatory feedback loop, and renders live session analytics.

## Key Features
- **Multi-Turn Agentic Workflow:** Maintains conversational context across turns and triggers topic-shift detection (e.g., `Deep Learning -> Machine Learning`).
- **Mandatory Feedback Loop:** Collects turn-level ratings (1–4), correctness status, and length preference before advancing.
- **Real-Time Session Analytics Dashboard:** Displays summary metrics along with **7 charts** and **6 tables** covering correctness, phase-wise accuracy, response latency, ratings, and length preferences.
- **Containerized Setup:** Orchestrated with Docker Compose (`mongodb`, `backend`, `frontend`) while connecting to local Ollama (`llama3`).

## Tech Stack
- **Frontend:** Next.js, Material UI, Recharts
- **Backend:** Python, FastAPI
- **Database:** MongoDB
- **LLM Runtime:** Ollama (`llama3`)
- **Containerization:** Docker, Docker Compose

## Docker Hub Images
- **Frontend:** https://hub.docker.com/r/ahmad808/llama3-agentic-chatbot-frontend[cite: 1]
- **Backend:** https://hub.docker.com/r/ahmad808/llama3-agentic-chatbot-backend[cite: 1]

## Running the Project
1. Ensure **Ollama** is running locally with the `llama3` model pulled (`ollama pull llama3`).
2. Start the services using Docker Compose:
   ```bash
   docker compose up -d
