import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

def get_headers(token: str):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def get_sessions(token: str):
    response = requests.get(f"{BASE_URL}/sessions", headers=get_headers(token))
    response.raise_for_status()
    return response.json()

def get_session(token: str, session_id: str):
    response = requests.get(f"{BASE_URL}/sessions/{session_id}", headers=get_headers(token))
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()

def delete_session(token: str, session_id: str):
    response = requests.delete(f"{BASE_URL}/sessions/{session_id}", headers=get_headers(token))
    response.raise_for_status()
    return response.json()

def chat_start(token: str, query: str):
    response = requests.post(
        f"{BASE_URL}/chat/start",
        headers=get_headers(token),
        json={"query": query}
    )
    response.raise_for_status()
    return response.json()

def chat_resume(token: str, thread_id: str, user_response: str):
    response = requests.post(
        f"{BASE_URL}/chat/resume",
        headers=get_headers(token),
        json={"thread_id": thread_id, "user_response": user_response}
    )
    response.raise_for_status()
    return response.json()

def get_thread_history(token: str, thread_id: str):
    response = requests.get(f"{BASE_URL}/chat/{thread_id}/history", headers=get_headers(token))
    if response.status_code == 404:
        return {"messages": []}
    response.raise_for_status()
    return response.json()
