import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """
    Enterprise-grade configuration settings for the Clint suite.
    Uses Pydantic for validation and environment variable loading.
    """
    
    # --- AI & LLM CONFIGURATION ---
    OPENROUTER_API_KEY: str = ""
    AI_MODEL: str = "google/gemini-2.0-flash-001"

    # --- DATABASE CONFIGURATION ---
    DB_PATH: str = "data/clint.db"

    # --- OUTREACH LIMITS & SAFETY ---
    DAILY_EMAIL_LIMIT: int = 200
    DAILY_WHATSAPP_LIMIT: int = 200
    MIN_SCORE_THRESHOLD: int = 5
    
    # Safety delays (seconds) between messages
    MIN_DELAY_SECONDS: int = 5
    MAX_DELAY_SECONDS: int = 15

    # --- SLAs & INCIDENT RECOVERY ---
    SLA_BREACH_HOURS: int = 24
    ALERT_EMAIL: str = "hello@pixartual.studio"
    FALLBACK_TEMPLATE_ENABLED: bool = True

    # --- SENDER PERSONALIZATION (PIXARTUAL STUDIO) ---
    SENDER_NAME: str = "Sagar Kewat"
    SENDER_TITLE: str = "Founder | Pixartual"
    SENDER_CONTACT: str = ""
    SENDER_SITE: str = "https://www.pixartual.studio/"
    SENDER_SUPPORT: str = "hello@pixartual.studio"
    SENDER_TAGLINE: str = "Where Brands Evolve Into Power."
    FROM_EMAIL: str = "hello@pixartual.studio"

    # --- SMTP CONFIGURATION (ROTATION SUPPORT) ---
    SMTP_USER_1: str = ""
    SMTP_PASS_1: str = ""
    SMTP_HOST_1: str = "smtp.gmail.com"
    SMTP_PORT_1: int = 587
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

if __name__ == "__main__":
    # Test loading
    print(f"Loaded Settings for: {settings.SENDER_NAME}")
