"""
state.py
Central state definition for the Research Agent graph.
All nodes read from and write to this TypedDict.

messages          — plain dict list for the UI chat log (existing nodes).
research_thread   — LangChain Message objects used by research_node + its ToolNode.
synthesis_thread  — LangChain Message objects used by blue_team_node + its ToolNode.

Keeping the two concerns separate means:
  - Existing nodes (analyze, present, classify, expert) stay completely unchanged.
  - ToolNode instances each point to their own thread field, not the shared chat log.
"""

from typing import Annotated, Literal, List, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel
import operator
from langgraph.graph.message import add_messages


class InterpretedContext(BaseModel):
    """Structured output from the analyze node — parsed via Groq structured output."""
    domain: str
    interpreted_goal: str
    assumptions: list[str]
    confidence: Literal["high", "medium", "low"]

class Persona(BaseModel):
    domain: str
    name: str
    system_prompt: str
    role: str

class PanelOutput(BaseModel):
    """Wrapper so with_structured_output() can return a list of Persona objects."""
    personas: list[Persona]

class State(TypedDict):
    """
    Shared state that flows through every node in the graph.

    raw_input           - The user's original, unprocessed query.
    messages            – Simple list of {"role": str, "content": str} dicts.
    interpreted_context – Pydantic model produced by the analyze node.
    gathered_data       – Accumulated research output (append-only).
    is_confirmed        – True once the user confirms the interpretation.
    iteration_count     – Number of analyze→present→classify loops completed.
    user_corrections    – Corrections fed back into each analyze pass (append-only).
    the type declaration specifies what values field is allowed to hold. msgs, gathered etc are never none and always lists, but interprtcon is diff and as no context is there unless an analysis is performedtherefore optional or else a dummy instance of i_c would be created of the class

    each node then fills in whatever part of the dict it is responsibe for 
    """
    raw_input:           str
    messages:            Annotated[List[dict], operator.add]  # UI chat log — plain dicts
    interpreted_context: Optional[InterpretedContext]
    gathered_data:       Annotated[List[str], operator.add]
    is_confirmed:        bool
    iteration_count:     int
    user_corrections:    Annotated[List[str], operator.add]
    personas:            Optional[List[Persona]]
    current_speaker_idx: int
    round_number:        int
    expert_critique:     Annotated[List[dict], operator.add]
    is_gauntlet_complete: bool
    final_report:        Optional[str]

    # ── Internal LLM conversation threads for tool-using agents ──────────
    # These hold proper LangChain Message objects (HumanMessage, AIMessage,
    # ToolMessage) so that LangGraph's ToolNode can read and write them.
    # ToolNode for research points here; ToolNode for blue_team points to synthesis_thread.
    research_thread:     Annotated[list, add_messages]
    synthesis_thread:    Annotated[list, add_messages]


# Alias kept for any legacy references
AgentState = State