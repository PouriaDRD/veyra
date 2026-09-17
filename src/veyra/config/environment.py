"""Application environment definitions."""

from enum import StrEnum


class AppEnvironment(StrEnum):
    """Supported Veyra runtime environments."""

    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"
