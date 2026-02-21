



"""
Human-in-the-Loop Research Agent with LangGraph
Asks clarifying questions before performing research
"""

import os
from typing import TypedDict, Annotated, Literal
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ============================================================================
# STATE DEFINITION
# ============================================================================

class ResearchAgentState(TypedDict):
    """State for the research agent with human-in-the-loop"""
    initial_query: str  # Original user request
    clarification_questions: list[str]  # Questions asked by agent
    user_answers: list[str]  # Answers provided by user
    questions_asked: int  # Counter for questions
    ready_for_research: bool  # Flag to indicate if ready to research
    final_research: str  # Final research output
    messages: list  # Chat history


# ============================================================================
# LLM SETUP
# ============================================================================

def get_llm():
    """Initialize and return the Groq LLM"""
    api_key = os.getenv("GROQ_API_KEY")
    return ChatGroq(
        model="openai/gpt-oss-120b",
        api_key=api_key,
        temperature=0.7
    )


# ============================================================================
# GRAPH NODES
# ============================================================================

def question_generator_node(state: ResearchAgentState) -> ResearchAgentState:
    """
    Generate clarifying questions based on the initial query and previous answers
    """
    llm = get_llm()
    
    initial_query = state.get("initial_query", "")
    questions_asked = state.get("questions_asked", 0)
    previous_answers = state.get("user_answers", [])
    previous_questions = state.get("clarification_questions", [])
    
    # Build context for the LLM
    context = f"User's initial request: {initial_query}\n\n"
    
    if previous_questions and previous_answers:
        context += "Previous clarifications:\n"
        for q, a in zip(previous_questions, previous_answers):
            context += f"Q: {q}\nA: {a}\n\n"
    
    # Prompt to generate next clarifying question
    prompt = f"""{context}
You are a research assistant. The user wants information about: "{initial_query}"

Generate ONE specific clarifying question to gather more details about what exactly they want to know.
Focus on aspects like:
- Specific subtopics they're interested in
- Depth of information needed (basic overview vs detailed analysis)
- Particular aspects (habitat, behavior, evolution, conservation, etc.)
- Geographic focus or time period if relevant

Generate ONLY the question, no additional text."""

    response = llm.invoke(prompt)
    new_question = response.content.strip()
    
    # Update state
    state["clarification_questions"] = state.get("clarification_questions", []) + [new_question]
    state["questions_asked"] = questions_asked + 1
    
    return state


def human_input_node(state: ResearchAgentState) -> ResearchAgentState:
    """
    Interrupt execution to wait for human input
    """
    current_question = state["clarification_questions"][-1]
    
    # This will pause the graph execution and wait for human response
    user_answer = interrupt(
        {
            "question": current_question,
            "type": "clarification"
        }
    )
    
    # Store the user's answer
    state["user_answers"] = state.get("user_answers", []) + [user_answer]
    
    return state


def check_questions_node(state: ResearchAgentState) -> ResearchAgentState:
    """
    Determine if enough questions have been asked using LLM evaluation
    """
    llm = get_llm()
    
    initial_query = state.get("initial_query", "")
    questions_asked = state.get("questions_asked", 0)
    questions = state.get("clarification_questions", [])
    answers = state.get("user_answers", [])
    
    # Safety limits
    MAX_QUESTIONS = 5
    
    if questions_asked >= MAX_QUESTIONS:
        state["ready_for_research"] = True
        return state
        
    # Build context for evaluation
    context = f"User's initial request: {initial_query}\n\n"
    if questions and answers:
        context += "Information gathered so far:\n"
        for q, a in zip(questions, answers):
            context += f"Q: {q}\nA: {a}\n\n"
            
    # Ask LLM if we have enough info
    prompt = f"""{context}
You are a requirements analyst. Your goal is to gather enough information to write a detailed requirements specification for the user's request.

Analyze the information gathered so far. Do you have enough sufficient, detailed information to construct a comprehensive requirements summary?
Consider:
- Is the scope clear?
- Are the specific goals or subtopics defined?
- Is the level of detail known?

Reply with ONLY "YES" if you have enough information, or "NO" if you still need to ask clarifying questions."""

    response = llm.invoke(prompt)
    decision = response.content.strip().upper()
    
    print(f"\n🤔 Agent decision on context sufficiency: {decision}")
    
    if "YES" in decision:
        state["ready_for_research"] = True
    else:
        state["ready_for_research"] = False
    
    return state


def research_node(state: ResearchAgentState) -> ResearchAgentState:
    """
    Generate the final requirements summary based on gathered context
    """
    llm = get_llm()
    
    initial_query = state.get("initial_query", "")
    questions = state.get("clarification_questions", [])
    answers = state.get("user_answers", [])
    
    # Build comprehensive context
    context = f"Original request: {initial_query}\n\n"
    context += "Clarifying information gathered:\n"
    
    for q, a in zip(questions, answers):
        context += f"Q: {q}\nA: {a}\n\n"
    
    # Generate requirements summary
    research_prompt = f"""{context}
Based on the user's initial request and the clarifying information gathered above, please compile a comprehensive "Requirements Summary".

Your output should be structured as follows:
1. **Project/Goal Overview**: A clear statement of what the user wants to achieve.
2. **Key Requirements**: The specific features, topics, or constraints identified.
3. **Scope and Limitations**: What is included and what is excluded (if mentioned).
4. **Detailed Specifications**: Any specific details gathered from the Q&A (e.g., specific technologies, animals, time periods, etc.).
5. **Next Steps / Recommendations**: Suggested actions based on these requirements.

Ensure this serves as a complete standalone document describing the user's needs."""

    response = llm.invoke(research_prompt)
    state["final_research"] = response.content.strip()
    
    return state


