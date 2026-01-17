from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Telegram Bot
    telegram_bot_token: str
    
    # AI Configuration
    ai_provider: Literal["openai", "anthropic", "groq"] = "openai"  # Добавлен groq
    ai_model: str = "gpt-4-turbo-preview"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    groq_api_key: str | None = None  # НОВОЕ!
    
    # Database
    database_url: str = "sqlite:///./oracle.db"
    
    # Bot Settings
    debug_mode: bool = False
    log_level: str = "INFO"
    
    # Monetization
    payment_provider_token: str | None = None
    free_questions_per_day: int = 2
    premium_price_rub: int = 499
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
