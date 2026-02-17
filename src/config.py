
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
TAVILY_API_KEY = os.environ.get('TAVILY_API_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

