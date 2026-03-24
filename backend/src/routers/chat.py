import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from langgraph.types import Command
from pydantic import BaseModel

from src.auth import get_current_user
from src.db.session_store import create_session, get_session, update_session

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)

class ChatStartRequest(BaseModel):
    query: str

class ChatResumeRequest(BaseModel):
    thread_id: str
    user_response: str

async def _run_and_respond(agent, config: dict, session_id: str, user_id: str) -> dict:
    state = await agent.aget_state(config)

    if state.next:
        interrupt_val = state.tasks[0].interrupts[0].value if state.tasks[0].interrupts else {}
        interrupt_type = interrupt_val.get("type", "unknown")
        message = interrupt_val.get("summary", str(interrupt_val))
        
        await update_session(session_id, user_id, {"agent_phase": "waiting"})
        
        return {
            "status": "waiting",
            "interrupt_type": interrupt_type,
            "message": message,
            "expert_name": interrupt_val.get("expert_name"),
            "expert_role": interrupt_val.get("expert_role"),
            "thread_id": config["configurable"]["thread_id"],
            "round_number": interrupt_val.get("round_number", state.values.get("round_number")) if state.values else None
        }
    else:
        final_report = state.values.get("final_report") if state.values else None
        await update_session(session_id, user_id, {"agent_phase": "complete"})
        
        return {
            "status": "complete",
            "interrupt_type": None,
            "message": None,
            "final_report": final_report,
            "thread_id": config["configurable"]["thread_id"]
        }


@router.post("/start")
async def chat_start(payload: ChatStartRequest, req: Request, user: dict = Depends(get_current_user)):
    agent = getattr(req.app.state, "agent", None)
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    # 1. Create DB Session
    title = payload.query[:60]
    session = await create_session(user["uid"], title)
    thread_id = session["thread_id"]
    config = {"configurable": {"thread_id": thread_id}}

    # 2. Initial state
    initial_state = {
        "raw_input":            payload.query,
        "messages":             [{"role": "user", "content": payload.query}],
        "interpreted_context":  None,
        "is_confirmed":         False,
        "iteration_count":      0,
        "user_corrections":     [],
        "personas":             None,
        "current_speaker_idx":  0,
        "round_number":         0,
        "expert_critique":      [],
        "is_gauntlet_complete": False,
        "final_report":         None,
        "synthesis_thread":     [],
    }

    try:
        # Run graph
        async for _ in agent.astream(initial_state, config):
            pass
    except Exception as e:
        logger.error(f"Error during agent execution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during agent execution.")

    return await _run_and_respond(agent, config, session["_id"], user["uid"])


@router.post("/resume")
async def chat_resume(payload: ChatResumeRequest, req: Request, user: dict = Depends(get_current_user)):
    agent = getattr(req.app.state, "agent", None)
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    # Verify session
    session = await get_session(payload.thread_id, user["uid"])
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or not owned by user")
        
    if session.get("agent_phase") == "complete":
        raise HTTPException(status_code=400, detail="Cannot resume a complete graph")

    config = {"configurable": {"thread_id": payload.thread_id}}

    try:
        state = await agent.aget_state(config)
    except Exception as e:
        logger.error(f"State fetch error: {e}")
        raise HTTPException(status_code=404, detail="Thread state not found")

    if not state.next:
        raise HTTPException(status_code=400, detail="No active interrupt on this thread")

    try:
        async for _ in agent.astream(Command(resume=payload.user_response), config):
            pass
    except Exception as e:
        logger.error(f"Error during agent resumption: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during resumption.")

    return await _run_and_respond(agent, config, session["_id"], user["uid"])
