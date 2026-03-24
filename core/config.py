import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Keys
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    AI_MODEL: str = os.getenv("AI_MODEL", "openai/gpt-4o-mini")

    # DB
    DB_PATH: str = os.getenv("DB_PATH", "data/cold_mailer.db")

    # Limits
    DAILY_EMAIL_LIMIT: int = int(os.getenv("DAILY_EMAIL_LIMIT", 200))
    DAILY_WHATSAPP_LIMIT: int = int(os.getenv("DAILY_WHATSAPP_LIMIT", 100))
    
    # Delays
    MIN_DELAY: int = int(os.getenv("MIN_DELAY_SECONDS", 30))
    MAX_DELAY: int = int(os.getenv("MAX_DELAY_SECONDS", 120))

    class Config:
        case_sensitive = True

settings = Settings()
