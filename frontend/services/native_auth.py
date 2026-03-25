import requests
import os
from dotenv import load_dotenv
from services.api import ApiError

load_dotenv()

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
REQUEST_TIMEOUT_SECONDS = int(os.environ.get("API_TIMEOUT_SECONDS", "30"))


def _error_message(response: requests.Response, fallback: str) -> str:
    try:
        payload = response.json()
        if isinstance(payload, dict):
            return payload.get("detail") or payload.get("message") or fallback
    except ValueError:
        pass
    return fallback

def sign_in(email, password):
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise ApiError("Could not reach backend API. Check if Uvicorn is running.") from exc

    if response.status_code != 200:
        raise ApiError(_error_message(response, "Login failed"))
    return response.json()

def sign_up(email, password):
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={"email": email, "password": password},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise ApiError("Could not reach backend API. Check if Uvicorn is running.") from exc

    if response.status_code != 200:
        raise ApiError(_error_message(response, "Registration failed"))
    return response.json()
