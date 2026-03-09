import uuid
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from langgraph.types import Command

from src.Research_Agent.graph.graph_builder import GraphBuilder
from backend.src.auth import get_current_user

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= Build the LangGraph agent once at startup =============
_builder = GraphBuilder()
agent = _builder.build()


# ============= Data Models =============
class ChatStartRequest(BaseModel):
    query: str

class ChatResumeRequest(BaseModel):
    thread_id: str
    user_response: str


# ============= Helpers =============
def _run_and_respond(config: dict) -> dict:
    """
    After invoking the agent, inspect the graph state to decide
    whether we are interrupted (waiting) or finished (complete).
    """
    state = agent.get_state(config)

    # Graph is paused at an interrupt() call → waiting for user input
    if state.next:
        # The interrupt payload is stored in the pending task's interrupts list
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

    # Graph ran to END → research complete
    final_state = state.values
    gathered = final_state.get("gathered_data", [])
    if gathered:
        message = "\n\n".join(gathered)
    else:
        # Fallback: last assistant message in state
        msgs = final_state.get("messages", [])
        ai_msgs = [m for m in msgs if m.get("role") in ("assistant", "ai")]
        message = ai_msgs[-1].get("content", "Research complete.") if ai_msgs else "Research complete."

    return {
        "status": "complete",
        "message": message,
        "thread_id": config["configurable"]["thread_id"],
    }


# ============= Endpoints =============
@app.get("/index")
def index():
    return {"message": "Welcome to the Research Agent API"}


@app.get("/auth/verify")
def auth_verify(user: dict = Depends(get_current_user)):
    """
    Verifies the Firebase ID token supplied as `Authorization: Bearer <token>`.
    Returns basic profile info from the token claims.
    """
    return {
        "uid": user["uid"],
        "email": user.get("email"),
        "name": user.get("name"),
    }


@app.post("/chat/start")
def chat_start(request: ChatStartRequest, user: dict = Depends(get_current_user)):
    """
    Begin a new agent conversation.
    Creates a fresh thread, runs the graph until it either interrupts
    (waiting for user confirmation) or completes.
    """
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "raw_input": request.query,
        "messages": [],
        "gathered_data": [],
        "is_confirmed": False,
        "iteration_count": 0,
        "user_corrections": [],
        "interpreted_context": None,
    }

    try:
        agent.invoke(initial_state, config)
    except Exception as exc:
        # LangGraph surfaces interrupts as exceptions in some versions — safe to ignore
        pass

    return _run_and_respond(config)


@app.post("/chat/resume")
def chat_resume(request: ChatResumeRequest, user: dict = Depends(get_current_user)):
    """
    Resume a paused agent conversation.
    Passes the user's reply back via Command(resume=...) and runs until
    the next interrupt or until the graph finishes.
    """
    config = {"configurable": {"thread_id": request.thread_id}}

    # Verify thread exists
    try:
        state = agent.get_state(config)
    except Exception:
        raise HTTPException(status_code=404, detail="Thread not found")

    if not state.next:
        raise HTTPException(status_code=400, detail="No active interrupt on this thread")

    try:
        agent.invoke(Command(resume=request.user_response), config)
    except Exception:
        pass

    return _run_and_respond(config)
