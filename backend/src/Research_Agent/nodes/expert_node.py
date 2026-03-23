from src.Research_Agent.state.state import State
from src.logging.logger import logger
from src.Research_Agent.LLMS.groqllm import get_llm
from langgraph.types import interrupt

EXPERT_PROMPT = """
=== YOUR EXPERT IDENTITY ===
{system_prompt}

You are {name}, a {role}. You have been assembled as part of an adversarial review panel
to stress-test the following research proposal. Your goal is NOT to be helpful or encouraging —
your goal is to find the ONE most critical flaw, gap, or risk that, if unaddressed, could cause
this proposal to fail completely.

=== RESEARCH PROPOSAL UNDER REVIEW ===
Domain:          {domain}
Research Goal:   {interpreted_goal}

=== WHAT HAS ALREADY BEEN CHALLENGED ===
{history}

=== YOUR ANALYSIS FRAMEWORK ===
Before generating your critique, mentally run through these lenses relevant to your role:

1. FEASIBILITY   — Is the core assumption technically or operationally achievable?
2. EVIDENCE      — What claims are made without proof, citation, or precedent?
3. RISK          — What is the single most likely failure mode from your expert perspective?
4. BLINDSPOT     — What has the researcher clearly NOT thought about that you know matters?
5. PRECEDENT     — Have similar approaches failed before? Why?

=== STRICT RULES ===
- Focus exclusively on your domain of expertise — do not stray into other experts' territory
- Do NOT raise concerns that have already been discussed in the exchange history above
- Do NOT validate or praise the proposal — you are here only to challenge
- Do NOT ask multiple questions — ask exactly ONE sharp, direct question
- Keep your full response under 200 words
- End your response with your question on a new line prefixed with "QUESTION:"

=== OUTPUT FORMAT ===
[Brief identification of the flaw or risk — 2-4 sentences max]

QUESTION: [Your single, direct, pointed question to the researcher]
"""


def expert_node(state: State) -> dict:
    logger.info("Expert Node Entered")

    current_speaker_idx = state.get("current_speaker_idx", 0)
    current_persona = state.get("personas", [])[current_speaker_idx]
    ctx = state.get("interpreted_context")

    current_domain = current_persona.domain
    current_prompt = current_persona.system_prompt
    current_role = current_persona.role
    current_name = current_persona.name
    history = state.get("expert_critique", [])

    history_str = "\n\n".join([
        f"[{e['persona']}]: {e['critique']}\nResearcher: {e['response']}"
        for e in history
    ]) or "No previous expert exchanges yet."

    llm    = get_llm(temperature=0.6)
    prompt = EXPERT_PROMPT.format(
        system_prompt    = current_prompt,
        name             = current_name,
        role             = current_role,
        domain           = current_domain,
        interpreted_goal = ctx.interpreted_goal,
        history          = history_str,
    )

    response      = llm.invoke(prompt)
    critique_text = response.content
    logger.info(f"Expert [{current_name}] critique generated — round {state.get('round_number', 1)}")

    # Pause graph — hand critique to the outside world, wait for user reply
    user_response = interrupt({
        "summary":     critique_text,
        "type":        "expert_critique",
        "expert_name": current_name,
        "expert_role": current_role,
    })

    new_entry = {
        "persona":  current_name,
        "role":     current_role,
        "critique": critique_text,
        "response": str(user_response),
        "round":    state.get("round_number", 1),
    }

    logger.info(f"Expert [{current_name}] exchange complete")

    return {
        "expert_critique": [new_entry],
        "messages": [
            {"role": "expert", "content": f"[{current_name} — {current_role}]: {critique_text}"},
            {"role": "user",   "content": str(user_response)},
        ],
    }
