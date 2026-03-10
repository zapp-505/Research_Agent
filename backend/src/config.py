
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
TAVILY_API_KEY = os.environ.get('TAVILY_API_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
<<<<<<< HEAD

# Path to Firebase service-account JSON (e.g. serviceAccountKey.json).
# Leave unset to use Application Default Credentials.
FIREBASE_SERVICE_ACCOUNT = os.environ.get('FIREBASE_SERVICE_ACCOUNT')

=======
MONGODB_URI = os.environ.get('MONGODB_URI')
>>>>>>> 5995caf81143f0c4bd6681bb2ec31944e086c90c
