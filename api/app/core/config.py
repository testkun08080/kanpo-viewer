"""
Configuration settings for Kanpo PDF API
Reads all settings from environment variables
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables"""

    # Basic application settings
    project_name: str = os.getenv("PROJECT_NAME", "Kanpo PDF API")
    project_description: str = os.getenv("PROJECT_DESCRIPTION", "PDF download API for Kanpo documents")
    version: str = os.getenv("VERSION", "0.1.0")
    root_path: str = os.getenv("ROOT_PATH", "/api")

    # Security settings
    api_key: str = os.getenv("KANPO_API_KEY", "your-secure-api-key-here")

    # Environment configuration
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "DEBUG")

    # Service limits
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB default
    timeout: int = int(os.getenv("TIMEOUT", "30"))  # 30 seconds default

    # CORS configuration
    @property
    def allowed_origins(self) -> List[str]:
        """Parse CORS allowed origins from environment variable"""
        origins_env = os.getenv("ALLOWED_ORIGINS", "")

        if origins_env:
            # Split by comma and strip whitespace
            origins = [origin.strip() for origin in origins_env.split(",") if origin.strip()]
            return origins

        # Default development origins
        if self.environment == "development":
            return [
                "http://localhost:3000",
                "http://localhost:8080",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8080"
            ]

        # Production should have explicit origins
        return []

    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        case_sensitive = False
