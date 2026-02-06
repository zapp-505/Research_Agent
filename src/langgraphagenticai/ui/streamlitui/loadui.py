"""
Load and initialize Streamlit UI
"""

import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from langgraphagenticai.ui.uiconfigfile import UIConfig
from langgraphagenticai.ui.streamlitui.display_result import display_chat_history, display_message


def initialize_ui():
    """
    Initialize the Streamlit UI with configuration
    """
    config = UIConfig()
    streamlit_config = config.get_streamlit_config()
    
    st.set_page_config(
        page_title=streamlit_config.get('page_title', 'LangGraph Agentic AI'),
        page_icon=streamlit_config.get('page_icon', '🤖'),
        layout=streamlit_config.get('layout', 'wide')
    )
    
    st.title(config.get('UI', 'title', fallback='LangGraph Agentic AI'))


def load_ui():
    """
    Load and run the main UI
    """
    initialize_ui()
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    display_chat_history(st.session_state.messages)
    
    # Chat input
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        display_message(user_input, is_user=True)
        
        # Generate bot response (placeholder)
        bot_response = f"Echo: {user_input}"
        st.session_state.messages.append({"role": "assistant", "content": bot_response})
        display_message(bot_response, is_user=False)
        
        st.rerun()


if __name__ == "__main__":
    load_ui()
