# Adversarial Human-in-the-Loop Strategy

## What We're Building

After the agent generates a research report, instead of immediately returning it to the user, we insert an **adversarial review loop**:

1. A **Red Team agent** automatically attacks the report (biases, gaps, flawed logic)
2. The **user sees both the report and the critique** and decides what to do
3. Optionally, a **Blue Team agent** rebuts the critique
4. The user can also choose to **regenerate the report** with the critique as context

This is human-in-the-loop not just for input confirmation (which we already have), but for **quality control of the output**.

---

## Extended Graph Flow

```
START
  │
  ▼
[analyze_node]        ← interprets raw query → InterpretedContext
  │
  ▼
[present_node]        ← interrupt #1: "Is this what you meant?"
  │
  ▼
[classify_node]       ← CONFIRMED / CORRECTED / REJECTED
  │                      CORRECTED/REJECTED → loop back to analyze
  │ CONFIRMED
  ▼
[research_node]       ← generates full report (+ optional Tavily search)
  │
  ▼                   ━━━━━ NEW BELOW THIS LINE ━━━━━
[red_team_node]       ← adversarial AI attacks the report automatically
  │
  ▼
[present_review_node] ← interrupt #2: user sees report + critique side-by-side
  │                      user replies: "accept" / "defend" / "revise"
  ▼
[review_classify_node]← classifies the user's reply
  │
  ├── ACCEPTED  ──────────────────────────────────► END
  │
  ├── REVISE    ──────────────────────────────────► [research_node]  (loop)
  │
  └── DEFEND
        │
        ▼
      [blue_team_node]      ← defensive AI rebuts the critique point-by-point
        │
        ▼
      [present_defense_node]← interrupt #3: user sees full Red vs Blue debate
        │
        ▼
       END
```

---

## State Changes (`state/state.py`)

Add three optional fields to the existing `State` TypedDict:

```python
# Adversarial review fields
red_team_critique:  Optional[str]   # populated by red_team_node
blue_team_defense:  Optional[str]   # populated by blue_team_node (if DEFEND chosen)
review_decision:    Optional[str]   # "ACCEPTED" | "DEFEND" | "REVISE"
```

These are plain `Optional[str]` — not append-only — because each is overwritten once per review cycle, not accumulated.

---

## New Nodes

### 1. `red_team_node.py`

**Role:** Automated adversarial agent. Runs without any user interaction.

**Input state:** `gathered_data[-1]` (the research report)  
**Output state:** `red_team_critique: str`, appends to `messages`

**LLM:** Groq, `temperature=0.6` (creative enough to find non-obvious flaws)

**Prompt instructs the LLM to attack across 5 dimensions:**
- Factual gaps — missing evidence, unverified claims
- Biases & assumptions — unjustified gaps filled by the LLM
- Logical flaws — contradictions, non-sequiturs
- Missing perspectives — counter-arguments, stakeholders ignored
- Practical weaknesses — where "applications" fall apart in reality
- Verdict: WEAK / MODERATE / STRONG reliability rating

---

### 2. `present_review_node.py`

**Role:** Pauses the graph and presents the report + critique to the user.

**Input state:** `gathered_data[-1]`, `red_team_critique`  
**Output state:** appends to `messages`

**Uses LangGraph `interrupt()`** with payload:
```python
{
  "summary": "<formatted report + critique>",
  "type": "adversarial_review"
}
```

**API response the client sees:**
```json
{
  "status": "waiting",
  "message": "━━━ REPORT ━━━\n...\n━━━ RED TEAM CRITIQUE ━━━\n...\nReply: accept / defend / revise",
  "thread_id": "uuid"
}
```

---

### 3. `review_classify_node.py`

**Role:** Classifies the user's decision using the LLM.

**Input state:** last user message in `messages`  
**Output state:** `review_decision: "ACCEPTED" | "DEFEND" | "REVISE"`

**LLM:** Groq, `temperature=0.0` (deterministic)

**Prompt:**
```
The user was shown a research report and a Red Team critique.
They replied: "{user_response}"
Classify as: ACCEPTED, DEFEND, or REVISE. Reply with only the word.
```

