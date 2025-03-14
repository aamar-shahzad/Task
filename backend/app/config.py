import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Constants
MAX_HISTORY_ENTRIES = 10
CONVERSATION_TIMEOUT_HOURS = 24
UNSAFE_CODE_PATTERNS = ['import', 'exec', 'eval', 'os.', 'system', '__', 'open', 'file', 'write']

# Configure Google Gemini API
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("GEMINI_API_KEY not found in environment variables!")