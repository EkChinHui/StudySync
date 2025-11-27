"""Configuration management for StudySync backend."""

from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "StudySync"
    debug: bool = True

    # Database
    database_url: str = "sqlite:///./studysync.db"

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"

    # LLM API Keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # YouTube Data API
    youtube_api_key: str = ""

    class Config:
        # Look for .env in backend directory
        env_file = os.path.join(Path(__file__).parent, ".env")
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
