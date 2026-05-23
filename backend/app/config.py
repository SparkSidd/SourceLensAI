from backend.app.core.config import (
    WORKSPACE_DIR,
    DATABASE_URL,
    SANDBOX_MODE,
    GEMINI_API_KEY,
    TAVILY_API_KEY,
    LLM_MODEL,
    MAX_OUTPUT_TOKENS,
    TEMPERATURE
)

# For compatibility
DB_PATH = DATABASE_URL.replace("sqlite+aiosqlite:///", "")
