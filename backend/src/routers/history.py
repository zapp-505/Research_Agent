from fastapi import APIRouter, Depends

from src.auth import get_current_user
from src.db.chat_history import get_chat_history, get_chat_summary, delete_chat_history

router = APIRouter(prefix="/chat", tags=["history"])


@router.get("/{thread_id}/history")
async def get_thread_history(thread_id: str, user: dict = Depends(get_current_user)):
    messages = await get_chat_history(thread_id)
    return {
        "thread_id": thread_id,
        "message_count": len(messages),
        "messages": messages,
    }


@router.get("/{thread_id}/summary")
async def get_thread_summary(thread_id: str, user: dict = Depends(get_current_user)):
    summary = await get_chat_summary(thread_id)
    return summary


@router.delete("/{thread_id}/history")
async def delete_thread_history(thread_id: str, user: dict = Depends(get_current_user)):
    deleted = await delete_chat_history(thread_id)
    return {
        "thread_id": thread_id,
        "deleted": deleted,
        "message": "Chat history deleted." if deleted else "No history found to delete.",
    }
