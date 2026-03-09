import firebase_admin
from firebase_admin import credentials, auth
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.config import FIREBASE_SERVICE_ACCOUNT

# Initialise the Firebase Admin SDK once at import time.
# If FIREBASE_SERVICE_ACCOUNT is a path to a service-account JSON file, use it;
# otherwise fall back to Application Default Credentials (useful on GCP / Cloud Run).
if not firebase_admin._apps:
    if FIREBASE_SERVICE_ACCOUNT:
        cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT)
    else:
        cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)

_bearer = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    """
    FastAPI dependency that verifies a Firebase ID token sent as
    `Authorization: Bearer <id_token>` and returns the decoded token claims.
    Raises HTTP 401 on any failure.
    """
    token = credentials.credentials
    try:
        decoded = auth.verify_id_token(token)
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    return decoded
