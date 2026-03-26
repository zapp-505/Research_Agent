import json
from src.Research_Agent.state.state import State, Persona, PanelOutput
from src.logging.logger import logger
from src.Research_Agent.LLMS.groqllm import get_llm


PANEL_GENERATOR_PROMPT = """
You are a "panel director" for an adversarial research review board.
Given a research topic, generate exactly 3 expert personas who will challenge the idea from different angles.

Domain: {domain}
Goal: {interpreted_goal}

Rules:
- Generate EXACTLY 3 experts.
- EXPERT 1 must ALWAYS be a Senior Software Engineer / Technical Architect. They challenge the
  technical implementation: architecture choices, scalability, data pipelines, API design, model
  serving, coding complexity, tech stack suitability, and build-vs-buy tradeoffs. Their name and
  role should be specific to the domain (e.g. "ML Systems Engineer" for an AI project, "Backend
  Architect" for a SaaS product).
- EXPERT 2 and EXPERT 3 must each cover a DIFFERENT non-technical dimension relevant to the domain
  (e.g. market viability, regulatory/legal risk, UX/product, ethics, finance, operations — never
  two of the same).
- All three experts should be domain-specific, not generic (e.g. "FDA Compliance Officer" not
  "Legal Expert").
- Each system_prompt must describe how the expert thinks, what they prioritize, and what they are
  skeptical of.
- All experts are adversarial — they look for fatal flaws, gaps, and weaknesses only.
"""


def _first_sentence(text: str) -> str:
    """Extract the first complete sentence from a text block."""
    for sep in (".", "!", "?"):
        idx = text.find(sep)
        if 15 < idx < 250:
            return text[:idx + 1].strip()
    return text[:150].rstrip() + "..."


def panel_generator_node(state: State) -> dict:
    """Phase 3: Generate the adversarial expert panel."""
    logger.info("Panel Generator Node Entered")

    llm = get_llm(temperature=0.7)
    structured_llm = llm.with_structured_output(PanelOutput)

    ctx = state.get("interpreted_context")
    if ctx is None:
        raise ValueError("panel_generator_node called but interpreted_context is None")

    prompt = PANEL_GENERATOR_PROMPT.format(
        domain=ctx.domain,
        interpreted_goal=ctx.interpreted_goal,
    )

    panel_output: PanelOutput = structured_llm.invoke(prompt)
    logger.info(f"Panel generated: {[p.name for p in panel_output.personas]}")

    # Build a 'panel_intro' message so the expert lineup appears in chat history
    # (both live and when old sessions are reloaded from LangGraph state).
    panel_intro_data = json.dumps([
        {
            "name":    p.name,
            "role":    p.role,
            "domain":  p.domain,
            "summary": _first_sentence(p.system_prompt),
        }
        for p in panel_output.personas
    ])

    return {
        "personas":            panel_output.personas,
        "current_speaker_idx": 0,
        "round_number":        1,
        "messages": [
            {"role": "panel_intro", "content": panel_intro_data}
        ],
    }