"""Application configuration and environment settings."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Core settings loaded from environment or defaults."""

    PROJECT_NAME: str = "Investment Data Engineering & Portfolio Intelligence Platform"
    ENVIRONMENT: str = Field(default="development")
    LOG_LEVEL: str = Field(default="INFO")

    # PostgreSQL Connection parameters
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="portfolio_db")
    POSTGRES_USER: str = Field(default="portfolio_app")
    POSTGRES_PASSWORD: str = Field(default="portfolio_dev_secret")

    # SQLAlchemy Database URL
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://portfolio_app:portfolio_dev_secret@localhost:5432/portfolio_db"
    )

    # API configuration
    API_V1_STR: str = Field(default="/api/v1")
    RUN_ID_PREFIX: str = Field(default="RUN")

    # In-memory / Test SQLite fallback URL for fast local test execution
    TEST_DATABASE_URL: str = Field(default="sqlite:///:memory:")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
