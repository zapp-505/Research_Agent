# Research Agent — Full System Implementation Plan

## Current State (What Is Already Done)

| Component | Status |
|---|---|
| All 7 LangGraph nodes (analyze → present → classify → panel_generator → moderator → expert → blue_team) | ✅ Done, tested via CLI |
| [state.py](file:///c:/Dev/Mini_Proj/backend/src/Research_Agent/state/state.py) with all gauntlet fields | ✅ Done |
| [graph_builder.py](file:///c:/Dev/Mini_Proj/backend/src/Research_Agent/graph/graph_builder.py) with MongoDBSaver + ToolNode | ✅ Done |
| [mongo_client.py](file:///c:/Dev/Mini_Proj/backend/src/db/mongo_client.py) (Motor async client) | ✅ Done |
| [session_store.py](file:///c:/Dev/Mini_Proj/backend/src/db/session_store.py) (session CRUD) | ✅ Done |
| [auth.py](file:///c:/Dev/Mini_Proj/backend/src/auth.py) (Firebase JWT verification) | ✅ Done |
| [app.py](file:///c:/Dev/Mini_Proj/backend/app.py), [chat.py](file:///c:/Dev/Mini_Proj/backend/src/routers/chat.py), [history.py](file:///c:/Dev/Mini_Proj/backend/src/routers/history.py) | ⚠️ Template only — wrong state fields, sync instead of async, missing gauntlet support |
| Streamlit frontend | ❌ Not started |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        STREAMLIT FRONTEND                       │
│   Login Page  ──►  Sidebar (sessions)  ──►  Chat Interface      │
│                                                                  │
│   Firebase JS SDK (get token) →  sends Bearer token with every  │
│   request to the FastAPI backend (HTTP polling, not websockets)  │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP (REST)
┌─────────────────────────▼───────────────────────────────────────┐
│                       FASTAPI BACKEND  (app.py)                  │
│                                                                  │
│  startup():                                                      │
│    ① Motor.connect()  → MongoDB Atlas (async Motor client)       │
│    ② MongoDBSaver(MongoClient(uri)) → separate sync pymongo      │
│    ③ GraphBuilder(checkpointer).build() → compiled LangGraph     │
│    All three stored on app.state                                 │
│                                                                  │
│  Routers:                                                        │
│    /auth/*      ← Firebase token verify                          │
│    /sessions/*  ← session CRUD (uses session_store.py)           │
│    /chat/*      ← start + resume (uses LangGraph graph)          │
└────────────────────┬──────────────────┬─────────────────────────┘
                     │                  │
          ┌──────────▼──────┐  ┌────────▼──────────────────────────┐
          │  MOTOR (async)  │  │  SYNC PYMONGO                      │
          │  research_agent │  │  checkpointing_db                  │
          │  db.sessions    │  │  db.checkpoints                    │
          │  (session meta) │  │  (full LangGraph state snapshots)  │  
          └─────────────────┘  └───────────────────────────────────┘
```

---

## The Two MongoDB Connections Explained

This is a deliberate design choice, not a bug.

| | Motor (async) | Sync pymongo via MongoDBSaver |
|---|---|---|
| **Used for** | Session metadata (title, user_id, status) | LangGraph checkpoint snapshots |
| **Database** | [research_agent](file:///c:/Dev/Mini_Proj/backend/src/Research_Agent/testing/contextBuilder.py#262-291) | `checkpointing_db` |
| **Collections** | [sessions](file:///c:/Dev/Mini_Proj/backend/src/db/session_store.py#46-57) | `checkpoints`, `checkpoint_writes` |
| **Who manages it** | Your code ([session_store.py](file:///c:/Dev/Mini_Proj/backend/src/db/session_store.py)) | LangGraph internals |
| **Why async** | FastAPI is async — Motor is the only async MongoDB driver | MongoDBSaver uses sync pymongo internally but wraps with `run_in_executor` so `astream()` still works |

**Do not merge these.** They serve separate concerns.

---

## Part 1: FastAPI Backend

### 1.1 [app.py](file:///c:/Dev/Mini_Proj/backend/app.py) — The Entry Point

[app.py](file:///c:/Dev/Mini_Proj/backend/app.py) is exactly like you said — the final composition point, like Streamlit's [main()](file:///c:/Dev/Mini_Proj/backend/src/Research_Agent/testing/test_gauntlet.py#75-167). It:
1. Creates the FastAPI app instance
2. Attaches middleware (CORS)
3. Registers all routers
4. Defines [startup](file:///c:/Dev/Mini_Proj/backend/app.py#21-26) and [shutdown](file:///c:/Dev/Mini_Proj/backend/app.py#27-30) lifecycle events

```
startup():
  ① await MongoDB.connect()          # motor client for session_store
  ② sync_client = MongoClient(uri)   # pymongo client for LangGraph checkpointer
     memory = MongoDBSaver(sync_client)
  ③ app.state.agent = GraphBuilder(checkpointer=memory).build()
  ④ app.state.sync_client = sync_client  # keep ref to close at shutdown

shutdown():
  ① await MongoDB.close()
  ② app.state.sync_client.close()
```

**Why not pass GraphBuilder the motor client?**
[MongoDBSaver](file:///C:/Dev/Mini_Proj/backend/.venv/Lib/site-packages/langgraph/checkpoint/mongodb/saver.py#66-622) is a LangGraph library class requiring sync pymongo. Motor is async only. They cannot be swapped. Two clients, same Atlas cluster, no conflict.

---

### 1.2 Firebase Auth — How It Works End to End

```
Streamlit                      FastAPI                     Firebase
─────────                      ───────                     ────────
① User logs in via             
  firebase JS/Python SDK  ──────────────────────────────►  Firebase Auth returns
  (in Streamlit)                                            id_token (JWT, 1hr expiry)

② Streamlit stores token
   in st.session_state

③ Every API call adds:
   headers = {"Authorization": "Bearer <id_token>"}

④                        ──►  get_current_user() dependency
                               reads Authorization header
                               calls firebase_admin.auth.verify_id_token(token)
                         ◄──►  Firebase verifies signature
                               returns decoded dict:
                               {"uid": "abc", "email": "user@example.com"}

⑤                              user_id = decoded["uid"]
                               passed to route handler
                               ALL DB queries include user_id filter
```

[auth.py](file:///c:/Dev/Mini_Proj/backend/src/auth.py) (already implemented) does steps ④–⑤ via the [get_current_user](file:///c:/Dev/Mini_Proj/backend/src/auth.py#21-48) FastAPI dependency.

**Session isolation:** Every `session_store` function takes `user_id` as a parameter and includes it in every MongoDB query. A user can never access another user's sessions even if they know the thread_id.

---

### 1.3 Chat Router — The Core API

This is the most important file. Two endpoints drive the entire user experience.

#### POST `/chat/start`

Called once per new conversation. Does:
1. Firebase token → `user_id`
2. `session_store.create_session(user_id, title=query[:60])` → returns [session](file:///c:/Dev/Mini_Proj/backend/src/db/session_store.py#59-71) with `thread_id`
3. Build `initial_state` (all LangGraph state fields — see below)
4. `async for _ in agent.astream(initial_state, config): pass` — run graph until interrupt or END
5. Read graph state → extract interrupt payload
6. `session_store.update_session(session_id, {"agent_phase": "waiting"})` 
7. Return structured response to frontend

**Initial state must include ALL fields defined in state.py:**
```python
initial_state = {
    "raw_input":            query,
    "messages":             [{"role": "user", "content": query}],
    "interpreted_context":  None,
    "is_confirmed":         False,
    "iteration_count":      0,
    "user_corrections":     [],
    "personas":             None,
    "current_speaker_idx":  0,
    "round_number":         0,
    "expert_critique":      [],
    "is_gauntlet_complete": False,
    "final_report":         None,
    "synthesis_thread":     [],
}
```
Missing ANY field → LangGraph TypedDict validation error.

#### POST `/chat/resume`

Called for every user reply during the conversation. Does:
1. Firebase token → `user_id`
2. `session_store.get_session(thread_id, user_id)` → verify ownership
3. If session is `"complete"` → return 400 (can't resume a done graph)
4. `async for _ in agent.astream(Command(resume=user_response), config): pass`
5. Read state → extract interrupt or final report
6. Update `agent_phase` in session_store
7. Return response

#### The Response Format (both endpoints return this shape)

```json
// Graph paused at confirmation (present_node)
{
  "status": "waiting",
  "interrupt_type": "confirmation",
  "message": "Domain: Solar Drones\nGoal: autonomous reforestation...",
  "expert_name": null,
  "expert_role": null,
  "thread_id": "abc-123",
  "round_number": null
}

// Graph paused at expert critique (expert_node)
{
  "status": "waiting",
  "interrupt_type": "expert_critique",
  "message": "[Critique text]\n\nQUESTION: Have you validated battery life?",
  "expert_name": "Dr. Regulatory Hawk",
  "expert_role": "FAA compliance auditor",
  "thread_id": "abc-123",
  "round_number": 1
}

// Graph finished (blue_team produced final report)
{
  "status": "complete",
  "interrupt_type": null,
  "message": null,
  "final_report": "## Executive Summary\n...",
  "thread_id": "abc-123"
}
```

**How to read the interrupt payload from graph state:**
```python
state = agent.get_state(config)

if state.next:  # graph is paused at an interrupt
    interrupt_val = state.tasks[0].interrupts[0].value
    # interrupt_val is the dict passed to interrupt() in the node
    # For present_node: {"type": "confirmation", "summary": "..."}
    # For expert_node:  {"type": "expert_critique", "summary": "...", 
    #                    "expert_name": "...", "expert_role": "..."}
else:  # graph finished
    final_report = state.values.get("final_report")
```

---

### 1.4 Sessions Router

```
GET    /sessions          → list all sessions for user (sidebar)
GET    /sessions/{id}     → get single session metadata
DELETE /sessions/{id}     → delete session (from session_store only — 
                            LangGraph checkpoints stay, harmless)
```

These are thin wrappers over [session_store.py](file:///c:/Dev/Mini_Proj/backend/src/db/session_store.py). Already implemented and correct.

---

### 1.5 History Router

The history of a conversation is the `messages` field from LangGraph state — it accumulates across every node that writes to it. Read it directly from the checkpointer:

```python
config = {"configurable": {"thread_id": thread_id}}
state  = agent.get_state(config)
messages = state.values.get("messages", [])
```

Create `src/db/chat_history.py` with two functions:
- `get_thread_messages(agent, thread_id)` → returns `messages` list from graph state
- `get_thread_report(agent, thread_id)` → returns `final_report` from graph state

The history router needs [agent](file:///c:/Dev/Mini_Proj/backend/src/Research_Agent/testing/contextBuilder.py#262-291) passed in — get it from `request.app.state.agent`.

---

## Part 2: Streamlit Frontend

### 2.1 Why Streamlit (not React)

Streamlit re-renders the entire page on each interaction. This actually maps well to the polling pattern: user sends a message → page rerenders → show new state. No websockets needed.

### 2.2 File Structure

```
frontend/
├── app.py              ← Streamlit entry point (streamlit run frontend/app.py)
├── pages/
│   └── chat.py         ← could use multi-page format
├── components/
│   ├── sidebar.py      ← session list component
│   ├── chat_area.py    ← message display
│   └── input_bar.py    ← text input + send
└── services/
    ├── api.py          ← all HTTP calls to FastAPI (using requests or httpx)
    └── firebase_auth.py ← Firebase login via pyrebase or firebase-admin SDK
```

### 2.3 Authentication in Streamlit

Streamlit doesn't have a native auth system. Use `pyrebase4` (Firebase Python client) for login:

```python
import pyrebase
firebase = pyrebase.initialize_app(firebase_config)
auth_client = firebase.auth()

# Login
user = auth_client.sign_in_with_email_and_password(email, password)
id_token = user["idToken"]
st.session_state["token"] = id_token
st.session_state["user_id"] = user["localId"]
```

Store `id_token` in `st.session_state`. Pass it as Bearer token in every API call.

**Token refresh:** Firebase tokens expire in 1 hour. Call `auth_client.refresh(user["refreshToken"])` if you get a 401 from the API.

### 2.4 The Streamlit Session State Machine

```python
# st.session_state keys:
# "token"        - Firebase id_token
# "thread_id"    - current LangGraph thread
# "phase"        - "idle" | "waiting" | "complete"
# "interrupt_type" - "confirmation" | "expert_critique" | None
# "messages"     - list of displayed messages
# "last_response" - full API response dict
```

### 2.5 The Polling Loop (Critical Pattern)

Streamlit doesn't do real-time streaming natively. The pattern is:

```
User types query → clicks Send
  → POST /chat/start (or /chat/resume)
  → API blocks while graph runs (could be 5-30s)
  → API returns when graph hits an interrupt or finishes
  → Streamlit rerenders with the response
  → Show message + input for user's next reply
  → Repeat
```

For long-running nodes (blue_team can take 30-60s), show a spinner:
```python
with st.spinner("Running expert panel... this may take a minute"):
    response = api.chat_start(token, query)
```

### 2.6 Chat UI Flow

```
Page loads
│
├── Not logged in → show Login form
│     user enters email/password
│     → pyrebase sign_in
│     → store token in st.session_state
│     → rerender
│
└── Logged in → show sidebar + chat
      │
      Sidebar: GET /sessions → list sessions
               "New Chat" button → clears st.session_state["thread_id"]
      │
      Chat area: if no thread_id → show empty input
                 if thread_id → show message history
      │
      User types query → Send
        → POST /chat/start { query }
        → response comes back:
            if status == "waiting" and type == "confirmation":
                show "Is this correct?" card with Confirm/Edit buttons
            if status == "waiting" and type == "expert_critique":
                show expert name + role badge, show critique, show text input
            if status == "complete":
                show final report (st.markdown with full formatting)
      │
      User responds → Send Reply
        → POST /chat/resume { thread_id, user_response }
        → same response handling as above
```

### 2.7 Displaying Expert Identity

In the chat area, distinguish each expert with a colored badge:
```python
if interrupt_type == "expert_critique":
    st.markdown(f"**⚔️ {expert_name}** — *{expert_role}*")
    st.info(message)   # expert's critique in a blue box
    user_reply = st.text_area("Your response:")
    if st.button("Send Response"):
        # call /chat/resume
```

---

## Part 3: Build Order (Exact Sequence)

### Phase A: Fix the Backend (This Week)

```
1. app.py           Fix startup/shutdown with both MongoDB connections
2. chat.py          Full async rebuild — most important file
3. chat_history.py  Create it (history.py currently crashes without it)
4. history.py       Fix to use session_store + chat_history
5. auth router      Check if it has anything beyond what auth.py provides
```

**Test each step with curl/Postman before moving to the next.**

```bash
# Test /chat/start
curl -X POST http://localhost:8000/chat/start \
  -H "Authorization: Bearer <firebase_token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "feasibility of solar drones for reforestation"}'

# Should return: {"status": "waiting", "interrupt_type": "confirmation", ...}

# Test /chat/resume
curl -X POST http://localhost:8000/chat/resume \
  -H "Authorization: Bearer <firebase_token>" \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "<from above>", "user_response": "yes that is correct"}'
```

### Phase B: Build Streamlit (After Backend Works)

```
1. services/api.py          All HTTP calls to FastAPI
2. services/firebase_auth.py  Login / token management
3. app.py (Streamlit)       Main layout — sidebar + chat area
4. components/sidebar.py    Session list
5. components/chat_area.py  Message display with expert badges
6. components/input_bar.py  Send button logic
```

---

## Part 4: Key Requirements for Error-Free Operation

| Requirement | Why it matters |
|---|---|
| Atlas IP whitelist | MongoDBSaver fails SSL handshake if IP not whitelisted |
| All state fields in initial_state | Missing fields → TypedDict validation error in LangGraph |
| `async def` on all route handlers | LangGraph `astream` is async — sync handlers will deadlock |
| `agent.get_state()` check before resume | Thread may not exist if user tampers with thread_id |
| `user_id` filter on every DB query | Security — prevents cross-user data access |
| `st.session_state` for all Streamlit state | Streamlit rerenders whole page on every action |
| Firebase token passed in every API call | Auth dependency rejects requests without valid Bearer token |

---

## What Does NOT Need to Change

[mongo_client.py](file:///c:/Dev/Mini_Proj/backend/src/db/mongo_client.py), [session_store.py](file:///c:/Dev/Mini_Proj/backend/src/db/session_store.py), [auth.py](file:///c:/Dev/Mini_Proj/backend/src/auth.py) (middleware), [graph_builder.py](file:///c:/Dev/Mini_Proj/backend/src/Research_Agent/graph/graph_builder.py), all 7 nodes, [state.py](file:///c:/Dev/Mini_Proj/backend/src/Research_Agent/state/state.py) — all correct. Do not touch them.
