"""Configuration and environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration from environment variables."""

    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
    OPENAI_TEMPERATURE = 0.2

    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    # Server
    BACKEND_PORT = int(os.getenv("BACKEND_PORT", 8000))
    BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # RAG
    RAG_SIMILARITY_THRESHOLD = 0.45
    RAG_TOP_K = 5
    RAG_CHUNK_SIZE = 500
    RAG_CHUNK_OVERLAP = 100

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        required = ["OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_ANON_KEY"]
        missing = [key for key in required if not getattr(cls, key)]

        if missing:
            raise ValueError(f"Missing required env vars: {', '.join(missing)}")

        return True
