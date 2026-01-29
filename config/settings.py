"""Application configuration and environment settings."""
import os
from typing import Optional

from dotenv import load_dotenv


load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # MongoDB
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "omnisearch")

    # Weaviate
    WEAVIATE_URL: str = os.getenv("WEAVIATE_URL", "http://localhost:8080")

    # Application
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    DEV_MODE: bool = os.getenv("DEV_MODE", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    APP_NAME: str = "omnisearch"
    APP_VERSION: str = "0.1.0"


settings = Settings()
