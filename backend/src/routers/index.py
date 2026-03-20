from fastapi import APIRouter

router = APIRouter()


@router.get("/index")
def index():
    return {"message": "Welcome to the Research Agent API"}
