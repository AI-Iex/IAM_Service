from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration settings. Loads from environment variables or .env file"""

    # ------------Service Config------------

    SERVICE_NAME: str
    """Name of the Service"""

    SERVICE_VERSION: str
    """Version of the Service, used in the OpenAPI docs (Swagger, ReDoc) and **ROUTES**"""

    @property
    def route_prefix(self) -> str:
        """Returns **API Route** prefix using the configured service version"""

        try:

            v = float(self.SERVICE_VERSION)
            if v.is_integer():
                v = int(v)

        except Exception:
            v = self.SERVICE_VERSION

        return f"/api/v{v}"

    SERVICE_DESCRIPTION: str
    """Description of the Service, used in the OpenAPI docs (Swagger, ReDoc) """

    SERVICE_LICENSE: str
    """License of the Service, used in the OpenAPI docs (Swagger, ReDoc) """

    SERVICE_PERMISSIONS_PATH: str
    """Path to permissions_map.json file, to load permissions definitions and for seeding it into the database"""

    CORS_ORIGINS: list[str]
    """List of allowed CORS origins"""

    DEBUG: bool = False
    """Enable or disable debug mode logging"""

    # ------------DDBB Config------------

    DATABASE_URL: str
    """Database connection URL"""

    TEST_DATABASE_URL: str
    """Test database connection URL, used only for testing"""

    # ------------Superuser Config------------

    CREATE_SUPERUSER_ON_STARTUP: bool = False
    """Flag to create a superuser on startup"""

    SUPERUSER_EMAIL: str
    """Email of the superuser"""

    SUPERUSER_PASSWORD: str
    """Password of the superuser, will be used only for the initial login and must be changed afterwards"""

    SUPERUSER_NAME: str
    """Name of the superuser"""

    # ------------Business Rules Config------------

    BUSINESS_RULES_PATH: str
    """Path to business_rules.json file, to load business rules definitions used in user services"""

    # ------------Logging Config------------

    # Logging config
    LOGGING_CONFIG_PATH: str
    """Path to logging configuration file (YAML format)"""

    LOG_PRIVACY_LEVEL: str = "standard"
    """Logging privacy level: none, standard, strict"""

    # ------------Token and Security Config------------

    JWT_SECRET_KEY: str
    """Secret key used to sign JWT tokens"""

    JWT_ALGORITHM: str
    """Algorithm used for JWT token signing"""

    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    """Expiration time for JWT access tokens in minutes"""

    REFRESH_TOKEN_SECRET: str
    """Secret key used to sign refresh tokens"""

    REFRESH_TOKEN_EXPIRE_DAYS: int
    """Expiration time for refresh tokens in days"""

    # ------------Environment Config------------

    ENVIRONMENT: str = "production"
    """Application environment (e.g., development, production)"""

    @property
    def is_development(self):
        """Returns True if the environment is set to development, used for limitate the routes to send the refresh cookie"""
        return self.ENVIRONMENT == "development"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
