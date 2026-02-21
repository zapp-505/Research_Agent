"""
state.py
Central state definition for the Research Agent graph.
All nodes read from and write to this TypedDict.

NOTE: We use operator.add for messages (simple list append) instead of
langgraph's add_messages to avoid the jsonpatch transitive dependency.
"""

from typing import Annotated, Literal, List, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel
import operator


class InterpretedContext(BaseModel):
    """Structured output from the analyze node — parsed via Groq structured output."""
    domain: str
    interpreted_goal: str
    assumptions: list[str]
    confidence: Literal["high", "medium", "low"]


class State(TypedDict):
    """
    Shared state that flows through every node in the graph.

    raw_input           – The user's original, unprocessed query.
    messages            – Simple list of {"role": str, "content": str} dicts.
    interpreted_context – Pydantic model produced by the analyze node.
    gathered_data       – Accumulated research output (append-only).
    is_confirmed        – True once the user confirms the interpretation.
    iteration_count     – Number of analyze→present→classify loops completed.
    user_corrections    – Corrections fed back into each analyze pass (append-only).
    """
    raw_input:           str
    messages:            Annotated[List[dict], operator.add]
    interpreted_context: Optional[InterpretedContext]
    gathered_data:       Annotated[List[str], operator.add]
    is_confirmed:        bool
    iteration_count:     int
    user_corrections:    Annotated[List[str], operator.add]


# Alias kept for any legacy references
AgentState = State