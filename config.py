import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(PROJECT_ROOT, "omnibook.db"))
TICKETS_PATH = os.path.join(PROJECT_ROOT, "data", "tickets.json")
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
