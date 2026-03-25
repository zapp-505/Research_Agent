import pyrebase
import os
from dotenv import load_dotenv

load_dotenv()

# Streamlit uses .env file or st.secrets. We will rely on .env for local.
firebase_config = {
    "apiKey": os.environ.get("FIREBASE_API_KEY", ""),
    "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN", ""),
    "projectId": os.environ.get("FIREBASE_PROJECT_ID", ""),
    "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET", ""),
    "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID", ""),
    "appId": os.environ.get("FIREBASE_APP_ID", ""),
    "databaseURL": os.environ.get("FIREBASE_DATABASE_URL", "") # Required by Pyrebase even if empty
}

# Only initialize if api key is provided, so it doesn't crash during mock auth periods
if firebase_config["apiKey"]:
    firebase = pyrebase.initialize_app(firebase_config)
    auth_client = firebase.auth()
else:
    auth_client = None

def sign_in(email, password):
    if not auth_client:
        # Mock mode
        return {"idToken": "YOUR_FIREBASE_ID_TOKEN", "localId": "test-user-12345", "email": email}
    return auth_client.sign_in_with_email_and_password(email, password)

def sign_up(email, password):
    if not auth_client:
        # Mock mode
        return {"idToken": "YOUR_FIREBASE_ID_TOKEN", "localId": "test-user-12345", "email": email}
    # Pyrebase handles the creation
    user = auth_client.create_user_with_email_and_password(email, password)
    # Immediately sign them in to get the token
    return sign_in(email, password)
