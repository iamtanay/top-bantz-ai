import os
from dotenv import load_dotenv

load_dotenv()

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")