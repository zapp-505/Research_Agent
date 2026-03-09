# Research Agent

An AI-powered research assistant with a human-in-the-loop confirmation step. The user submits a query, the agent interprets it and presents a structured summary for confirmation, then generates a full research report.

---

## Project Structure

```
Research_Agent/
├── backend/          # FastAPI server + LangGraph agent (Python)
└── ai-frontend/      # React frontend (not used for MVP — Streamlit is used instead)
```

---

## How It Works (End-to-End)

```
User submits query
        │
        ▼
POST /chat/start  (Firebase ID token required)
        │
        ▼
  [analyze_node]     Groq LLM parses the query into:
                     domain, goal, assumptions, confidence
        │
        ▼
  [present_node]     Formats a human-readable summary.
                     LangGraph interrupt() pauses the graph here.
                     API returns: { status: "waiting", message: <summary> }
        │
        ▼
User reads summary, replies (yes / correction / reject)
        │
        ▼
POST /chat/resume  (same thread_id, Firebase token required)
        │
        ▼
  [classify_node]    Groq LLM classifies the reply:
                     CONFIRMED → proceed to research
                     CORRECTED → loop back to analyze with corrections
                     REJECTED  → loop back to analyze, corrections cleared
        │
   CONFIRMED │
        ▼
  [research_node]    Optionally runs a Tavily web search.
                     Groq LLM generates full structured report.
                     API returns: { status: "complete", message: <report> }
```

---

## Tech Stack

| Layer            | Technology                              |
|------------------|-----------------------------------------|
| Agent framework  | LangGraph                               |
| LLM              | Groq — `llama-3.3-70b-versatile`        |
| Web search       | Tavily                                  |
| API server       | FastAPI + Uvicorn                       |
| Auth             | Firebase Admin SDK (ID token verify)    |
| Frontend (MVP)   | Streamlit (planned)                     |

---

## API Endpoints

| Method | Path           | Auth required | Description                                      |
|--------|----------------|---------------|--------------------------------------------------|
| GET    | `/index`       | No            | Health check                                     |
| GET    | `/auth/verify` | Yes           | Verifies Firebase token, returns uid/email/name  |
| POST   | `/chat/start`  | Yes           | Starts a new research conversation               |
| POST   | `/chat/resume` | Yes           | Resumes a paused conversation                    |

All protected endpoints require `Authorization: Bearer <Firebase ID token>`.

### POST /chat/start

```json
Request:  { "query": "Tell me about agricultural drone technology" }
Response (waiting): { "status": "waiting", "message": "...", "thread_id": "uuid" }
Response (complete): { "status": "complete", "message": "...", "thread_id": "uuid" }
```

### POST /chat/resume

```json
Request:  { "thread_id": "uuid", "user_response": "yes" }
Response: { "status": "complete", "message": "..." , "thread_id": "uuid" }
```

---

## Setup & Running

See [backend/README.md](backend/README.md) for full setup instructions.

---

## License

MIT




