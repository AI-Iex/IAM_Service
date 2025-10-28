from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):

    """Application configuration settings."""

    # SERVICE config
    SERVICE_NAME: str
    SERVICE_VERSION: str
    SERVICE_DESCRIPTION: str
    SERVICE_LICENSE: str

    # DDBB config
    DATABASE_URL: str

    # Business rules config
    BUSINESS_RULES_PATH: str

    # Logging config
    LOGGING_CONFIG_PATH: str
    LOG_PRIVACY_LEVEL: str = "standard"

    # JWT config
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_SECRET: str
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    REFRESH_TOKEN_BYTES: int = 64

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
