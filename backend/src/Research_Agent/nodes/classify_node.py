"""
classify_node.py
Phase 3 – Routing Decision: classify user's reply as CONFIRMED, CORRECTED, or REJECTED.
Uses the LLM to intelligently parse natural-language confirmations/corrections.
"""

from typing import Literal
from src.Research_Agent.state.state import State
from src.Research_Agent.LLMS.groqllm import get_llm
from langchain_core.messages import HumanMessage, AIMessage


CLASSIFY_PROMPT = """The user was shown an interpretation of their request and asked to confirm it.
They responded: "{user_response}"

Classify this response as exactly ONE of:
- CONFIRMED  (they agree with the interpretation, e.g. "yes", "looks good", "correct", "that's right")
- CORRECTED  (they provided corrections or additional info, e.g. "no, I meant...", "actually...", "change X to Y")
- REJECTED   (they want to start completely over, e.g. "no, forget it", "start over", "that's completely wrong")

Reply with ONLY the single word: CONFIRMED, CORRECTED, or REJECTED."""


def classify_node(state: State) -> dict:
    """
    Phase 3 – Read the last user message (their response to our interpretation)
    and decide what to do next. Stores classification in is_confirmed and may
    append a user correction.
    """
    llm = get_llm(temperature=0.0)

    # The last message in state.messages is the user's reply to our summary
    messages = state.get("messages", [])
    user_response = ""
    for msg in reversed(messages):
        # Support both dict-style (from our present_node) and BaseMessage objects
        if isinstance(msg, dict):
            if msg.get("role") == "user":
                user_response = msg.get("content", "")
                break
        elif isinstance(msg, HumanMessage):
            user_response = msg.content
            break

    if not user_response:
        # Default to asking again if we can't read the response
        return {"is_confirmed": False}

    prompt = CLASSIFY_PROMPT.format(user_response=user_response)
    classification = llm.invoke(prompt).content.strip().upper()

    # Normalize — sometimes the LLM wraps it in extra text
    if "CONFIRMED" in classification:
        return {"is_confirmed": True}
    elif "REJECTED" in classification:
        # Treat rejection as a reset — clear corrections and context
        return {
            "is_confirmed": False,
            "interpreted_context": None,
            "user_corrections": [],   # operator.add won't help here, but graph resets this
        }
    else:
        # CORRECTED — add the user's message as a correction for the next analyze pass
        return {
            "is_confirmed": False,
            "user_corrections": [user_response],  # operator.add appends this
        }
