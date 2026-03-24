from src.Research_Agent.state.state import State
from src.logging.logger import logger

MAX_ROUNDS = 2

def moderator_node(state: State) -> dict:
    """
    Phase 4: Moderator AI presents the research to the user.
    """
    logger.info("Moderator Node Entered")

    #Default Value. If the key "personas" does not exist in the dictionary, Python will return this empty list instead of crashing.
    personas = state.get("personas",[])
    critiques = state.get("expert_critique", [])   # NOTE: no trailing 's'

    total_experts = len(personas)

    if total_experts == 0:
        return {"is_gauntlet_complete": True}

    completed_rounds = len(critiques) // total_experts   # full rounds done
    next_idx         = len(critiques) % total_experts    # who speaks next

    if completed_rounds >= MAX_ROUNDS:
        return {
            "is_gauntlet_complete": True,
            "current_speaker_idx":  next_idx,
            "round_number":         completed_rounds,
        }

    return {
        "is_gauntlet_complete": False,
        "current_speaker_idx":  next_idx,
        "round_number":         completed_rounds + 1,
    }
    