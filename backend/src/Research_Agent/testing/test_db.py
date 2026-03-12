"""
test_db.py
Standalone async test for MongoDB connection and session_store CRUD.

Run from the backend/ directory:
    uv run python src/Research_Agent/testing/test_db.py

What this tests:
    1. MongoDB connects successfully
    2. create_session()  — inserts a doc, returns it with thread_id
    3. get_sessions()    — lists sessions for the user
    4. get_session()     — fetches one by id (correct user)
    5. get_session()     — returns None for wrong user (access control)
    6. update_session()  — updates a field, stamps updated_at
    7. delete_session()  — removes the doc, returns True
    8. delete_session()  — second delete returns False (idempotency check)
"""

import asyncio
from src.db.mongo_client import MongoDB
from src.db.session_store import (
    create_session,
    get_sessions,
    get_session,
    update_session,
    delete_session,
)

# ── Fake Firebase UIDs for testing ──────────────────────────────────────────
USER_A = "test_user_uid_A"
USER_B = "test_user_uid_B"


async def run_tests():
    # ── Setup ─────────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("  DB TEST SUITE")
    print("="*60)

    await MongoDB.connect()
    print("✅  MongoDB connected\n")

    # ── Test 1: create_session ─────────────────────────────────────────────
    session = await create_session(USER_A, "Solar Drone Research")
    assert session["_id"] == session["thread_id"], "❌  _id and thread_id must be equal"
    assert session["user_id"] == USER_A
    assert session["agent_phase"] == "idle"
    print(f"✅  create_session  → _id: {session['_id'][:8]}...")

    session_id = session["_id"]

    # ── Test 2: get_sessions ───────────────────────────────────────────────
    sessions = await get_sessions(USER_A)
    assert any(s["_id"] == session_id for s in sessions), "❌  Created session not found in list"
    print(f"✅  get_sessions    → {len(sessions)} session(s) found for USER_A")

    # ── Test 3: get_session (correct user) ────────────────────────────────
    fetched = await get_session(session_id, USER_A)
    assert fetched is not None, "❌  get_session returned None for valid owner"
    assert fetched["title"] == "Solar Drone Research"
    print(f"✅  get_session     → title: '{fetched['title']}'")

    # ── Test 4: get_session (wrong user — access control) ─────────────────
    unauthorized = await get_session(session_id, USER_B)
    assert unauthorized is None, "❌  Access control failed — USER_B should NOT see USER_A's session"
    print("✅  access_control  → USER_B correctly blocked from USER_A's session")

    # ── Test 5: update_session ────────────────────────────────────────────
    updated = await update_session(session_id, USER_A, {"agent_phase": "waiting", "title": "Updated Title"})
    assert updated["agent_phase"] == "waiting", "❌  agent_phase not updated"
    assert updated["title"] == "Updated Title", "❌  title not updated"
    assert updated["updated_at"] > session["updated_at"], "❌  updated_at not refreshed"
    print(f"✅  update_session  → phase: '{updated['agent_phase']}', title: '{updated['title']}'")

    # ── Test 6: delete_session ────────────────────────────────────────────
    deleted = await delete_session(session_id, USER_A)
    assert deleted is True, "❌  delete_session should return True"
    print("✅  delete_session  → deleted successfully")

    # ── Test 7: delete idempotency ────────────────────────────────────────
    deleted_again = await delete_session(session_id, USER_A)
    assert deleted_again is False, "❌  Second delete should return False"
    print("✅  idempotency     → second delete correctly returned False")

    # ── Cleanup ───────────────────────────────────────────────────────────
    await MongoDB.close()
    print("\n" + "="*60)
    print("  ALL TESTS PASSED ✅")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_tests())
