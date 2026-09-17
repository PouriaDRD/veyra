"""Veyra application settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .environment import AppEnvironment

LogLevel = Literal[
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
]


class Settings(BaseSettings):
    """
    Strongly typed application configuration.

    Values may be provided through environment variables or a local
    `.env` file.

    Environment variables use the `VEYRA_` prefix.
    """

    model_config = SettingsConfigDict(
        env_prefix="VEYRA_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: AppEnvironment = Field(
        default=AppEnvironment.DEVELOPMENT,
        validation_alias=AliasChoices(
            "environment",
            "VEYRA_ENV",
        ),
    )

    debug: bool = True

    log_level: LogLevel = "INFO"

    database_path: Path = Path("./data/veyra.db")

    media_root: Path = Path("./data/media")

    log_dir: Path = Path("./logs")

    log_max_bytes: int = 10 * 1024 * 1024

    log_backup_count: int = 5

    @field_validator(
        "log_level",
        mode="before",
    )
    @classmethod
    def normalize_log_level(
        cls,
        value: object,
    ) -> object:
        """Normalize textual log levels before validation."""

        if isinstance(value, str):
            return value.strip().upper()

        return value

    @property
    def is_development(self) -> bool:
        """Return whether Veyra is running in development."""

        return self.environment is AppEnvironment.DEVELOPMENT

    @property
    def is_test(self) -> bool:
        """Return whether Veyra is running in the test environment."""

        return self.environment is AppEnvironment.TEST

    @property
    def is_production(self) -> bool:
        """Return whether Veyra is running in production."""

        return self.environment is AppEnvironment.PRODUCTION


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the process-level application settings.

    Caching prevents repeated environment and `.env` parsing during the
    lifetime of one process.
    """

    return Settings()


def clear_settings_cache() -> None:
    """
    Clear the cached application settings.

    Primarily useful for isolated tests and controlled runtime reloading.
    """

    get_settings.cache_clear()
