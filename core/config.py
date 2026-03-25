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
    MIN_DELAY: int = int(os.getenv("MIN_DELAY_SECONDS", 5))
    MAX_DELAY: int = int(os.getenv("MAX_DELAY_SECONDS", 15))

    # Sender Personalization
    SENDER_NAME: str = os.getenv("SENDER_NAME", "Senior Business Development Manager")
    SENDER_TITLE: str = os.getenv("SENDER_TITLE", "Founder")
    SENDER_CONTACT: str = os.getenv("SENDER_CONTACT", "")
    SENDER_SITE: str = os.getenv("SENDER_SITE", "https://www.pixartual.studio/")
    SENDER_SUPPORT: str = os.getenv("SENDER_SUPPORT", "hello@pixartual.studio")
    SENDER_TAGLINE: str = os.getenv("SENDER_TAGLINE", "Where Brands Evolve Into Power.")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "hello@pixartual.studio")

    class Config:
        case_sensitive = True

settings = Settings()

# Runtime validation
if not settings.OPENROUTER_API_KEY:
    from core.logger import logger
    logger.error("[bold red]CRITICAL: OPENROUTER_API_KEY is missing![/bold red] AI features will not work.")
