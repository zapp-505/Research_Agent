# Research Agent Simulator 

## Overview

This repository contains a small proof‑of‑concept agentic AI application built using **LangGraph** on the backend and a **React** frontend. The system implements a human‑in‑the‑loop research assistant: user queries are progressively interpreted, clarified, and then researched by a language model.

The workspace is divided into two top‑level folders:

- `backend/` – Python backend powered by FastAPI (TODO) and LangGraph. It defines the agent graph, state types, LLM integrations, and a lightweight HTTP API.
- `ai-frontend/` – Create React App based UI managing multiple chat threads. It sends user messages to the backend and displays responses.

## Backend architecture

The backend uses LangGraph to define a state‑machine graph with four primary nodes:

```
START → analyze → present → classify → [analyze loop | research] → END
```

- **State definition** – a `TypedDict` describing the shared mutable context that flows through every node (`backend/src/Research_Agent/state/state.py`).
- **Nodes** – each node is a pure function that takes the current state, invokes an LLM or performs other logic, and returns a dict of updates. Nodes live under `backend/src/Research_Agent/nodes/`.
- **Graph builder** – wires nodes together and compiles a `StateGraph` instance with a `MemorySaver` checkpoint. The compiled graph is exposed as a singleton for requests via `backend/src/Research_Agent/graph/graph_builder.py`.
- **LLM integrations** – abstraction wrappers around Groq models are in `backend/src/Research_Agent/LLMS/`.

The project currently includes a sketch of the FastAPI entrypoint (`backend/app.py`) with `TODO` comments where HTTP endpoints should be added.

### Run‑ID and state management

Every conversation is represented by a single state dict owned by a LangGraph run. When you start a new chat (via `compiled_graph.start(...)`), the graph returns a run ID. This ID is used to resume the same state on subsequent messages. The frontend stores this ID in each chat thread.

### Testing and experimentation

A simple standalone example graph lives in `backend/src/Research_Agent/testing/contextBuilder.py` which illustrates the same pattern with clarifying questions, interrupt/resume, and final research output.

## Frontend architecture

The React app (`ai-frontend/`) maintains local state for:

- `chats` – list of conversation objects, each with messages and `threadId` (the backend run ID).
- `activeChat` – index of the currently selected chat.
- `agentPhase` – whether the agent is idle, waiting for confirmation, typing, or complete.

Key behavior in `src/App.js`:

- On a first message or when the agent is idle, POST to `/chat/start` with the user query. The backend responds with a `thread_id` and the AI reply.
- When waiting for a continuation, POST to `/chat/resume` with `thread_id` and the new user response.
- `newChat()` resets UI state and clears the `threadId` to start a fresh conversation.

UI components under `src/components` manage the chat interface, input bar, sidebar, etc.

## Getting started

### Prerequisites

- Python 3.11+ (backend uses `venv` in `backend/.venv`)
- Node.js 18+ / npm or yarn
- Groq API key set in `.env` for backend

### Backend

```powershell
cd backend
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
# run development server once endpoints are implemented
python app.py
```

Replace `python app.py` with a FastAPI server command (e.g. `uvicorn app:app --reload`) once the HTTP routes are added.

### Frontend

```bash
cd ai-frontend
npm install
npm start
```

This will launch the React app on `http://localhost:3000`.

## Extending the project

- **Add FastAPI endpoints** in `backend/app.py` for `/chat/start`, `/chat/resume`, and `/health` using the compiled graph. See the earlier discussion in this thread for sample code.
- **Persist state** using a different checkpointer (Redis, database) instead of `MemorySaver` if you need durability across restarts.
- **Enhance UI** with authentication, user sessions, or conversation storage.
- **Refactor state** with more detailed typed models as the agent becomes more complex.

## License

MIT




