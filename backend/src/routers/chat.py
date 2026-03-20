import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from langgraph.types import Command
from pydantic import BaseModel

from src.auth import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatStartRequest(BaseModel):
    query: str


class ChatResumeRequest(BaseModel):
    thread_id: str
    user_response: str


def _run_and_respond(agent, config: dict) -> dict:
    state = agent.get_state(config)

    if state.next:
        try:
            interrupt_value = state.tasks[0].interrupts[0].value
            message = interrupt_value.get("summary", str(interrupt_value))
        except (IndexError, AttributeError, KeyError):
            message = "Please confirm or correct the interpretation above."
        return {
            "status": "waiting",
            "message": message,
            "thread_id": config["configurable"]["thread_id"],
        }

    final_state = state.values
    gathered = final_state.get("gathered_data", [])
    if gathered:
        message = "\n\n".join(gathered)
    else:
        msgs = final_state.get("messages", [])
        ai_msgs = [m for m in msgs if m.get("role") in ("assistant", "ai")]
        message = ai_msgs[-1].get("content", "Research complete.") if ai_msgs else "Research complete."

    return {
        "status": "complete",
        "message": message,
        "thread_id": config["configurable"]["thread_id"],
    }


@router.post("/start")
def chat_start(payload: ChatStartRequest, req: Request, user: dict = Depends(get_current_user)):
    agent = getattr(req.app.state, "agent", None)
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "raw_input": payload.query,
        "messages": [],
        "gathered_data": [],
        "is_confirmed": False,
        "iteration_count": 0,
        "user_corrections": [],
        "interpreted_context": None,
    }

    try:
        agent.invoke(initial_state, config)
    except Exception:
        pass

    return _run_and_respond(agent, config)


@router.post("/resume")
def chat_resume(payload: ChatResumeRequest, req: Request, user: dict = Depends(get_current_user)):
    agent = getattr(req.app.state, "agent", None)
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    config = {"configurable": {"thread_id": payload.thread_id}}

    try:
        state = agent.get_state(config)
    except Exception:
        raise HTTPException(status_code=404, detail="Thread not found")

    if not state.next:
        raise HTTPException(status_code=400, detail="No active interrupt on this thread")

    try:
        agent.invoke(Command(resume=payload.user_response), config)
    except Exception:
        pass

    return _run_and_respond(agent, config)
