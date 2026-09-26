from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


API_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Memorial Trust Management"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True

    api_v1_prefix: str = "/api/v1"

    cors_origins: str = (
        "http://localhost:3000,"
        "http://127.0.0.1:3000"
    )

    database_url: str = ""
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    model_config = SettingsConfigDict(
        env_file=API_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def validate_production_security(self) -> None:
        if self.environment.lower() != "production":
            return

        if self.debug:
            raise ValueError("DEBUG must be false in production.")

        if not self.database_url:
            raise ValueError(
                "DATABASE_URL must be configured in production."
            )

        if len(self.jwt_secret_key) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must contain at least 32 characters in production."
            )

        if not self.cors_origins.strip():
            raise ValueError(
                "CORS_ORIGINS must be configured in production."
            )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_production_security()
    return settings


settings = get_settings()
