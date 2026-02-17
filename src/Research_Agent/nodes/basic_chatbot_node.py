"""
Basic chatbot node implementation
"""

def basic_chatbot_node(state):
    """
    Basic chatbot node that processes user input and generates responses
    
    Args:
        state: Current state of the graph
        
    Returns:
        Updated state with bot response
    """
    user_input = state.get("user_input", "")
    
    # Process user input and generate response
    response = f"Echo: {user_input}"
    
    state["bot_response"] = response
    return state
