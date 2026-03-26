import os
from langchain_groq import ChatGroq
from src.config import GROQ_API_KEY
from src.constants import GROQ_LLM_MODEL_NAME, GROQ_FAST_MODEL_NAME

def get_llm(temperature=0.0, use_fast_model=False):
    """
    Factory function to return a configured Groq LLM.
    """
    if not GROQ_API_KEY:
        raise ValueError("CRITICAL ERROR: GROQ_API_KEY is missing from .env file.")
    
    model_name = GROQ_FAST_MODEL_NAME if use_fast_model else GROQ_LLM_MODEL_NAME
    llm = ChatGroq(api_key=GROQ_API_KEY, temperature=temperature, model=model_name)
    return llm 