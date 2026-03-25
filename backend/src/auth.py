import jwt
import os
import binascii
import base64
import hashlib
import hmac
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

try:
    import bcrypt
except Exception:
    bcrypt = None

SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is required but missing")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
PBKDF2_ITERATIONS = 390000

_bearer = HTTPBearer()

def verify_password(plain_password, hashed_password):
    if not hashed_password or not plain_password:
        return False

    if hashed_password.startswith("pbkdf2_sha256$"):
        return _verify_pbkdf2_password(plain_password, hashed_password)

    # Backward-compatible verification for legacy bcrypt hashes.
    if hashed_password.startswith("$2") and bcrypt is not None:
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except ValueError:
            # Some bcrypt backends error on >72-byte inputs instead of truncating.
            return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))

    return False

def get_password_hash(password):
    return _hash_pbkdf2_password(password)

def _hash_pbkdf2_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
        dklen=32,
    )
    salt_b64 = base64.b64encode(salt).decode("ascii")
    hash_b64 = base64.b64encode(dk).decode("ascii")
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt_b64}${hash_b64}"

def _verify_pbkdf2_password(password: str, stored_hash: str) -> bool:
    try:
        _, iterations_str, salt_b64, hash_b64 = stored_hash.split("$", 3)
        iterations = int(iterations_str)
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected_hash = base64.b64decode(hash_b64.encode("ascii"))
    except (ValueError, TypeError, binascii.Error):
        return False

    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
        dklen=len(expected_hash),
    )
    return hmac.compare_digest(candidate, expected_hash)

def create_access_token(data: dict):
    to_encode = data.copy()

    # Ensure JWT payload is JSON-serializable (important for Mongo ObjectId in `sub`)
    if "sub" in to_encode and to_encode["sub"] is not None:
        to_encode["sub"] = str(to_encode["sub"])
    if "email" in to_encode and to_encode["email"] is not None:
        to_encode["email"] = str(to_encode["email"])

    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    """
    Decodes the native PyJWT token sent from Streamlit.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        uid: str = payload.get("sub")
        email: str = payload.get("email")
        if uid is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        return {"uid": uid, "email": email}
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
