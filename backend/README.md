# 🔬 Research Agent — Human-in-the-Loop Research Assistant

An AI-powered research agent built with **LangGraph** that interprets ambiguous user queries, validates its understanding through a human-in-the-loop confirmation step, and generates structured research reports — all orchestrated as a formal state machine.

---

## 🎯 Goal

Users rarely express research needs with full precision. A direct "query → output" pipeline produces results that may miss the user's actual intent. This project solves that by inserting an **Interpret → Validate → Research** loop:

1. The AI **analyzes** the user's vague input and fills in gaps with reasonable assumptions.
2. It **presents** a structured interpretation and pauses for user confirmation.
3. If the user corrects, the AI **loops back** and re-analyzes with the new context.
4. Once confirmed, it generates a **comprehensive research report**.

---

## 🏗️ Architecture

```
┌──────────────┐     ┌───────────────────┐     ┌──────────────────┐
│   ANALYZE    │────▶│  PRESENT & VALIDATE│────▶│  RESEARCH/OUTPUT │
│  (AI thinks) │     │  (User confirms)   │     │  (Final action)  │
└──────────────┘     └───────────────────┘     └──────────────────┘
       ▲                      │
       └──────────────────────┘
            (User corrects)
```

### State Machine Flow

```
START → analyze_node → present_node (interrupt ⏸) → classify_node
                                                        │
                                          ┌─────────────┼──────────────┐
                                          │ CONFIRMED   │ CORRECTED    │
                                          ▼             ▼              │
                                    research_node   analyze_node ◄─────┘
                                          │
                                         END
```

---

## 📂 Project Structure

```
backend/
├── app.py                          # Entry point (FastAPI — TODO)
├── main.py                         # Alt entry point
├── pyproject.toml                  # Dependencies (managed by uv)
├── requirements.txt
├── .env.example                    # Template for API keys
│
└── src/
    ├── __init__.py
    ├── config.py                   # Loads API keys from .env
    ├── constants.py                # Model names, temperatures, roles
    │
    └── Research_Agent/
        ├── __init__.py
        ├── main.py
        │
        ├── state/
        │   └── state.py            # State (TypedDict) + InterpretedContext (Pydantic)
        │
        ├── nodes/
        │   ├── analyze_node.py     # Phase 1: Structured interpretation via LLM
        │   ├── present_node.py     # Phase 2: interrupt() for human validation
        │   ├── classify_node.py    # Phase 3: LLM classifies user reply
        │   ├── research_node.py    # Phase 4: Final research report generation
        │   └── basic_chatbot_node.py  # Legacy echo node (unused)
        │
        ├── graph/
        │   └── graph_builder.py    # Wires nodes + edges, compiles with MemorySaver
        │
        ├── LLMS/
        │   ├── groqllm.py          # ChatGroq factory (primary)
        │   └── geminillm.py        # Gemini LLM factory (alternate)
        │
        ├── tools/
        │   └── search_tool.py      # TavilySearchResults (optional web enrichment)
        │
        └── testing/
            └── contextBuilder.py   # Standalone prototype script (reference only)
```

---

## 🧩 Core Components

### State (`state/state.py`)

| Field | Type | Purpose |
|---|---|---|
| `raw_input` | `str` | User's original query |
| `messages` | `List[dict]` | Chat history (append-only) |
| `interpreted_context` | `InterpretedContext` | Pydantic model — domain, goal, assumptions, confidence |
| `gathered_data` | `List[str]` | Research output chunks (append-only) |
| `is_confirmed` | `bool` | Set to `True` when user confirms interpretation |
| `iteration_count` | `int` | Number of analyze → validate loops completed |
| `user_corrections` | `List[str]` | Corrections fed back into re-analysis (append-only) |

### Nodes

| Node | File | What It Does |
|---|---|---|
| **analyze** | `analyze_node.py` | Uses `with_structured_output()` to parse user input into an `InterpretedContext` Pydantic model |
| **present** | `present_node.py` | Formats the interpretation as a summary and calls `interrupt()` to pause for user input |
| **classify** | `classify_node.py` | LLM classifies user reply as `CONFIRMED`, `CORRECTED`, or `REJECTED` |
| **research** | `research_node.py` | Generates a structured report; optionally enriched with Tavily search results |

### Graph (`graph/graph_builder.py`)

- Uses `StateGraph(State)` from LangGraph
- `MemorySaver` checkpoint enables `interrupt()` / `Command(resume=...)` across requests
- Conditional edge after `classify_node` drives the correction loop
- `compiled_graph` is a module-level singleton — built once, shared across all requests

---

## ⚙️ Tech Stack

| Category | Technology |
|---|---|
| Graph Orchestration | LangGraph ≥ 1.0.8 |
| LLM Provider | Groq Cloud (`llama-3.3-70b-versatile`) |
| Structured Output | Pydantic v2 + `with_structured_output()` |
| Web Search (optional) | Tavily via `langchain-community` |
| Checkpointing | LangGraph `MemorySaver` (in-memory) |
| Package Manager | `uv` |
| Python | ≥ 3.11 |

---

## 🚀 Getting Started

```bash
# 1. Clone and navigate
cd backend

# 2. Create .env from the template
cp .env.example .env
# Fill in: GROQ_API_KEY (required), TAVILY_API_KEY (optional)

# 3. Install dependencies
uv sync

# 4. Verify the graph compiles
uv run python -c "from src.Research_Agent.graph.graph_builder import compiled_graph; print('OK')"
```

---

## 🔮 Planned Features (Not Yet Implemented)

> The following features are part of the roadmap but **not present in the current codebase**.

| Feature | Description |
|---|---|
| **FastAPI + React Frontend** | REST API (`/chat/start`, `/chat/resume`) with a React chat UI replacing the prototype Streamlit demo |
| **Dynamic Agent Creation** | Ability to spin up specialized sub-agents on the fly based on the research domain detected during analysis |
| **Multi-Agent Collaboration** | Architect, Red Team, and Blue Team agents working together to produce validated research outputs |
| **Persistent Checkpointing** | Replace `MemorySaver` with `SqliteSaver` or `PostgresSaver` for session persistence across server restarts |
| **Iteration Cap** | Hard limit on the analyze → validate loop (3–5 iterations) to prevent infinite correction cycles |
| **Streaming Responses** | Server-Sent Events (SSE) for real-time token-by-token output in the frontend |
| **Authentication** | User login with per-user session management and chat history |

---

## 📄 License

This project is for academic / personal use.
