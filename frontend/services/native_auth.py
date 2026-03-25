import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

def sign_in(email, password):
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )
    if response.status_code != 200:
        raise Exception(response.json().get("detail", "Login failed"))
    return response.json()

def sign_up(email, password):
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": email, "password": password}
    )
    if response.status_code != 200:
        raise Exception(response.json().get("detail", "Registration failed"))
    return response.json()
