import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
REQUEST_TIMEOUT_SECONDS = int(os.environ.get("API_TIMEOUT_SECONDS", "30"))


class ApiError(Exception):
    pass


class AuthExpiredError(ApiError):
    pass


def _extract_error_message(response: requests.Response, fallback: str) -> str:
    try:
        payload = response.json()
        if isinstance(payload, dict):
            return payload.get("detail") or payload.get("message") or fallback
    except ValueError:
        pass
    return fallback


def _request(method: str, path: str, token: str | None = None, allow_statuses: set[int] | None = None, **kwargs):
    headers = kwargs.pop("headers", {})
    if token:
        headers.update(get_headers(token))

    try:
        response = requests.request(
            method,
            f"{BASE_URL}{path}",
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
            **kwargs,
        )
    except requests.RequestException as exc:
        raise ApiError("Could not reach backend API. Check if Uvicorn is running.") from exc

    if response.status_code == 401:
        raise AuthExpiredError("Your session expired. Please log in again.")

    if allow_statuses and response.status_code in allow_statuses:
        return response

    if not response.ok:
        raise ApiError(_extract_error_message(response, f"Request failed with status {response.status_code}"))

    if response.status_code == 204:
        return None

    try:
        return response.json()
    except ValueError as exc:
        raise ApiError("Backend returned a non-JSON response.") from exc

def get_headers(token: str):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def get_sessions(token: str):
    return _request("GET", "/sessions", token=token)

def get_session(token: str, session_id: str):
    response = _request("GET", f"/sessions/{session_id}", token=token, allow_statuses={404})
    if isinstance(response, requests.Response) and response.status_code == 404:
        return None
    return response

def delete_session(token: str, session_id: str):
    return _request("DELETE", f"/sessions/{session_id}", token=token)

def chat_start(token: str, query: str):
    return _request("POST", "/chat/start", token=token, json={"query": query})

def chat_resume(token: str, thread_id: str, user_response: str):
    return _request(
        "POST",
        "/chat/resume",
        token=token,
        json={"thread_id": thread_id, "user_response": user_response},
    )

def get_thread_history(token: str, thread_id: str):
    response = _request("GET", f"/chat/{thread_id}/history", token=token, allow_statuses={404})
    if isinstance(response, requests.Response) and response.status_code == 404:
        return {"messages": []}
    return response
