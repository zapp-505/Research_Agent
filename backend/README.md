# Backend

FastAPI server that exposes the LangGraph research agent over HTTP, secured with JWT authentication.

---

## Directory Structure

```
backend/
├── app.py                          # FastAPI app bootstrap (CORS, startup, router registration)
├── main.py                         # Entrypoint stub
├── requirements.txt                # Python dependencies
├── pyproject.toml
└── src/
    ├── routers/
    │   ├── index.py                # Public health/info endpoint(s)
    │   ├── auth.py                 # JWT verification endpoint(s)
    │   ├── chat.py                 # /chat/start and /chat/resume + interrupt/resume helper
    │   └── history.py              # Chat history/summary/delete endpoints
    ├── config.py                   # Loads env vars (API keys, DB URI)
    ├── constants.py                # LLM model names, temperature constants
    ├── auth.py                     # JWT helpers + get_current_user dependency
    └── Research_Agent/
        ├── state/state.py          # Shared graph state (TypedDict + Pydantic models)
        ├── graph/graph_builder.py  # Wires nodes into the LangGraph StateGraph
        ├── nodes/
        │   ├── analyze_node.py     # Phase 1: interpret user query → InterpretedContext
        │   ├── present_node.py     # Phase 2: format summary + interrupt() for confirmation
        │   ├── classify_node.py    # Phase 3: classify user reply (CONFIRMED/CORRECTED/REJECTED)
        │   └── research_node.py    # Phase 4: generate full research report
        ├── LLMS/
        │   ├── groqllm.py          # Groq ChatGroq factory (get_llm) — primary LLM
        │   └── geminillm.py        # Gemini LLM factory (available, not in active flow)
        └── tools/
            └── search_tool.py      # Tavily web search tool wrapper
```

---

## Setup

### 1. Create and activate a virtual environment

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in `backend/`:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
GEMINI_API_KEY=your_gemini_api_key          # optional, not in active flow
JWT_SECRET_KEY=your_long_random_secret
```

Use a strong random value for `JWT_SECRET_KEY` in all environments.

### 4. Run the server

```powershell
uvicorn app:app --reload
```

Server runs on `http://localhost:8000`.

---

## API Endpoints

| Method | Path           | Auth | Description                                      |
|--------|----------------|------|--------------------------------------------------|
| GET    | `/index`       | No   | Health check                                     |
| GET    | `/auth/verify` | Yes  | Verifies JWT token, returns uid/email/name  |
| POST   | `/chat/start`  | Yes  | Starts a new research conversation               |
| POST   | `/chat/resume` | Yes  | Resumes a paused conversation                    |
| GET    | `/chat/{thread_id}/history` | Yes | Returns full message history for one thread |
| GET    | `/chat/{thread_id}/summary` | Yes | Returns compact summary for one thread |
| DELETE | `/chat/{thread_id}/history` | Yes | Deletes all persisted messages for one thread |

All protected endpoints require `Authorization: Bearer <JWT token>`.

## Router Registration Pattern

FastAPI equivalent of Flask `register_blueprint()` is used in `app.py`:

```python
app.include_router(index_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(history_router)
```

This keeps route handlers in focused modules and leaves `app.py` as the application bootstrap file.

### POST /chat/start

```json
Request:  { "query": "Tell me about agricultural drone technology" }

Response (paused, waiting for confirmation):
{ "status": "waiting", "message": "Here's what I understood...", "thread_id": "uuid" }

Response (if graph completes without interrupt):
{ "status": "complete", "message": "<research report>", "thread_id": "uuid" }
```

### POST /chat/resume

```json
Request:  { "thread_id": "uuid", "user_response": "yes" }

Response: { "status": "complete", "message": "<research report>", "thread_id": "uuid" }
      or: { "status": "waiting", "message": "...", "thread_id": "uuid" }  (another loop)
```

---

## Authentication (`src/auth.py`)

The backend uses native JWT authentication.

**Flow:**
1. Client obtains a JWT signed with `JWT_SECRET_KEY`
2. Client sends the token on every request: `Authorization: Bearer <token>`
3. `get_current_user` decodes and validates the token server-side
4. The route receives claims like `{ "uid": "...", "email": "..." }`

---

## Key Files Explained

### `src/config.py`
Loads all secrets from `.env` via `python-dotenv`. Always import constants from here — never call `os.environ` directly in node files.

### `src/constants.py`
Centralised values:
- `GROQ_LLM_MODEL_NAME = "llama-3.3-70b-versatile"`
- `TEMPERATURE_CREATIVE = 0.7` — used by research_node for creative output
- `TEMPERATURE_STRICT = 0.0` — used by classify_node for deterministic classification

### `src/Research_Agent/state/state.py`

```python
class InterpretedContext(BaseModel):
    domain: str               # e.g. "Agricultural Drone Technology"
    interpreted_goal: str     # one-sentence description of user's goal
    assumptions: list[str]    # gaps filled in by the LLM
    confidence: Literal["high", "medium", "low"]

class State(TypedDict):
    raw_input:           str
    messages:            Annotated[List[dict], operator.add]        # append-only
    interpreted_context: Optional[InterpretedContext]
    gathered_data:       Annotated[List[str], operator.add]         # append-only
    is_confirmed:        bool
    iteration_count:     int
    user_corrections:    Annotated[List[str], operator.add]         # append-only
```

`Annotated[..., operator.add]` means LangGraph **appends** node updates to the list instead of replacing it.

### `src/Research_Agent/graph/graph_builder.py`
- Builds a `StateGraph` with a `MemorySaver` checkpoint store
- **`MemorySaver` is in-process RAM** — state is lost on server restart; swap for `AsyncPostgresSaver` for production
- The compiled graph is a **module-level singleton** — created once at startup, shared across all requests
- Each conversation is isolated by a UUID `thread_id` generated in `/chat/start`

---

## LangGraph Interrupt / Resume Pattern

This is the core mechanism that lets the agent pause mid-execution across two separate HTTP requests:

```
/chat/start invoked
    │
    ├── agent.invoke(initial_state, config)
    │       │
    │       └── present_node calls interrupt({"summary": "..."})
    │               LangGraph saves state to MemorySaver, stops execution
    │
    └── _run_and_respond() sees state.next is not empty
        returns: { "status": "waiting", "message": summary, "thread_id": ... }

/chat/resume invoked (same thread_id)
    │
    ├── agent.invoke(Command(resume=user_response), config)
    │       │
    │       └── LangGraph restores state, continues from present_node
    │           present_node returns the user_response
    │           classify_node runs next
    │
    └── _run_and_respond() returns "complete" or "waiting" (if another loop)
```

---

## Dependencies

| Package            | Purpose                                      |
|--------------------|----------------------------------------------|
| `langgraph`        | Agent state machine + interrupt/resume       |
| `langchain`        | LLM abstraction layer                        |
| `langchain-groq`   | Groq LLM integration                         |
| `langchain-community` | Tavily search tool                        |
| `fastapi`          | HTTP API framework                           |
| `uvicorn`          | ASGI server                                  |
| `tavily-python`    | Web search API client                        |
| `pydantic`         | Data validation / structured LLM output      |
| `python-dotenv`    | Load `.env` file                             |
| `pyjwt`            | JWT token encode/verify (server-side)        |
| `chromadb`         | Vector store (available, not in active flow) |
| `semanticscholar`  | Academic search (available, not in active flow) |

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
