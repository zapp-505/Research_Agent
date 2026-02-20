"""
research_node.py
Phase 4 – Final Output: Generate a comprehensive research/requirements summary
based on the confirmed interpreted_context.
"""

from src.Research_Agent.state.state import State
from src.Research_Agent.LLMS.groqllm import get_llm


RESEARCH_PROMPT = """You are a world-class research assistant. Based on the confirmed requirements below, generate a comprehensive research summary.

CONFIRMED REQUIREMENTS:
- Domain: {domain}
- Goal: {interpreted_goal}
- Assumptions: {assumptions}

Please produce a structured research summary with:
1. **Executive Overview** – A clear, concise description of the topic.
2. **Key Facts & Insights** – The most important, accurate, up-to-date information.
3. **Sub-Topics Explored** – Break down the domain into relevant sub-areas.
4. **Practical Applications** – Real-world use cases and examples.
5. **Recommended Next Steps** – What the user should explore or do next.

Make this thorough, informative, and actionable. Use markdown formatting."""


def research_node(state: State) -> dict:
    """
    Phase 4 – Generate the final research output using the confirmed context.
    Optionally uses the Tavily search tool to ground claims in real data.
    """
    llm = get_llm(temperature=0.7)
    ctx = state.get("interpreted_context")

    if ctx is None:
        return {"gathered_data": ["Error: No confirmed context found."]}

    assumptions_str = ", ".join(ctx.assumptions) if ctx.assumptions else "None"

    # Optional: use Tavily to fetch real search results first
    search_results = []
    try:
        from src.Research_Agent.tools.search_tool import search_tool
        tools = search_tool()
        tavily = tools[0]  # TavilySearchResults
        results = tavily.invoke(ctx.interpreted_goal)
        if isinstance(results, list):
            for r in results:
                if isinstance(r, dict) and "content" in r:
                    search_results.append(r["content"])
    except Exception:
        # If Tavily fails (no key, network, missing extras), continue without it
        pass

    # Build the prompt — inject real search data if we have it
    prompt = RESEARCH_PROMPT.format(
        domain=ctx.domain,
        interpreted_goal=ctx.interpreted_goal,
        assumptions=assumptions_str,
    )

    if search_results:
        prompt += f"\n\nAdditional real-time context from the web:\n" + "\n---\n".join(search_results[:2])

    response = llm.invoke(prompt)
    research_output = response.content.strip()

    return {
        "gathered_data": [research_output],
        "messages": [{"role": "assistant", "content": research_output}],
    }
