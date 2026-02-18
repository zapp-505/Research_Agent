
from typing import Annotated, Literal, List
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
import operator

class InterpretedContext(BaseModel):
    domain: str
    interpreted_goal: str
    assumptions: list[str]
    confidence: Literal["high", "medium", "low"]

class State(TypedDict):
    """
    Represent the structure of the state used in graph
    """
    raw_input: str
    messages: Annotated[List[BaseMessage],add_messages]
    interpreted_context: InterpretedContext | None
    gathered_data: Annotated[List,operator.add]
    is_confirmed: bool
    iteration_count: int
    user_corrections: Annotated[list[str], operator.add]