from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):

    """Application configuration settings. Loads from environment variables or .env file."""

    # SERVICE config
    SERVICE_NAME: str
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_DESCRIPTION: str
    SERVICE_LICENSE: str
    SERVICE_PERMISSIONS_PATH: str
    CORS_ORIGINS: list[str] = ["http://127.0.0.1:8000", "http://localhost:8000"]

    # Superuser creation on startup
    CREATE_SUPERUSER_ON_STARTUP: bool = False
    SUPERUSER_EMAIL: str 
    SUPERUSER_PASSWORD: str
    SUPERUSER_NAME: str

    # API config
    API_VERSION: float = 1.0

    @property
    def route_prefix(self) -> str:
        """Returns API route prefix using the configured API version."""
        return f"/api/v{self.API_VERSION}"

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

    # Environment config
    ENVIRONMENT: str = "development"

    @property
    def is_development(self):
        return self.ENVIRONMENT == "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
