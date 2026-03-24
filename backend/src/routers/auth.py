from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from src.auth import get_current_user, get_password_hash, verify_password, create_access_token
from src.db.user_store import get_user_by_email, create_user

router = APIRouter(prefix="/auth", tags=["auth"])

class UserCredentials(BaseModel):
    email: str
    password: str

@router.post("/register")
async def register(creds: UserCredentials):
    existing = await get_user_by_email(creds.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_pwd = get_password_hash(creds.password)
    user = await create_user(creds.email, hashed_pwd)
    
    # Returning the payload matching pyrebase so frontend UI handles it smoothly
    access_token = create_access_token(data={"sub": user["uid"], "email": user["email"]})
    return {"idToken": access_token, "localId": user["uid"], "email": user["email"]}

@router.post("/login")
async def login(creds: UserCredentials):
    user = await get_user_by_email(creds.email)
    if not user or not verify_password(creds.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
        
    access_token = create_access_token(data={"sub": user["uid"], "email": user["email"]})
    return {"idToken": access_token, "localId": user["uid"], "email": user["email"]}

@router.get("/verify")
def auth_verify(user: dict = Depends(get_current_user)):
    return {
        "uid": user["uid"],
        "email": user.get("email")
    }
