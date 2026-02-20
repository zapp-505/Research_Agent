"""
present_node.py
Phase 2 of the state machine: Present the AI's interpretation to the user and wait.
Uses LangGraph's interrupt() to pause execution until the user responds.
The interrupt payload is what the FastAPI layer will surface to the frontend.
"""

from langgraph.types import interrupt
from src.Research_Agent.state.state import State


def present_node(state: State) -> dict:
    """
    Phase 2 Format the interpreted context and interrupt to get user confirmation.
    The value passed to interrupt() becomes the payload the API returns to the frontend.
    After the user replies, LangGraph resumes this node and returns the user's response
    in `user_response`.
    """
    ctx = state.get("interpreted_context")
    if ctx is None:
        raise ValueError("present_node called but interpreted_context is None")

    # Build a nice human-readable summary to show the user
    assumptions_text = "\n".join(f"  • {a}" for a in ctx.assumptions) or "  • None"

    summary = (
        f"📋 Here's what I understood:\n"
        f"  🔹 Domain:  {ctx.domain}\n"
        f"  🔹 Goal:    {ctx.interpreted_goal}\n"
        f"  🔹 Assumptions made:\n{assumptions_text}\n"
        f"  🔹 Confidence: {ctx.confidence.upper()}\n\n"
        f"❓ Is this correct? Reply 'yes' to proceed, or tell me what to change."
    )

    # interrupt() pauses the graph here — the payload is sent to the frontend
    user_response: str = interrupt({"summary": summary, "type": "confirmation"})

    # When resumed, user_response holds what the user typed
    return {"messages": [{"role": "assistant", "content": summary},
                         {"role": "user",      "content": user_response}]}
