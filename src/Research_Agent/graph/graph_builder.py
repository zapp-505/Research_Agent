from langgraph.graph import StateGraph
from src.Research_Agent.state.state import AgentState
from langgraph.graph import START,END
class GraphBuilder:
    """
    Builder class for creating and managing LangGraph graphs
    """
    
    def __init__(self,model):
        self.llm = model
        self.graph_builder = StateGraph(AgentState)
    
    def build(self):
        """
        Build and return the graph
        """
        self.graph_builder.add_node()
        self.graph_builder.add_edge(START,)