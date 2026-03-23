"""
blueteam_node.py
Terminal synthesis node — produces the final structured research report.

Uses LangGraph's ToolNode pattern via state["synthesis_thread"]:
  - First entry: builds the synthesis prompt and invokes LLM.
  - Re-entry (after ToolNode): passes full thread back to LLM to continue.
  - Only writes final_report and messages when LLM produces plain text (no tool_calls).

A separate ToolNode(tools, messages_key="synthesis_thread") in graph_builder
handles tool execution and routes back here.
"""

from langchain_core.messages import HumanMessage

from src.Research_Agent.state.state import State
from src.Research_Agent.LLMS.groqllm import get_llm
from src.logging.logger import logger


BLUE_TEAM_PROMPT = """
You are the Blue Team Synthesis Lead — a senior consultant tasked with producing the
final research assessment after an adversarial expert panel review.

You have access to a web search tool. Use it only when you need to verify a specific
claim or find current supporting evidence that would materially improve the report.
Do not search for general background — focus on precision.

=== ORIGINAL RESEARCH PROPOSAL ===
Domain:  {domain}
Goal:    {interpreted_goal}

=== ADVERSARIAL PANEL DEBATE TRANSCRIPT ===
{debate_transcript}

=== YOUR TASK ===
Produce a structured final report with the following sections:

**EXECUTIVE SUMMARY**
A 2-3 sentence overview of the proposal's viability based on the panel debate.

**CONCERNS RAISED BY THE PANEL**
For each expert, summarize the key concern they raised and how the researcher addressed it.
Rate how well each concern was resolved: [RESOLVED / PARTIALLY RESOLVED / UNRESOLVED]

**CRITICAL UNRESOLVED RISKS**
Any concerns from the panel that remain inadequately addressed.
These are the proposal's current fatal weaknesses.

**STRENGTHS IDENTIFIED**
What aspects of the proposal survived adversarial scrutiny successfully.

**RECOMMENDATIONS**
Concrete next steps the researcher should take before proceeding.

**VIABILITY VERDICT**
Rate overall viability: STRONG / MODERATE / WEAK / INSUFFICIENT EVIDENCE
One sentence justifying the verdict.
"""


def _format_debate(expert_critiques: list) -> str:
    """Convert expert_critique list into a readable debate transcript."""
    lines = []
    for entry in expert_critiques:
        lines.append(
            f"--- Round {entry['round']} | {entry['persona']} ({entry['role']}) ---\n"
            f"CRITIQUE:    {entry['critique']}\n"
            f"RESEARCHER:  {entry['response']}"
        )
    return "\n\n".join(lines) or "No expert exchanges recorded."


def blue_team_node(state: State) -> dict:
    """
    Runs every time the graph enters this node — fresh or after ToolNode.

    First entry:  synthesis_thread is empty → build prompt and start conversation.
    Re-entry:     synthesis_thread has tool results → pass full thread to LLM.
    """
    logger.info("Blue Team Node Entered")

    ctx       = state.get("interpreted_context")
    critiques = state.get("expert_critique", [])
    thread    = state.get("synthesis_thread", [])

    llm = get_llm(temperature=0.4)

    # Bind Tavily if available
    try:
        from src.Research_Agent.tools.search_tool import search_tool
        tools          = search_tool()
        llm_with_tools = llm.bind_tools(tools)
        logger.info("Tavily bound to synthesis LLM")
    except Exception:
        llm_with_tools = llm
        logger.info("Tavily unavailable — synthesis proceeds without web search")

    if not thread:
        # ── First entry: build the synthesis prompt ────────────────────────
        debate_transcript = _format_debate(critiques)
        prompt = BLUE_TEAM_PROMPT.format(
            domain            = ctx.domain,
            interpreted_goal  = ctx.interpreted_goal,
            debate_transcript = debate_transcript,
        )
        thread = [HumanMessage(content=prompt)]

    # Invoke LLM with the full thread (includes any ToolMessages on re-entry)
    response = llm_with_tools.invoke(thread)
    logger.info(f"Synthesis LLM responded — tool_calls: {bool(getattr(response, 'tool_calls', None))}")

    update = {"synthesis_thread": [*thread, response] if not state.get("synthesis_thread") else [response]}

    # Only write the final report when LLM is done (no tool_calls)
    if not getattr(response, "tool_calls", None):
        final_report = response.content
        logger.info("Blue Team synthesis complete — writing final report")
        update["final_report"] = final_report
        update["messages"]     = [{"role": "report", "content": final_report}]

    return update
