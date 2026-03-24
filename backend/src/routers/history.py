from fastapi import APIRouter, Depends, HTTPException, Request

from src.auth import get_current_user
from src.db.chat_history import get_thread_messages, get_chat_summary, get_thread_report
from src.db.session_store import get_session

router = APIRouter(prefix="/chat", tags=["history"])


@router.get("/{thread_id}/history")
async def get_thread_history(thread_id: str, req: Request, user: dict = Depends(get_current_user)):
    agent = req.app.state.agent
    session = await get_session(thread_id, user["uid"])
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or not owned by user")

    messages = await get_thread_messages(agent, thread_id)
    return {
        "thread_id": thread_id,
        "message_count": len(messages),
        "messages": messages,
    }


@router.get("/{thread_id}/summary")
async def get_thread_summary_route(thread_id: str, req: Request, user: dict = Depends(get_current_user)):
    agent = req.app.state.agent
    session = await get_session(thread_id, user["uid"])
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or not owned by user")

    summary = await get_chat_summary(agent, thread_id)
    return summary

@router.get("/{thread_id}/report")
async def get_thread_report_route(thread_id: str, req: Request, user: dict = Depends(get_current_user)):
    agent = req.app.state.agent
    session = await get_session(thread_id, user["uid"])
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or not owned by user")

    report = await get_thread_report(agent, thread_id)
    return {"thread_id": thread_id, "report": report}
