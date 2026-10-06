import os
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

load_dotenv()

# Initialize Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# We use the free tier model
model = genai.GenerativeModel('gemini-2.5-flash')

# Retry logic for rate limiting (15 RPM limit on free tier)
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def generate_response(prompt: str) -> str:
    """
    Generate a response from the Gemini model, with exponential backoff 
    to handle potential 429 Too Many Requests errors.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        raise
