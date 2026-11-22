import os
import requests
from dotenv import load_dotenv
from backend.classifier import topic_classifier

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


def summarize_old_history(old_turns: list[dict]) -> str:
    if not old_turns:
        return ""

    transcript = "\n".join(
        f"Turn {t['turn_number']} [{t.get('topic_label', 'General')}]: "
        f"User: {t['user_message']} | Assistant: {t['bot_response'][:250]}"
        for t in old_turns
    )

    try:
        res = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "Summarize prior chat turns concisely in 3-4 bullet points for context memory.",
                    },
                    {"role": "user", "content": transcript},
                ],
                "stream": False,
            },
            timeout=120,
        )
        res.raise_for_status()
        return res.json()["message"]["content"]
    except Exception:
        return "Previous discussion summarized due to topic shift."


def run_multi_turn_agent(history: list[dict], new_message: str) -> dict:
    current_topic = topic_classifier.predict(new_message)
    previous_topic = history[-1].get("topic_label") if history else None

    topic_shifted = bool(previous_topic and previous_topic != current_topic)
    agent_action = "standard_multi_turn"

    messages = [
        {
            "role": "system",
            "content": (
                "You are a multi-turn AI assistant specializing in Machine Learning, "
                "Deep Learning, Healthcare AI, Power Systems, and E-commerce AI. "
                f"Current detected topic: {current_topic}. Give clear, accurate answers."
            ),
        }
    ]

    if topic_shifted and len(history) > 2:
        older_turns = history[:-2]
        recent_turns = history[-2:]
        summary_text = summarize_old_history(older_turns)
        agent_action = f"topic_shift_summarized ({previous_topic} -> {current_topic})"
        messages.append({
            "role": "system",
            "content": f"Summary of earlier session context: {summary_text}",
        })
        for item in recent_turns:
            messages.append({"role": "user", "content": item["user_message"]})
            messages.append({"role": "assistant", "content": item["bot_response"]})
    else:
        if topic_shifted:
            agent_action = f"topic_shift_detected ({previous_topic} -> {current_topic})"
        for item in history[-6:]:
            messages.append({"role": "user", "content": item["user_message"]})
            messages.append({"role": "assistant", "content": item["bot_response"]})

    messages.append({"role": "user", "content": new_message})

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
    bot_reply = ollama_res.json()["message"]["content"]

    return {
        "response": bot_reply,
        "topic_label": current_topic,
        "topic_shifted": topic_shifted,
        "agent_action": agent_action,
        "turn_number": len(history) + 1,
    }
