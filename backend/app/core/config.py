import os
from dotenv import load_dotenv

# Resolve active paths
CORE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(CORE_DIR)
BACKEND_DIR = os.path.dirname(APP_DIR)
WORKSPACE_DIR = os.path.dirname(BACKEND_DIR)

# Load environment configuration
env_path = os.path.join(BACKEND_DIR, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# Sandbox Toggle
SANDBOX_MODE = not (GEMINI_API_KEY and TAVILY_API_KEY)

# Database Resolver
DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    # Fallback to local SQLite DB inside workspace
    DB_PATH = os.path.join(WORKSPACE_DIR, "sourcelens.db")
    DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"
else:
    # Support postgres+asyncpg or sqlite direct strings
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Core LLM Configurations
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "4096"))

print(f"[CONFIG] Workspace Root: {WORKSPACE_DIR}")
print(f"[CONFIG] Active DB URI: {DATABASE_URL}")
print(f"[CONFIG] Sandbox Active: {SANDBOX_MODE} (Gemini: {'Loaded' if GEMINI_API_KEY else 'Missing'}, Tavily: {'Loaded' if TAVILY_API_KEY else 'Missing'})")
