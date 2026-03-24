from fastapi import APIRouter, Depends, HTTPException
from src.auth import get_current_user
from src.db import session_store

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("")
async def list_sessions(user: dict = Depends(get_current_user)):
    return await session_store.get_sessions(user["uid"])


@router.get("/{session_id}")
async def get_session(session_id: str, user: dict = Depends(get_current_user)):
    session = await session_store.get_session(session_id, user["uid"])
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/{session_id}")
async def delete_session(session_id: str, user: dict = Depends(get_current_user)):
    deleted = await session_store.delete_session(session_id, user["uid"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "ok", "deleted": True}
