from src.Research_Agent.state.state import State, Persona, PanelOutput  
from src.logging.logger import logger                                     
from src.Research_Agent.LLMS.groqllm import get_llm



PANEL_GENERATOR_PROMPT = """
You are a "panel director" for an adversarial research review board.
Given a research topic, generate exactly 3 expert personas who will challenge the idea from different angles.

Domain: {domain}
Goal: {interpreted_goal}

Rules:
- Each expert must attack from a DIFFERENT dimension (e.g. technical, legal, market — never two of the same)
- Experts should be domain-specific, not generic (e.g. "FAA Regulatory Officer" not "Legal Expert")
- Each system_prompt must describe how the expert thinks, what they prioritize, and what they are skeptical of
- Experts are adversarial — they look for fatal flaws, gaps, and weaknesses

"""


def panel_generator_node(state: State) -> dict:
    """
    Phase 3: Generate the panel of experts.
    """
    
    logger.info("Panel Generator Node Entered")

    llm = get_llm(temperature=0.7)
    structured_llm = llm.with_structured_output(PanelOutput)

    ctx = state.get("interpreted_context")
    if ctx is None:
        raise ValueError("panel_generator_node called but interpreted_context is None")

    prompt = PANEL_GENERATOR_PROMPT.format(
        domain=ctx.domain,
        interpreted_goal=ctx.interpreted_goal
    )

    panel_output: PanelOutput = structured_llm.invoke(prompt)

    return {
        "personas": panel_output.personas,
        "current_speaker_idx": 0,
        "round_number": 1
    }