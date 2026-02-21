# --- LLM CONFIGURATION ---
GROQ_LLM_MODEL_NAME = "llama-3.3-70b-versatile"
GEMINI_LLM_MODEL_NAME = "gemini-2.5-flash"
TEMPERATURE_CREATIVE = 0.7  # For generating ideas
TEMPERATURE_STRICT = 0.0    # For validation/code

# --- SEARCH CONFIGURATION ---
MAX_SEARCH_RESULTS = 3
SEARCH_DEPTH = "advanced"   # Options: "basic", "advanced"

# --- AGENT SETTINGS ---
# We can define the standard roles here so we don't typo them later
ROLE_ARCHITECT = "Architect"
ROLE_RED_TEAM = "Red Team"
ROLE_BLUE_TEAM = "Blue Team"