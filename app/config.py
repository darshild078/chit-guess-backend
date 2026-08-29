import os
import re
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PORT: int = Field(default=5000)
    DATABASE_URL: str = Field(
        default="postgresql://chitguess:chitguess_dev_password@localhost:5432/chitguess"
    )
    JWT_SECRET: str = Field(default="dev-super-secret-jwt-key-change-in-production")
    FRONTEND_URL: str = Field(default="http://localhost:5173")
    NODE_ENV: str = Field(default="development")
    ROOM_EXPIRY_HOURS: int = Field(default=24)
    LOG_LEVEL: str = Field(default="info")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def is_dev(self) -> bool:
        return self.NODE_ENV == "development"

    @property
    def async_database_url(self) -> str:
        """
        Converts a postgresql:// or postgres:// URL to postgresql+asyncpg://
        and strips parameters that asyncpg handles via connect_args.
        """
        url = self.DATABASE_URL.strip()
        # Clean pgbouncer parameter if present in query string
        url = re.sub(r'([?&])pgbouncer=true(&?)', r'\1', url)
        url = url.rstrip('?&')

        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        return url

settings = Settings()
