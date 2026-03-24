"""
chat_history.py
Retrieve and manage chat history for sessions using LangGraph's state checkpointer.
"""
from typing import List, Dict, Any

async def get_thread_messages(agent: Any, thread_id: str) -> List[Dict[str, Any]]:
    config = {"configurable": {"thread_id": thread_id}}
    state = await agent.aget_state(config)
    if not state or not state.values:
        return []
    return state.values.get("messages", [])

async def get_thread_report(agent: Any, thread_id: str) -> str | None:
    config = {"configurable": {"thread_id": thread_id}}
    state = await agent.aget_state(config)
    if not state or not state.values:
        return None
    return state.values.get("final_report")

async def get_chat_summary(agent: Any, thread_id: str, max_messages: int = 10) -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    state = await agent.aget_state(config)
    
    if not state or not state.values:
        return {"error": "No checkpoint found"}
        
    messages = state.values.get("messages", [])
    
    first_user_msg = None
    for msg in messages:
        if isinstance(msg, dict) and msg.get("role") == "user":
            first_user_msg = msg.get("content")
            break
            
    last_messages = messages[-max_messages:] if messages else []
    
    metadata = {
        "total_messages": len(messages),
        "original_query": first_user_msg,
        "final_report_present": "final_report" in state.values,
    }
    
    return {
        "thread_id": thread_id,
        "metadata": metadata,
        "last_messages": last_messages
    }
