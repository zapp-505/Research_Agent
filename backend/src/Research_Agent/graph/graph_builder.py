"""
graph_builder.py
Wires all nodes into the Gauntlet state-machine graph.

Full flow:
  START → analyze → present (interrupt) → classify
                        ↑                     │
                        └────── CORRECTED ─────┘
                                              │ CONFIRMED
                                              ▼
                                      panel_generator
                                              │
                                              ▼
                               ┌──────► moderator ◄──────────────┐
                               │             │                    │
                               │      ┌──────┴───────┐           │
                               │  TERMINATE       CONTINUE       │
                               │      │               │           │
                               │      ▼               ▼           │
                               │  blue_team         expert        │
                               │      │          (interrupt)      │
                               │      │               │           │
                               │  [tool loop]  [user responds]   │
                               │      │               └───────────┘
                               │      ▼
                               └───► END
"""

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph_checkpoint_mongodb import AsyncMongoDBSaver

from src.db.mongo_client import MongoDB
from src.Research_Agent.state.state import State
from src.Research_Agent.nodes.analyze_node import analyze_node
from src.Research_Agent.nodes.present_node import present_node
from src.Research_Agent.nodes.classify_node import classify_node
from src.Research_Agent.nodes.panel_generator_node import panel_generator_node
from src.Research_Agent.nodes.expert_node import expert_node
from src.Research_Agent.nodes.moderator_node import moderator_node
from src.Research_Agent.nodes.blueteam_node import blue_team_node


# ── Load Tavily tools once at module level ────────────────────────────────────
# Loaded here rather than inside nodes so ToolNode and both LLMs share the same
# tool instances. Wrapped in try/except — app works without Tavily configured.
_tools = []
try:
    from src.Research_Agent.tools.search_tool import search_tool
    _tools = search_tool()
except Exception:
    pass   # Tavily not installed or API key missing — tool nodes are skipped


# ── Routing functions ─────────────────────────────────────────────────────────

def route_after_classify(state: State) -> str:
    """After classify_node: confirmed → start gauntlet, else → re-analyze."""
    if state.get("is_confirmed", False):
        return "panel_generator"
    return "analyze"


def route_after_moderator(state: State) -> str:
    """After moderator_node: all rounds done → synthesize, else → next expert."""
    if state.get("is_gauntlet_complete", False):
        return "blue_team"
    return "expert"


def route_after_blue_team(state: State) -> str:
    """After blue_team_node: if LLM made tool calls → run synthesis_tools, else → done."""
    thread = state.get("synthesis_thread", [])
    last   = thread[-1] if thread else None
    if getattr(last, "tool_calls", None):
        return "synthesis_tools"
    return "__end__"


# ── GraphBuilder ──────────────────────────────────────────────────────────────

class GraphBuilder:
    """Builds and compiles the Research Agent LangGraph with MongoDB checkpointing."""

    def __init__(self):
        # AsyncMongoDBSaver replaces MemorySaver — state is persisted to MongoDB
        # so sessions survive server restarts and can be resumed by thread_id.
        self.memory = AsyncMongoDBSaver(MongoDB.client)

    def build(self):
        """Build and return the compiled LangGraph app."""
        workflow = StateGraph(State)

        
        workflow.add_node("analyze",  analyze_node)
        workflow.add_node("present",  present_node)
        workflow.add_node("classify", classify_node)
        workflow.add_node("panel_generator", panel_generator_node)
        workflow.add_node("moderator", moderator_node)
        workflow.add_node("expert", expert_node)
        workflow.add_node("blue_team", blue_team_node)

        # ToolNode for blue_team's web searches — only added when Tavily is available.
        # messages_key="synthesis_thread" tells ToolNode to read tool_calls from
        # state["synthesis_thread"] and write ToolMessage results back there.
        if _tools:
            workflow.add_node(
                "synthesis_tools",
                ToolNode(_tools, messages_key="synthesis_thread"),
            )

        # ── Phase A: Intake & Confirmation (fixed edges) ──────────────────────
        workflow.add_edge(START,      "analyze")
        workflow.add_edge("analyze",  "present")
        workflow.add_edge("present",  "classify")

        workflow.add_conditional_edges(
            "classify",
            route_after_classify,
            {
                "panel_generator": "panel_generator",
                "analyze":         "analyze",
            },
        )

        # ── Phase B: The Gauntlet ─────────────────────────────────────────────
        workflow.add_edge("panel_generator", "moderator")   # always goes to moderator first

        # moderator → expert (continue) OR blue_team (all rounds done)
        workflow.add_conditional_edges(
            "moderator",
            route_after_moderator,
            {
                "expert":    "expert",
                "blue_team": "blue_team",
            },
        )

        # expert always loops back to moderator after interrupt + user response
        workflow.add_edge("expert", "moderator")

        # ── Phase C: Synthesis ────────────────────────────────────────────────
        if _tools:
            # blue_team may trigger tool calls → synthesis_tools → back to blue_team
            workflow.add_conditional_edges(
                "blue_team",
                route_after_blue_team,
                {
                    "synthesis_tools": "synthesis_tools",
                    "__end__":         END,
                },
            )
            workflow.add_edge("synthesis_tools", "blue_team")
        else:
            # No tools available — blue_team writes report directly and ends
            workflow.add_edge("blue_team", END)

        return workflow.compile(checkpointer=self.memory)