from fastapi import APIRouter, Depends

from src.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/verify")
def auth_verify(user: dict = Depends(get_current_user)):
    return {
        "uid": user["uid"],
        "email": user.get("email"),
        "name": user.get("name"),
    }
