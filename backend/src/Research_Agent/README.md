# Research Agent — Module Reference

This is the LangGraph agent module. It defines the state, nodes, graph, LLMs, and tools that power the research pipeline.

---

## Agent Flow

```
START
  │
  ▼
[analyze_node]
  - Groq LLM (temperature=0.3) uses with_structured_output() to parse raw_input
  - Returns: InterpretedContext (domain, interpreted_goal, assumptions, confidence)
  - Also increments iteration_count
  │
  ▼
[present_node]
  - Formats InterpretedContext into a human-readable summary string
  - Calls LangGraph interrupt() ← graph pauses here, API returns "waiting"
  - On resume: receives user_response, appends both messages to state.messages
  │
  ▼
[classify_node]
  - Reads the last user message from state.messages
  - Groq LLM (temperature=0.0) classifies it as CONFIRMED / CORRECTED / REJECTED
  - CONFIRMED  → sets is_confirmed=True  → route to research_node
  - CORRECTED  → appends correction to user_corrections → route back to analyze_node
  - REJECTED   → clears corrections + context → route back to analyze_node
  │
  ├── is_confirmed=True
  │      ▼
  │  [research_node]
  │   - Optional: runs TavilySearchResults to fetch real web data
  │   - Groq LLM (temperature=0.7) generates a structured markdown report
  │   - Appends report to state.gathered_data
  │      ▼
  │     END
  │
  └── is_confirmed=False → back to [analyze_node] (loop)
```

---

## State (`state/state.py`)

All nodes share a single `State` TypedDict that flows through the entire graph.

### `InterpretedContext` (Pydantic model)

Produced by `analyze_node` via Groq structured output.

| Field | Type | Description |
|---|---|---|
| `domain` | `str` | Subject area, e.g. "Agricultural Drone Technology" |
| `interpreted_goal` | `str` | One-sentence description of what the user wants |
| `assumptions` | `list[str]` | Gaps filled in by the LLM |
| `confidence` | `"high" \| "medium" \| "low"` | LLM's confidence in its interpretation |

### `State` fields

| Field | Type | Notes |
|---|---|---|
| `raw_input` | `str` | Original unprocessed user query |
| `messages` | `List[dict]` | `{"role": "user"/"assistant", "content": str}` — **append-only** |
| `interpreted_context` | `Optional[InterpretedContext]` | None until analyze_node runs; cleared on REJECTED |
| `gathered_data` | `List[str]` | Research output chunks — **append-only** |
| `is_confirmed` | `bool` | Routes classify_node output to research or loop |
| `iteration_count` | `int` | How many analyze→present→classify loops have run |
| `user_corrections` | `List[str]` | Corrections from user, fed into next analyze pass — **append-only** |

Fields marked **append-only** use `Annotated[List, operator.add]` — LangGraph merges node updates by concatenation.

---

## Nodes (`nodes/`)

### `analyze_node.py`

```
Input state fields:  raw_input, user_corrections
Output state fields: interpreted_context, iteration_count
LLM: Groq, temperature=0.3, with_structured_output(InterpretedContext)
```

Builds a prompt with the raw input and any previous corrections, then calls the LLM with structured output to directly get an `InterpretedContext` Pydantic instance — no manual JSON parsing needed.

---

### `present_node.py`

```
Input state fields:  interpreted_context
Output state fields: messages (appends assistant summary + user reply)
No LLM call — pure formatting + interrupt()
```

Builds a markdown-formatted summary and calls `interrupt({"summary": ..., "type": "confirmation"})`. This pauses the graph. The interrupt payload is what the FastAPI layer surfaces as the `message` field in the API response.

When resumed, the user's reply is returned by `interrupt()` as `user_response`.

---

### `classify_node.py`

```
Input state fields:  messages (reads last user message)
Output state fields: is_confirmed, user_corrections (if CORRECTED), interpreted_context (reset if REJECTED)
LLM: Groq, temperature=0.0
```

Sends the user's response to the LLM with a strict prompt: reply with only `CONFIRMED`, `CORRECTED`, or `REJECTED`.

- **CONFIRMED** → `is_confirmed=True` → graph routes to `research_node`
- **CORRECTED** → appends the user reply to `user_corrections`, `is_confirmed=False` → routes back to `analyze_node`
- **REJECTED** → clears `user_corrections` and `interpreted_context`, `is_confirmed=False` → routes back to `analyze_node` for a fresh start

---

### `research_node.py`

```
Input state fields:  interpreted_context
Output state fields: gathered_data (appends final report)
LLM: Groq, temperature=0.7
Optional: Tavily web search to ground the report in real data
```

Attempts to run a Tavily search first (fails silently if no API key or network issue). Injects search results into the prompt if available. Generates a structured markdown report with: Executive Overview, Key Facts, Sub-Topics, Practical Applications, Recommended Next Steps.

---

## LLMs (`LLMS/`)

### `groqllm.py` — Primary

```python
def get_llm(temperature=0.0) -> ChatGroq
```

Returns a `ChatGroq` instance using `GROQ_LLM_MODEL_NAME` from `constants.py` (`llama-3.3-70b-versatile`). Raises immediately if `GROQ_API_KEY` is missing.

### `geminillm.py` — Available but not in active flow

Gemini LLM factory. Can be swapped in if Groq rate limits are hit.

---

## Tools (`tools/`)

### `search_tool.py`

```python
def search_tool() -> list       # returns [TavilySearchResults(max_results=2)]
def create_tool_node(tools)     # wraps tools in a LangGraph ToolNode
```

Used optionally in `research_node` to fetch real web content before generating the report. Requires `TAVILY_API_KEY` in `.env`.

---

## Graph (`graph/graph_builder.py`)

```python
workflow = StateGraph(State)

workflow.add_node("analyze",  analyze_node)
workflow.add_node("present",  present_node)
workflow.add_node("classify", classify_node)
workflow.add_node("research", research_node)

workflow.add_edge(START,     "analyze")
workflow.add_edge("analyze", "present")
workflow.add_edge("present", "classify")

workflow.add_conditional_edges(
    "classify",
    route_after_classify,   # returns "research" if is_confirmed else "analyze"
    {"research": "research", "analyze": "analyze"}
)

workflow.add_edge("research", END)

compiled = workflow.compile(checkpointer=MemorySaver())
```

The `MemorySaver` stores the full state snapshot after every node, keyed by `thread_id`. This is what makes `interrupt()` / `Command(resume=...)` work across separate HTTP requests.

> **Production note:** `MemorySaver` is in-process RAM. Replace with `AsyncPostgresSaver` or `SqliteSaver` if you need persistence across restarts or multiple server processes.
