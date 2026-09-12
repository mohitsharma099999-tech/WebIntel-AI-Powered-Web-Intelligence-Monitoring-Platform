from functools import lru_cache
from typing import Optional
from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    APP_NAME: str = "WebIntel"
    APP_VERSION: str = "1.1.0"
    DEBUG: bool = False
    API_KEY: Optional[str] = None  # set to enable auth

    # Database
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql://webintel:webintel@postgres:5432/webintel"
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis / Celery
    REDIS_URL: RedisDsn = Field(default="redis://redis:6379/0")
    CELERY_TASK_TIME_LIMIT: int = 300
    CELERY_TASK_SOFT_TIME_LIMIT: int = 240

    # Scraping
    USER_AGENT: str = "WebIntelBot/1.0 (+https://github.com/mohitsharma099999-tech)"
    HTTP_TIMEOUT: int = 20
    BROWSER_TIMEOUT_MS: int = 30_000
    MAX_CONTENT_BYTES: int = 5_000_000
    RESPECT_ROBOTS_TXT: bool = True

    # AI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    AI_MAX_INPUT_CHARS: int = 12_000

    @field_validator("OPENAI_API_KEY")
    @classmethod
    def _strip_key(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else None

    @property
    def ai_enabled(self) -> bool:
        return bool(self.OPENAI_API_KEY)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
