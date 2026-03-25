import streamlit as st
from services import api

def render_sidebar():
    with st.sidebar:
        st.title("Research Agent")
        
        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            st.session_state["thread_id"] = None
            st.session_state["phase"] = "idle"
            st.session_state["messages"] = []
            st.session_state["interrupt_type"] = None
            st.session_state["last_response"] = None
            st.rerun()
            
        st.divider()
        st.subheader("Your Sessions")
        
        try:
            sessions = api.get_sessions(st.session_state["token"])
            if not sessions:
                st.caption("No prior chat sessions found.")
            else:
                for session in sessions:
                    title = session.get("title", "Untitled Session")
                    # Add a button for each session
                    if st.button(f"💬 {title}", key=session["_id"], use_container_width=True):
                        st.session_state["thread_id"] = session["thread_id"]
                        
                        # Fetch history immediately
                        history = api.get_thread_history(st.session_state["token"], session["thread_id"])
                        st.session_state["messages"] = history.get("messages", [])
                        
                        # Phase state is tracked on the session document directly
                        st.session_state["phase"] = session.get("agent_phase", "idle")
                        
                        # For returning to an interrupted thread, we need the interrupt payload logic. 
                        # In a fully complete app, you'd fetch the raw state via a /chat/{id}/state endpoint
                        # but we can just clear interrupt_type and let the standard flow handle it, or 
                        # simulate a blank waiting state until they type something.
                        st.session_state["interrupt_type"] = "resumed" 
                        st.session_state["last_response"] = {}
                        
                        st.rerun()
        except Exception as e:
            st.error(f"Failed to load sessions: {e}")