# ============================================================================
# ROUTING LOGIC
# ============================================================================

def should_continue(state: ResearchAgentState) -> Literal["ask_more", "do_research"]:
    """
    Decide whether to ask more questions or proceed to research
    """
    if state.get("ready_for_research", False):
        return "do_research"
    else:
        return "ask_more"


# ============================================================================
# GRAPH BUILDER
# ============================================================================

def build_research_agent_graph():
    """
    Build and compile the LangGraph for human-in-the-loop research
    """
    # Create the graph
    workflow = StateGraph(ResearchAgentState)
    
    # Add nodes
    workflow.add_node("question_generator", question_generator_node)
    workflow.add_node("human_input", human_input_node)
    workflow.add_node("check_questions", check_questions_node)
    workflow.add_node("research", research_node)
    
    # Define the flow
    workflow.add_edge(START, "question_generator")
    workflow.add_edge("question_generator", "human_input")
    workflow.add_edge("human_input", "check_questions")
    
    # Conditional routing based on whether we need more questions
    workflow.add_conditional_edges(
        "check_questions",
        should_continue,
        {
            "ask_more": "question_generator",
            "do_research": "research"
        }
    )
    
    workflow.add_edge("research", END)
    
    # Compile with memory for interrupt support
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app


# ============================================================================
# USAGE FUNCTIONS
# ============================================================================

def run_research_agent(initial_query: str, thread_id: str = "default"):
    """
    Run the research agent with a user query
    
    Args:
        initial_query: The user's initial research request
        thread_id: Unique thread ID for this conversation
        
    Returns:
        Generator that yields questions and final research
    """
    app = build_research_agent_graph()
    
    # Initial state
    initial_state = {
        "initial_query": initial_query,
        "clarification_questions": [],
        "user_answers": [],
        "questions_asked": 0,
        "ready_for_research": False,
        "final_research": "",
        "messages": []
    }
    
    config = {"configurable": {"thread_id": thread_id}}
    
    # Run the graph
    for event in app.stream(initial_state, config, stream_mode="values"):
        yield event


def resume_with_answer(answer: str, thread_id: str = "default"):
    """
    Resume the graph after user provides an answer
    
    Args:
        answer: User's answer to the clarifying question
        thread_id: Thread ID to resume
        
    Returns:
        Generator that yields next question or final research
    """
    app = build_research_agent_graph()
    config = {"configurable": {"thread_id": thread_id}}
    
    # Resume with the answer using Command
    for event in app.stream(Command(resume=answer), config, stream_mode="values"):
        yield event


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("🔬 Research Agent with Human-in-the-Loop\n")
    print("=" * 60)
    
    # Get user's initial query
    user_query = input("\n👤 Enter your research topic: ").strip()
    if not user_query:
        user_query = "Give me research about animals"
    
    thread_id = "interactive_session"
    
    print(f"\n🔍 Starting research on: {user_query}\n")
    print("=" * 60)
    
    # Start the agent
    try:
        # Initial run to get first question
        state_snapshot = None
        for state in run_research_agent(user_query, thread_id):
            state_snapshot = state
            if state.get("clarification_questions"):
                current_q = state["clarification_questions"][-1]
                print(f"\n🤖 Question {state['questions_asked']}: {current_q}")
                break
        
        # Interactive loop for answering questions
        while state_snapshot and not state_snapshot.get("final_research"):
            # Get user's answer
            answer = input("\n👤 Your answer: ").strip()
            
            if not answer:
                print("⚠️  Please provide an answer.")
                continue
            
            # Resume with the answer
            for state in resume_with_answer(answer, thread_id):
                state_snapshot = state
                
                # Check if there's a new question
                if state.get("clarification_questions") and \
                   len(state.get("user_answers", [])) < len(state["clarification_questions"]):
                    current_q = state["clarification_questions"][-1]
                    print(f"\n🤖 Question {state['questions_asked']}: {current_q}")
                
                # Check if research is complete
                if state.get("final_research"):
                    break
        
        # Print summary
        if state_snapshot:
            print("\n" + "=" * 60)
            print("✅ CONTEXT GATHERING COMPLETE!")
            print("=" * 60)
            print(f"\n📋 Summary:")
            print(f"   • Initial Query: {state_snapshot.get('initial_query', '')}")
            print(f"   • Questions Asked: {state_snapshot.get('questions_asked', 0)}")
            print(f"\n💬 Clarifications Gathered:")
            
            questions = state_snapshot.get('clarification_questions', [])
            answers = state_snapshot.get('user_answers', [])
            
            for i, (q, a) in enumerate(zip(questions, answers), 1):
                print(f"\n   Q{i}: {q}")
                print(f"   A{i}: {a}")
            
            if state_snapshot.get('final_research'):
                print("\n" + "=" * 60)
                print("📚 RESEARCH OUTPUT:\n")
                print(state_snapshot['final_research'])
            
            print("\n" + "=" * 60)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Session interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nNote: Make sure GROQ_API_KEY is set in your .env file")