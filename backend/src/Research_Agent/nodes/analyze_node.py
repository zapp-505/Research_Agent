"""
analyze_node.py
Phase 1 of the state machine: AI interprets raw user input into a structured context object.
Uses Groq's structured output (with_structured_output) to return a Pydantic model directly.
"""

from src.Research_Agent.state.state import State, InterpretedContext
from src.Research_Agent.LLMS.groqllm import get_llm


ANALYZE_PROMPT = """You are a requirements analyst. Given the user's raw input (and optional corrections from a previous round), your job is to:

1. IDENTIFY the domain and topic
2. DETECT any ambiguities or missing information
3. FILL IN gaps with the most reasonable assumptions
4. OUTPUT a structured interpretation

User Input: "{raw_input}"
Previous corrections from user (empty if first attempt): {user_corrections}

Output your analysis as a structured object with these fields:
- domain: the subject area (e.g. "Agricultural Drone Technology")
- interpreted_goal: a one-sentence description of what the user wants
- assumptions: a list of reasonable assumptions you made to fill in gaps
- confidence: your confidence level — "high", "medium", or "low"
"""


def analyze_node(state: State) -> dict:
    """
    Phase 1  Interpret the raw user input into a structured InterpretedContext.
    Returns a partial state update dict.
    """
    llm = get_llm(temperature=0.3)
    structured_llm = llm.with_structured_output(InterpretedContext)

    raw_input = state.get("raw_input", "")
    corrections = state.get("user_corrections", [])
    corrections_str = str(corrections) if corrections else "None"

    prompt = ANALYZE_PROMPT.format(
        raw_input=raw_input,
        user_corrections=corrections_str,
    )

    interpreted: InterpretedContext = structured_llm.invoke(prompt)

    return {
        "interpreted_context": interpreted,
        "iteration_count": state.get("iteration_count", 0) + 1,
    }
