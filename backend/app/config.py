import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "ORBIT — Autonomous Business Operations Intelligence"
    API_V1_STR: str = "/api"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./orbit.db")
    
    # AI / LLM Configuration
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", None))
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini" if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") else "deterministic")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gemini-2.0-flash")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
