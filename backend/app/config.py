"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from typing import List
from pydantic import field_validator
import json
from app.utils import get_logger


def _mask_db_url(url: str) -> str:
    """Mask credentials in a DB URL for safe logging.

    Very small helper: if URL contains '@' (user:pass@host), mask everything before '@'.
    """
    try:
        if "@" in url and "://" in url:
            prefix, rest = url.split("://", 1)
            userinfo, host = rest.split("@", 1)
            return f"{prefix}://***@{host}"
    except Exception:
        pass
    return url


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    # Project Info
    PROJECT_NAME: str = "Money Tracker API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./moneytracker.db"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:80",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080"
    ]
    
    @field_validator('BACKEND_CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                # Try to parse as JSON array
                return json.loads(v)
            except json.JSONDecodeError:
                # If not JSON, split by comma
                return [origin.strip() for origin in v.split(',')]
        return v
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    # Pagination defaults
    DEFAULT_LIMIT: int = 50
    MAX_LIMIT: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Log a short, non-sensitive summary of loaded settings
logger = get_logger("app.config")
logger.info(
    "Settings loaded: host=%s port=%s db=%s cors=%s",
    settings.HOST,
    settings.PORT,
    _mask_db_url(settings.DATABASE_URL),
    settings.BACKEND_CORS_ORIGINS,
)
