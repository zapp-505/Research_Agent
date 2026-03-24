"""
test_gauntlet.py
End-to-end CLI test harness for the full Gauntlet workflow.

Run with:
    uv run python -m src.Research_Agent.testing.test_gauntlet

This exercises the complete graph:
  analyze → present (confirmation) → classify → panel_generator
  → moderator → expert (adversarial critique) × N rounds
  → blue_team (final report)

Each interrupt() pause is handled here: the payload is displayed,
the user types a response, and execution resumes with Command(resume=...).
"""

import asyncio
import uuid
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver

from src.logging.logger import logger
from src.Research_Agent.graph.graph_builder import GraphBuilder


# ── Display helpers ────────────────────────────────────────────────────────────

def _divider(char: str = "─", width: int = 60) -> str:
    return char * width

def _print_interrupt(interrupt_val: dict) -> None:
    """Format and print an interrupt payload based on its type."""
    itype = interrupt_val.get("type", "unknown")

    if itype == "confirmation":
        print(f"\n{'═' * 60}")
        print("🤖  AGENT — Interpretation")
        print(_divider())
        print(interrupt_val.get("summary", ""))
        print(_divider())
        print("Does this match your intent? Confirm or correct it.")

    elif itype == "expert_critique":
        name = interrupt_val.get("expert_name", "Expert")
        role = interrupt_val.get("expert_role", "")
        print(f"\n{'═' * 60}")
        print(f"⚔️   [{name}]  —  {role}")
        print(_divider())
        print(interrupt_val.get("summary", ""))
        print(_divider())
        print("Respond to the expert's critique / question above.")

    else:
        # Fallback for unknown interrupt types
        print(f"\n{'═' * 60}")
        print(f"⏸   AGENT PAUSED  (type: {itype})")
        print(_divider())
        print(str(interrupt_val))
        print(_divider())


def _get_interrupt(graph, config: dict) -> dict | None:
    """Read the current interrupt payload from graph state, or None if graph is done."""
    state = graph.get_state(config)
    if not state.next:
        return None
    try:
        return state.tasks[0].interrupts[0].value
    except (IndexError, AttributeError):
        return None


# ── Main test loop ─────────────────────────────────────────────────────────────

async def main():
    print("\n" + "═" * 60)
    print("  🔬  Research Agent — Gauntlet CLI Test Harness")
    print("═" * 60)

    # Build graph with MemorySaver — no Atlas needed for CLI testing.
    # Production (app.py) will use MongoDBSaver for persistence.
    builder = GraphBuilder(checkpointer=MemorySaver())
    graph   = builder.build()
    logger.info("Graph compiled successfully")

    # 2. Generate a unique thread_id for this session
    thread_id = str(uuid.uuid4())
    config    = {"configurable": {"thread_id": thread_id}}
    print(f"\n  Session ID: {thread_id}\n")

    # 3. Get the user's initial research query
    raw_input = input("📝  What do you want to research?\n> ").strip()
    if not raw_input:
        raw_input = "The feasibility of using autonomous solar-powered drones for reforestation"
        print(f"  (Using default: {raw_input})")

    # 4. Build the initial state — all required fields must be present
    initial_state = {
        "raw_input":           raw_input,
        "messages":            [{"role": "user", "content": raw_input}],
        "interpreted_context": None,
        "is_confirmed":        False,
        "iteration_count":     0,
        "user_corrections":    [],
        "personas":            None,
        "current_speaker_idx": 0,
        "round_number":        0,
        "expert_critique":     [],
        "is_gauntlet_complete": False,
        "final_report":        None,
        "synthesis_thread":    [],
    }

    # 5. Run the graph — stream until first interrupt
    print(f"\n{_divider('─')}")
    print("  Starting Gauntlet workflow...")
    print(_divider("─"))

    async for _ in graph.astream(initial_state, config):
        pass   # stream until graph pauses or finishes

    # 6. Main interaction loop
    while True:
        interrupt_val = _get_interrupt(graph, config)

        if interrupt_val is None:
            # No interrupt — graph has finished
            break

        # Display the interrupt to the user
        _print_interrupt(interrupt_val)

        # Get user's response
        user_reply = input("\n> ").strip()
        while not user_reply:
            print("  ⚠️  Please type a response.")
            user_reply = input("> ").strip()

        # Resume the graph with the user's reply
        print(f"\n{_divider('─')}")
        async for _ in graph.astream(Command(resume=user_reply), config):
            pass

    # 7. Read and display the final report
    final_state = graph.get_state(config).values
    report      = final_state.get("final_report")

    print(f"\n{'═' * 60}")
    if report:
        print("📋  FINAL GAUNTLET REPORT")
        print("═" * 60)
        print(report)
    else:
        # Fallback — show last AI message if final_report wasn't set
        msgs    = final_state.get("messages", [])
        ai_msgs = [m for m in msgs if m.get("role") in ("assistant", "report", "ai")]
        if ai_msgs:
            print("📋  OUTPUT")
            print("═" * 60)
            print(ai_msgs[-1]["content"])
        else:
            print("⚠️  No final report found in state.")

    print(f"\n{'═' * 60}")
    print("  ✅  Session complete.")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
