"""
session_store.py
CRUD operations for the 'sessions' MongoDB collection.

A session document:
    {
        "_id":         str  (UUID — also used as LangGraph thread_id),
        "thread_id":   str  (same as _id — explicit copy for clarity),
        "user_id":     str  (Firebase uid — scopes all queries),
        "title":       str  (display name shown in sidebar),
        "agent_phase": str  ("idle" | "waiting" | "complete"),
        "created_at":  datetime,
        "updated_at":  datetime,
    }
"""

import uuid
from datetime import datetime

from src.db.mongo_client import MongoDB
from src.logging.logger import logger

COLLECTION = "sessions"


async def create_session(user_id: str, title: str) -> dict:
    """
    Create a new session for a user and return the session document.
    """
    session_id = str(uuid.uuid4())
    session = {
        "_id":         session_id,
        "thread_id":   session_id,      # same UUID — passed to LangGraph config
        "user_id":     user_id,
        "title":       title,
        "agent_phase": "idle",
        "created_at":  datetime.utcnow(),
        "updated_at":  datetime.utcnow(),
    }
    col = MongoDB.db[COLLECTION]
    await col.insert_one(session)
    logger.info(f"Session created: {session_id} for user: {user_id}")
    return session


async def get_sessions(user_id: str) -> list:
    """
    Return all sessions belonging to this user, sorted newest first.
    Used to populate the sidebar.
    """
    col = MongoDB.db[COLLECTION]
    sessions = await col.find(
        {"user_id": user_id}
    ).sort("updated_at", -1).to_list(100)
    logger.info(f"Fetched {len(sessions)} sessions for user: {user_id}")
    return sessions


async def get_session(session_id: str, user_id: str) -> dict | None:
    """
    Return a single session document.
    Returns None if not found or if the session belongs to a different user.
    """
    col = MongoDB.db[COLLECTION]
    session = await col.find_one({"_id": session_id, "user_id": user_id})
    if session:
        logger.info(f"Session fetched: {session_id}")
    else:
        logger.warning(f"Session not found or unauthorized: {session_id} for user: {user_id}")
    return session


async def update_session(session_id: str, user_id: str, updates: dict) -> dict | None:
    """
    Update specific fields on a session document.
    Always stamps updated_at automatically.
    Returns the updated session document.
    """
    col = MongoDB.db[COLLECTION]
    await col.update_one(
        {"_id": session_id, "user_id": user_id},
        {"$set": {**updates, "updated_at": datetime.utcnow()}},
    )
    logger.info(f"Session updated: {session_id} — fields: {list(updates.keys())}")
    return await get_session(session_id, user_id)


async def delete_session(session_id: str, user_id: str) -> bool:
    """
    Delete a session document.
    Returns True if a document was deleted, False if nothing matched.
    """
    col = MongoDB.db[COLLECTION]
    result = await col.delete_one({"_id": session_id, "user_id": user_id})
    deleted = result.deleted_count > 0
    if deleted:
        logger.info(f"Session deleted: {session_id}")
    else:
        logger.warning(f"Delete failed — session not found: {session_id} for user: {user_id}")
    return deleted