import os
from langchain_groq import ChatGroq
from src.config import GEMINI_API_KEY
from src.constants import GEMINI_LLM_MODEL_NAME

def get_llm(temperature=0.0):
    """
    Factory function to return a configured Groq LLM.
    """
    if not GEMINI_API_KEY:
        raise ValueError("CRITICAL ERROR: GROQ_API_KEY is missing from .env file.")
    
    llm = ChatGroq(api_key=GEMINI_API_KEY, temperature=temperature,model=GEMINI_LLM_MODEL_NAME)
    return llm 