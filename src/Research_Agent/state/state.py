"""
State management for the LangGraph application
"""

from typing import TypedDict, Optional


class AgentState(TypedDict):
    """
    State schema for the agent
    """
    user_input: Optional[str]
    bot_response: Optional[str]
    messages: list
    intermediate_steps: list


def create_initial_state():
    """
    Create and return initial state
    """
    return AgentState(
        user_input=None,
        bot_response=None,
        messages=[],
        intermediate_steps=[]
    )
