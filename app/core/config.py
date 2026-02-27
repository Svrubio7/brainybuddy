from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "BrainyBuddy"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://brainybuddy:brainybuddy@localhost:5432/brainybuddy"
    DATABASE_URL_SYNC: str = (
        "postgresql+psycopg2://brainybuddy:brainybuddy@localhost:5432/brainybuddy"
    )

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "change-me-to-a-random-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8123/auth/google/callback"

    # Anthropic
    ANTHROPIC_API_KEY: str = ""

    # S3
    S3_BUCKET: str = "brainybuddy"
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""

    # Sentry
    SENTRY_DSN: str = ""

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"


settings = Settings()
