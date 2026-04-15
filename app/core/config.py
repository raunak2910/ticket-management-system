"""
Application Configuration
Reads from environment variables with sensible defaults
"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Ticket Management System"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./tickets.db"
    DB_ECHO: bool = False  # Set True to log SQL queries

    # JWT
    SECRET_KEY: str = "your-super-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]

    # OpenAI (optional for enhanced AI responses)
    OPENAI_API_KEY: str = ""

    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
