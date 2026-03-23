"""
research_node.py
Phase 4 — Generate a comprehensive research summary based on confirmed context.

Uses LangGraph's ToolNode pattern:
  - Writes to state["research_thread"] (LangChain Message objects)
  - A separate ToolNode(tools, messages_key="research_thread") in graph_builder
    executes any tool calls the LLM makes and writes results back
  - This node is re-invoked after each tool execution until LLM produces plain text

The main state["messages"] (UI chat log) is only updated once, at the end,
with the final research output.
"""

from langchain_core.messages import HumanMessage

from src.Research_Agent.state.state import State
from src.Research_Agent.LLMS.groqllm import get_llm
from src.logging.logger import logger


RESEARCH_PROMPT = """You are a world-class research assistant with access to a web search tool.
Based on the confirmed requirements below, generate a comprehensive research summary.

Use the search tool when you need current data, statistics, or real-world examples to
ground your claims. Only search when it materially improves accuracy — do not search
for everything.

CONFIRMED REQUIREMENTS:
- Domain:      {domain}
- Goal:        {interpreted_goal}
- Assumptions: {assumptions}

Produce a structured research summary with:
1. **Executive Overview**     — A clear, concise description of the topic.
2. **Key Facts & Insights**   — The most important, accurate, up-to-date information.
3. **Sub-Topics Explored**    — Break down the domain into relevant sub-areas.
4. **Practical Applications** — Real-world use cases and examples.
5. **Recommended Next Steps** — What the user should explore or do next.

Make this thorough, informative, and actionable. Use markdown formatting."""


def research_node(state: State) -> dict:
    """
    Runs every time the graph enters this node — either fresh or after a ToolNode execution.

    First entry:  research_thread is empty → build the prompt and start the conversation.
    Re-entry:     research_thread has tool results → pass full thread to LLM to continue.
    """
    logger.info("Research Node Entered")

    ctx = state.get("interpreted_context")
    if ctx is None:
        return {"gathered_data": ["Error: No confirmed context found."]}

    thread = state.get("research_thread", [])

    llm = get_llm(temperature=0.7)

    # Bind Tavily if available
    try:
        from src.Research_Agent.tools.search_tool import search_tool
        tools          = search_tool()
        llm_with_tools = llm.bind_tools(tools)
        logger.info("Tavily bound to research LLM")
    except Exception:
        llm_with_tools = llm
        logger.info("Tavily unavailable — research proceeds without web search")

    if not thread:
        # ── First entry: start a fresh conversation ────────────────────────
        assumptions_str = ", ".join(ctx.assumptions) if ctx.assumptions else "None"
        prompt      = RESEARCH_PROMPT.format(
            domain           = ctx.domain,
            interpreted_goal = ctx.interpreted_goal,
            assumptions      = assumptions_str,
        )
        thread = [HumanMessage(content=prompt)]

    # Invoke LLM with the full thread (includes any ToolMessages on re-entry)
    response = llm_with_tools.invoke(thread)
    logger.info(f"Research LLM responded — tool_calls: {bool(getattr(response, 'tool_calls', None))}")

    # Write AIMessage (possibly with tool_calls) back to research_thread.
    # If tool_calls exist, graph_builder routes to the research ToolNode,
    # which executes the tools and appends ToolMessages to research_thread,
    # then routes back here. If no tool_calls, graph routes to next node.
    update = {"research_thread": [*thread, response] if not state.get("research_thread") else [response]}

    # Only write the final output to the UI chat log and gathered_data
    # when the LLM has no more tool calls (i.e., it's done).
    if not getattr(response, "tool_calls", None):
        research_output = response.content.strip()
        logger.info("Research complete — writing to gathered_data")
        update["gathered_data"] = [research_output]
        update["messages"]      = [{"role": "assistant", "content": research_output}]

    return update
