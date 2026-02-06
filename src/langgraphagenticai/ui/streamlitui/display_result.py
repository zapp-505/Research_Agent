"""
Display results in Streamlit UI
"""

import streamlit as st


def display_message(message, is_user=True):
    """
    Display a single message in the chat interface
    
    Args:
        message: Message text to display
        is_user: Whether this is a user message or bot message
    """
    if is_user:
        st.markdown(f"**You:** {message}")
    else:
        st.markdown(f"**Bot:** {message}")


def display_chat_history(messages):
    """
    Display full chat history
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
    """
    for msg in messages:
        is_user = msg.get("role") == "user"
        display_message(msg.get("content", ""), is_user=is_user)


def display_thinking_indicator():
    """
    Display a thinking/loading indicator
    """
    with st.spinner("Thinking..."):
        pass
