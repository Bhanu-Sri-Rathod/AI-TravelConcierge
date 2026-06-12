from dotenv import load_dotenv
import os

load_dotenv()
print("ENV FILE LOADED")
print("OPENWEATHER:", os.getenv("OPENWEATHER_API_KEY"))

GEMINI_API_KEY       = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY         = os.getenv("GROQ_API_KEY")
OPENWEATHER_API_KEY  = os.getenv("OPENWEATHER_API_KEY")
EXCHANGE_API_KEY     = os.getenv("EXCHANGE_API_KEY")
AVIATIONSTACK_API_KEY= os.getenv("AVIATIONSTACK_API_KEY")
DATABASE_URL         = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./travel.db")
JWT_SECRET           = os.getenv("JWT_SECRET", "changeme")
JWT_ALGORITHM        = os.getenv("JWT_ALGORITHM", "HS256")
FRONTEND_URL         = os.getenv("FRONTEND_URL", "http://localhost:3000")
LANGCHAIN_API_KEY    = os.getenv("LANGCHAIN_API_KEY")

# Set LangSmith env vars
os.environ["LANGCHAIN_API_KEY"]      = LANGCHAIN_API_KEY or ""
os.environ["LANGCHAIN_TRACING_V2"]   = os.getenv("LANGCHAIN_TRACING_V2", "true")
os.environ["LANGCHAIN_PROJECT"]      = os.getenv("LANGCHAIN_PROJECT", "travel-concierge")
