"""
graph_builder.py
Wires together all nodes into the state-machine graph described in the architecture plan.

Graph flow:
  START → analyze → present → classify → [analyze (loop) | research] → END

The conditional edge out of classify_node reads `is_confirmed`:
  True  → research (done!)
  False → analyze  (loop back with corrections)
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.Research_Agent.state.state import State
from src.Research_Agent.nodes.analyze_node import analyze_node
from src.Research_Agent.nodes.present_node import present_node
from src.Research_Agent.nodes.classify_node import classify_node
from src.Research_Agent.nodes.research_node import research_node


def route_after_classify(state: State) -> str:
    """
    Conditional edge function: decides the next node after classify_node.
    Returns "research" if the user confirmed, else "analyze" to loop back.
    """
    if state.get("is_confirmed", False):
        return "research"
    return "analyze"


class GraphBuilder:
    """
    Builder class for creating and compiling the Research Agent LangGraph.
    """

    def __init__(self):
        #n-memory database for agent's conversation history
        self.memory = MemorySaver()

    def build(self):
        """
        Build and return the compiled LangGraph app with memory checkpointing.
        """
        workflow = StateGraph(State)

        
        workflow.add_node("analyze",  analyze_node)
        workflow.add_node("present",  present_node)
        workflow.add_node("classify", classify_node)
        workflow.add_node("research", research_node)

        
        workflow.add_edge(START,      "analyze")
        workflow.add_edge("analyze",  "present")
        workflow.add_edge("present",  "classify")

        workflow.add_conditional_edges(
            "classify",
            route_after_classify,
            {
                "research": "research",
                "analyze":  "analyze",
            },
        )

        workflow.add_edge("research", END)

        # Compile with MemorySaver so interrupt() / resume works across HTTP requests   
        return workflow.compile(checkpointer=self.memory)


# Module-level singleton — shared across all FastAPI requests
_graph_builder = GraphBuilder()
compiled_graph = _graph_builder.build()