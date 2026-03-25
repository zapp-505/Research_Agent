import streamlit as st

def render_chat_messages():
    messages = st.session_state.get("messages", [])
    
    for idx, msg in enumerate(messages):
        if not isinstance(msg, dict):
            continue
            
        role = msg.get("role")
        content = msg.get("content")
        
        if role == "user":
            with st.chat_message("user"):
                st.write(content)
        elif role in ["assistant", "ai"]:
            name = msg.get("name")
            
            with st.chat_message("assistant"):
                if name and name != "assistant":
                    st.caption(f"**{name}**")
                st.write(content)
                
    # If the graph is complete, show the final report from the session state if available 
    if st.session_state.get("phase") == "complete" and st.session_state.get("last_response"):
        resp = st.session_state["last_response"]
        report = resp.get("final_report")
        if report:
            with st.chat_message("assistant", avatar="📄"):
                st.markdown("### Final Research Report")
                st.markdown(report)

def render_interrupt_ui():
    """Renders the special UI blocks for when the agent is paused and waiting for human input."""
    phase = st.session_state.get("phase")
    itype = st.session_state.get("interrupt_type")
    
    if phase == "waiting":
        resp = st.session_state.get("last_response", {})
        message = resp.get("message", "The agent is waiting for your input.")
        
        if itype == "expert_critique":
            expert_name = resp.get("expert_name", "Expert")
            expert_role = resp.get("expert_role", "Reviewer")
            st.markdown(f"**⚔️ {expert_name}** — *{expert_role}*")
            st.info(message)
        elif itype == "confirmation":
            st.warning("Please confirm or adjust the interpretation:")
            st.write(message)
        else:
            st.info(message)