**Routing logic in graph_builder:**
```python
def route_after_review(state):
    decision = state.get("review_decision", "ACCEPTED")
    if decision == "DEFEND":   return "blue_team"
    if decision == "REVISE":   return "research"
    return "__end__"
```

---

### 4. `blue_team_node.py`

**Role:** Defensive AI agent. Runs only when user chooses "defend".

**Input state:** `gathered_data[-1]`, `red_team_critique`  
**Output state:** `blue_team_defense: str`, appends debate_summary to `gathered_data`

**LLM:** Groq, `temperature=0.4`

**Prompt instructs the LLM to:**
- Quote each Red Team critique point and counter it
- Honestly acknowledge valid criticisms (builds credibility)
- Highlight what the Red Team missed
- Provide its own WEAK / MODERATE / STRONG verdict
- Give a final recommendation: accept / revise / more research needed

The full debate (Red + Blue) is appended to `gathered_data` as the final deliverable.

---

### 5. `present_defense_node.py`

**Role:** Shows the full adversarial debate and does a final interrupt before END.

**Input state:** `gathered_data[-1]` (the debate summary)  
**Output state:** appends to `messages`

**Uses `interrupt()`** with `"type": "defense_review"`.  
Whatever the user replies is logged to `messages` but no routing happens — graph always proceeds to `END` after this.

---

## Graph Builder Changes (`graph/graph_builder.py`)

### New imports
```python
from src.Research_Agent.nodes.red_team_node        import red_team_node
from src.Research_Agent.nodes.present_review_node  import present_review_node
from src.Research_Agent.nodes.review_classify_node import review_classify_node
from src.Research_Agent.nodes.blue_team_node       import blue_team_node
from src.Research_Agent.nodes.present_defense_node import present_defense_node
```

### New nodes
```python
workflow.add_node("red_team",        red_team_node)
workflow.add_node("present_review",  present_review_node)
workflow.add_node("review_classify", review_classify_node)
workflow.add_node("blue_team",       blue_team_node)
workflow.add_node("present_defense", present_defense_node)
```

### Replace the old `research → END` edge
```python
# OLD:
workflow.add_edge("research", END)

# NEW:
workflow.add_edge("research",       "red_team")
workflow.add_edge("red_team",       "present_review")
workflow.add_edge("present_review", "review_classify")

workflow.add_conditional_edges(
    "review_classify",
    route_after_review,
    {
        "blue_team": "blue_team",
        "research":  "research",   # REVISE loops back
        "__end__":   END,
    },
)

workflow.add_edge("blue_team",       "present_defense")
workflow.add_edge("present_defense", END)
```

---

## API Impact

The existing `/chat/start` and `/chat/resume` endpoints need **no changes** — the new interrupts surface through the same `status: "waiting"` response pattern. The `"type"` field in the interrupt payload lets the client differentiate which stage the conversation is at:

| `type` value | Interrupt stage | Expected user input |
|---|---|---|
| `"confirmation"` | After analyze — confirm intent | yes / correction / reject |
| `"adversarial_review"` | After red_team — review critique | accept / defend / revise |
| `"defense_review"` | After blue_team — acknowledge debate | anything (just to close) |

---

## REVISE Loop Behaviour

When the user chooses "revise", the graph routes back to `research_node`. The Red Team critique is now stored in `state.red_team_critique`. To make the regeneration actually address the critique, update `research_node` to inject it into the prompt:

```python
critique = state.get("red_team_critique")
if critique:
    prompt += f"\n\nIMPORTANT: A previous version of this report was critiqued as follows:\n{critique}\nAddress these weaknesses in your new report."
```

This closes the loop: the adversarial agent's output directly improves the next iteration.

---

## Files to Create / Modify

| Action | File |
|---|---|
| **Modify** | `state/state.py` — add 3 fields |
| **Modify** | `graph/graph_builder.py` — new nodes, edges, routing function |
| **Create** | `nodes/red_team_node.py` |
| **Create** | `nodes/present_review_node.py` |
| **Create** | `nodes/review_classify_node.py` |
| **Create** | `nodes/blue_team_node.py` |
| **Create** | `nodes/present_defense_node.py` |

No changes needed to `app.py`, `auth.py`, or any existing nodes.
